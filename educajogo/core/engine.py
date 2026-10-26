"""Motor do jogo. NÃO importa pygame: pode ser testado e simulado sem janela.

Ordem de execução de UMA decisão (documentada no GDD):
  1. registra a carta/escolha no histórico (uma única vez; `choose` é idempotente por carta)
  2. aplica efeitos nos medidores (valores brutos, sem clamp ainda)
  3. aplica flags, contadores, relações, cancelamentos e agendamentos
  4. avança o tempo (meses)
  5. aplica o FLUXO MENSAL (receitas/despesas recorrentes) proporcional aos meses
  6. limita (clamp 0..100) e verifica limites fatais
  7. se não morreu: verifica fim do mandato (vitória) e objetivos
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .conditions import check
from .content import Content
from .save import Save


@dataclass
class Result:
    card_id: str
    side: str
    label: str
    outcome: str
    deltas: dict            # efeito direto da decisão (por medidor)
    flow: dict              # efeito do fluxo mensal aplicado em seguida
    learn: str | None       # termo do glossário associado
    new_terms: list         # termos que nunca tinham sido vistos
    objectives: list        # objetivos concluídos nesta decisão
    ended: str | None       # id do final, se acabou
    month: int


class Run:
    """Estado TEMPORÁRIO de um mandato."""

    def __init__(self, content: Content, perm: Save | None = None, rng: random.Random | None = None):
        self.content = content
        self.perm = perm if perm is not None else Save.memory()
        self.rng = rng or random.Random()
        cfg = content.config
        self.cfg = cfg
        self.mandate_no = self.perm.mandates + 1
        self.inherit = self.perm.last_ending          # como o mandato anterior terminou
        self.ending_kind: str | None = None

        # identidade do(a) prefeito(a) (sucessão: alterna a cada mandato)
        mayors = cfg["mayors"]
        m = mayors[(self.mandate_no - 1) % len(mayors)]
        self.mayor_name = m["name"]
        self.mayor_t = m["t"]

        # estado
        self.month = 0
        self.turn = 0
        self.meters = {k: float(v["start"]) for k, v in cfg["meters"].items()}
        self.flags: set[str] = set()
        self.counters: dict[str, int] = {}
        self.rel: dict[str, int] = {}
        self.seen: dict[str, int] = {}       # carta -> turno em que apareceu
        self.choices: dict[str, str] = {}    # carta -> lado escolhido
        self.queue: list[dict] = []          # consequências adiadas
        self.history: list[dict] = []
        self.learned: list[str] = []
        self.obj_done: list[str] = []
        self.current: dict | None = None
        self.why: list[str] = []             # depuração: por que esta carta?
        self.ending: str | None = None
        self.last_char: str | None = None

        self._apply_start_mods()
        # a carta de abertura (tutorial) abre só o PRIMEIRO mandato; depois o jogador já conhece as regras
        if self.perm.mandates == 0:
            self.queue.append({"card": cfg["intro_card"], "due": 0})

    # ------------------------------------------------------------------ util
    def fmt(self, text: str) -> str:
        first = self.mayor_name.split()[0]
        return (text.replace("{T}", self.mayor_t.capitalize()).replace("{t}", self.mayor_t)
                .replace("{nome}", first).replace("{cidade}", self.cfg["city"]))

    def _apply_start_mods(self):
        for mod in self.cfg.get("start_mods", []):
            if check(mod.get("when"), self):
                for k, v in mod["effects"].items():
                    self.meters[k] += v
                self.flags.update(mod.get("flags_set", []))
        # pequena variação para que cada mandato comece diferente
        noise = self.cfg.get("start_noise", 0)
        if noise:
            for k in self.meters:
                self.meters[k] += self.rng.randint(-noise, noise)
        for k in self.meters:
            self.meters[k] = max(5.0, min(95.0, self.meters[k]))

    # --------------------------------------------------------------- seleção
    def _eligible(self, card: dict) -> bool:
        cid = card["id"]
        if card.get("weight", 10) <= 0:
            return False
        if cid in self.seen and not card.get("repeat", False):
            return False
        if cid in self.seen and card.get("repeat") and self.turn - self.seen[cid] < card.get("cooldown", 10):
            return False
        if self.month < card.get("min_month", 0) or self.month > card.get("max_month", 10_000):
            return False
        return check(card.get("req"), self)

    def _weight(self, card: dict) -> float:
        w = float(card.get("weight", 10))
        for b in card.get("boost", []):
            if check(b.get("when"), self):
                w *= b.get("mult", 2)
        if card["char"] == self.last_char:
            w *= 0.35                                # variedade de personagens
        return w

    def next_card(self) -> dict:
        """Escolhe (e fixa) a próxima carta. Idempotente enquanto não houver `choose`."""
        if self.current is not None:
            return self.current
        self.why = []
        card = self._pop_due()
        if card is None:
            pool = [self.content.cards[c] for c in self.content.card_order if self._eligible(self.content.cards[c])]
            if pool:
                weights = [self._weight(c) for c in pool]
                card = self.rng.choices(pool, weights=weights, k=1)[0]
                ranked = sorted(zip(pool, weights), key=lambda x: -x[1])[:5]
                self.why.append("sorteio ponderado entre %d elegíveis" % len(pool))
                self.why += [f"  {c['id']}: peso {w:.1f}" for c, w in ranked]
            else:
                card = self._fallback()
        self.current = card
        self.seen[card["id"]] = self.turn
        self.perm.seen_cards.add(card["id"])
        self.last_char = card["char"]
        return card

    def _pop_due(self) -> dict | None:
        due = [e for e in self.queue if e["due"] <= self.month]
        due.sort(key=lambda e: e["due"])
        for e in due:
            self.queue.remove(e)
            if e["card"] in self.seen and not self.content.cards[e["card"]].get("repeat"):
                self.why.append(f"agendada {e['card']} descartada (já apareceu neste mandato)")
                continue
            if not check(e.get("if"), self):
                self.why.append(f"agendada {e['card']} descartada (condição 'if' falsa)")
                continue
            self.why.append(f"FORÇADA: consequência agendada ({e['card']}), vencida no mês {e['due']}")
            return self.content.cards[e["card"]]
        return None

    def _fallback(self) -> dict:
        self.why.append("FALLBACK: nenhuma carta elegível")
        pool = [c for c in self.content.cards.values() if c.get("fallback")]
        pool.sort(key=lambda c: self.seen.get(c["id"], -1))
        return pool[0]

    # ------------------------------------------------------------- decisões
    def hints(self, card: dict, side: str) -> dict:
        """Pontos de 'quais medidores mudam' (sem direção), como no gênero. 0=nada, 1..3 = tamanho."""
        if card.get("hide_hints"):
            return {}
        out = {}
        for k, v in card[side].get("effects", {}).items():
            a = abs(v)
            if a:
                out[k] = 1 if a <= 6 else (2 if a <= 14 else 3)
        return out

    def choose(self, side: str) -> Result:
        assert side in ("left", "right")
        card = self.current
        if card is None or self.ending is not None:
            raise RuntimeError("não há carta ativa")
        self.current = None                          # garante que escolhas repetidas não contam 2x
        opt = card[side]
        self.choices[card["id"]] = side

        # 2) efeitos diretos
        before = dict(self.meters)
        for k, v in opt.get("effects", {}).items():
            self.meters[k] += v
        # 3) estado narrativo
        self.flags.update(opt.get("flags_set", []))
        self.flags.difference_update(opt.get("flags_clear", []))
        for k, v in opt.get("counters", {}).items():
            self.counters[k] = self.counters.get(k, 0) + v
        for k, v in opt.get("rel", {}).items():
            self.rel[k] = max(-3, min(3, self.rel.get(k, 0) + v))
        for cid in opt.get("cancel", []):
            self.queue = [e for e in self.queue if e["card"] != cid]
        self.perm.flags.update(opt.get("perm", []))
        # 4) tempo
        months = opt.get("months", card.get("months", self.cfg["months_per_card"]))
        for s in opt.get("schedule", []):               # agenda relativo ao mês ATUAL da decisão
            self.queue.append({"card": s["card"], "due": self.month + s.get("after", 2), "if": s.get("if")})
        self.month += months
        self.turn += 1
        direct = {k: round(self.meters[k] - before[k]) for k in self.meters}

        # 5) fluxo mensal, proporcional aos meses (base = months_per_card)
        flow = {k: 0.0 for k in self.meters}
        if months > 0:
            scale = months / self.cfg["months_per_card"]
            for r in self.cfg.get("recurring", []):
                if check(r.get("when"), self):
                    for k, v in r["effects"].items():
                        flow[k] += v * scale
            for k, v in flow.items():
                self.meters[k] += v
        flow = {k: round(v) for k, v in flow.items()}

        # 6) clamp + fatal
        ending = opt.get("end")
        if ending is None:
            ending = self._check_fatal(direct, flow)
        for k in self.meters:
            self.meters[k] = max(0.0, min(100.0, self.meters[k]))

        # termos aprendidos
        learn = opt.get("learn") or card.get("learn")
        new_terms = []
        if learn:
            if learn not in self.learned:
                self.learned.append(learn)
            if learn not in self.perm.glossary:
                new_terms.append(learn)
                self.perm.glossary.add(learn)

        self.history.append({
            "month": self.month, "card": card["id"], "char": card["char"], "side": side,
            "label": opt["label"], "learn": learn, "deltas": direct,
            "story": card.get("story"),
        })

        # 7) vitória por tempo
        if ending is None and self.month >= self.cfg["mandate_months"]:
            ending = self._pick_victory()
        if ending is not None:
            self._finish(ending)
        objs = self._check_objectives()
        if ending is not None and not objs:
            pass
        return Result(card["id"], side, opt["label"], self.fmt(opt["outcome"]), direct, flow,
                      learn, new_terms, objs, ending, self.month)

    def _check_fatal(self, direct, flow) -> str | None:
        lo, hi = self.cfg.get("fatal_low", 0), self.cfg.get("fatal_high", 100)
        hits = []
        for k, v in self.meters.items():
            if v <= lo:
                hits.append((abs(direct[k]) + abs(flow.get(k, 0)), k, "low"))
            elif v >= hi:
                hits.append((abs(direct[k]) + abs(flow.get(k, 0)), k, "high"))
        if not hits:
            return None
        hits.sort(key=lambda x: -x[0])
        _, k, side = hits[0]
        for e in self.content.endings_list:
            if e.get("kind") == "fatal" and e["meter"] == k and e["side"] == side:
                return e["id"]
        raise KeyError(f"final fatal ausente para {k}/{side}")

    def _pick_victory(self) -> str:
        self.ending_kind = "victory"
        for e in self.content.endings_list:
            if e["kind"] == "victory" and check(e.get("when"), self):
                return e["id"]
        raise KeyError("nenhum final de vitória aplicável")

    def _finish(self, ending_id: str):
        e = self.content.endings[ending_id]
        self.ending = ending_id
        self.ending_kind = e["kind"]
        self.perm.endings.add(ending_id)
        self.perm.flags.update(e.get("perm", []))
        for t in e.get("learn", []):
            self.perm.glossary.add(t)
        self.perm.last_ending = ending_id
        self.perm.mandates += 1
        self.perm.history.append({
            "n": self.mandate_no, "mayor": self.mayor_name, "ending": ending_id,
            "months": min(self.month, self.cfg["mandate_months"]), "decisions": self.turn,
            "kind": e["kind"],
        })
        for k in self.meters:
            self.meters[k] = max(0.0, min(100.0, self.meters[k]))

    def _check_objectives(self) -> list[str]:
        done = []
        for o in self.content.objectives:
            if o["id"] in self.obj_done:
                continue
            if check(o.get("when"), self):
                self.obj_done.append(o["id"])
                self.perm.selos.add(o["id"])
                self.perm.flags.update(o.get("perm", []))
                done.append(o["id"])
        return done

    # ------------------------------------------------------------ consultas
    @property
    def finished(self) -> bool:
        return self.ending is not None

    @property
    def flow_now(self) -> dict:
        """Fluxo mensal ATUAL (por decisão padrão), para mostrar na interface."""
        flow = {k: 0.0 for k in self.meters}
        for r in self.cfg.get("recurring", []):
            if check(r.get("when"), self):
                for k, v in r["effects"].items():
                    flow[k] += v
        return flow

    def flow_reasons(self) -> list[tuple[str, dict]]:
        return [(r["label"], r["effects"]) for r in self.cfg.get("recurring", []) if check(r.get("when"), self)]

    def danger(self, key: str) -> str | None:
        v = self.meters[key]
        if v <= self.cfg.get("danger_low", 20):
            return "low"
        if v >= self.cfg.get("danger_high", 80):
            return "high"
        return None

    def summary(self) -> dict:
        """Dados para a tela final (prestação de contas)."""
        ending = self.content.endings[self.ending] if self.ending else None
        return {
            "ending": ending,
            "months": min(self.month, self.cfg["mandate_months"]),
            "decisions": self.turn,
            "meters": {k: round(v) for k, v in self.meters.items()},
            "history": self.history,
            "learned": list(self.learned),
            "objectives": list(self.obj_done),
        }
