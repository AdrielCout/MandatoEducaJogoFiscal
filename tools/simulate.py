"""Simulador de balanceamento: joga milhares de mandatos com "jogadores robôs".

Uso:
    python tools/simulate.py              # 2000 mandatos por robô
    python tools/simulate.py 5000 --md    # imprime em Markdown (para docs/)

Por que existe: o guia pede que a dificuldade venha da interação entre recursos,
consequências e personagens, e não de sorte. Este script mede isso.

Robôs:
  aleatório     escolhe esquerda/direita no cara-ou-coroa (iniciante que não lê)
  equilibrista  escolhe a opção que deixa os 4 medidores mais perto do meio (jogador atento)
  distraído     equilibrista que erra 30% das vezes (melhor estimativa de um jogador humano)
  míope         só olha o medidor mais baixo (jogador que "apaga incêndio")
"""

from __future__ import annotations

import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from educajogo.core.content import Content  # noqa: E402
from educajogo.core.engine import Run  # noqa: E402
from educajogo.core.save import Save  # noqa: E402


def _after(run: Run, card: dict, side: str) -> dict:
    eff = card[side].get("effects", {})
    return {k: run.meters[k] + eff.get(k, 0) for k in run.meters}


def bot_random(run, card, rng):
    return rng.choice(("left", "right"))


def bot_balanced(run, card, rng):
    def cost(side):
        return sum((v - 50) ** 2 for v in _after(run, card, side).values())
    a, b = cost("left"), cost("right")
    if abs(a - b) < 1:
        return rng.choice(("left", "right"))
    return "left" if a < b else "right"


def bot_myopic(run, card, rng):
    worst = max(run.meters, key=lambda k: abs(run.meters[k] - 50))

    def score(side):
        return -abs(_after(run, card, side)[worst] - 50)
    a, b = score("left"), score("right")
    if a == b:
        return rng.choice(("left", "right"))
    return "left" if a > b else "right"


def bot_distracted(run, card, rng):
    """Como o equilibrista, mas erra 30% das vezes: estimativa de um jogador humano que não vê os números."""
    return rng.choice(("left", "right")) if rng.random() < 0.30 else bot_balanced(run, card, rng)


BOTS = {"aleatório": bot_random, "distraído (30% erro)": bot_distracted, "equilibrista": bot_balanced, "míope": bot_myopic}


def play(content, bot, rng, save=None):
    save = save or Save.memory()
    run = Run(content, save, random.Random(rng.random()))
    fallbacks = 0
    cards = []
    while not run.finished:
        card = run.next_card()
        if run.why and run.why[0].startswith("FALLBACK"):
            fallbacks += 1
        cards.append(card["id"])
        side = bot(run, card, rng)
        run.choose(side)
        if run.turn > 200:
            raise RuntimeError("mandato não termina (loop?)")
    return run, cards, fallbacks


def main():
    n = 2000
    md = "--md" in sys.argv
    for a in sys.argv[1:]:
        if a.isdigit():
            n = int(a)
    content = Content()
    rng = random.Random(20262)
    lines = []
    out = lines.append

    out(f"# Relatório de simulação ({n} mandatos por robô)\n" if md else f"Simulação: {n} mandatos por robô")
    summary = {}
    for name, bot in BOTS.items():
        endings = Counter()
        months = []
        decisions = []
        fb = 0
        appear = Counter()
        side_pick = defaultdict(Counter)
        for _ in range(n):
            run, cards, f = play(content, bot, rng)
            endings[run.ending] += 1
            months.append(min(run.month, content.config["mandate_months"]))
            decisions.append(run.turn)
            fb += f
            appear.update(set(cards))
            for h in run.history:
                side_pick[h["card"]][h["side"]] += 1
        wins = sum(c for e, c in endings.items() if content.endings[e]["kind"] == "victory")
        exemplar = endings.get("mandato_exemplar", 0)
        summary[name] = dict(wins=wins / n, exemplar=exemplar / n, months=sum(months) / n, endings=endings,
                             fb=fb, appear=appear, side=side_pick, dec=sum(decisions) / n)

    # ---------------------------------------------------------------- resumo
    out("## Sobrevivência" if md else "\n== Sobrevivência ==")
    out("| robô | concluiu o mandato | mandato exemplar | meses médios | decisões médias | cartas-reserva usadas |" if md else
        f"{'robô':14}{'concluiu':>10}{'exemplar':>10}{'meses':>8}{'decisões':>10}{'fallback':>10}")
    if md:
        out("|---|---|---|---|---|---|")
    for name, s in summary.items():
        if md:
            out(f"| {name} | {s['wins']:.0%} | {s['exemplar']:.0%} | {s['months']:.1f} | {s['dec']:.1f} | {s['fb']} |")
        else:
            out(f"{name:14}{s['wins']:>10.0%}{s['exemplar']:>10.0%}{s['months']:>8.1f}{s['dec']:>10.1f}{s['fb']:>10}")

    out("\n## Como os mandatos terminam" if md else "\n== Finais ==")
    ids = [e["id"] for e in content.endings_list]
    if md:
        out("| final | " + " | ".join(summary) + " |")
        out("|---|" + "---|" * len(summary))
    for eid in ids:
        row = [f"{summary[nm]['endings'].get(eid, 0) / n:.1%}" for nm in summary]
        title = content.endings[eid]["title"]
        out((f"| {title} | " + " | ".join(row) + " |") if md else f"{title[:34]:36}" + "".join(f"{r:>14}" for r in row))

    # ---------------------------------------------------------------- cobertura
    bal = summary["equilibrista"]
    out("\n## Cobertura de cartas (robô equilibrista)" if md else "\n== Cobertura de cartas (equilibrista) ==")
    never = [c for c in content.cards if bal["appear"].get(c, 0) == 0]
    rare = [(c, bal["appear"][c] / n) for c in content.cards if 0 < bal["appear"].get(c, 0) / n < 0.05]
    always = [(c, bal["appear"][c] / n) for c in content.cards if bal["appear"].get(c, 0) / n > 0.9]
    out(f"- cartas que NUNCA apareceram: {never or 'nenhuma'}")
    out(f"- cartas raras (<5% dos mandatos): {[(c, f'{p:.1%}') for c, p in rare] or 'nenhuma'}")
    out(f"- cartas em >90% dos mandatos: {[c for c, _ in always] or 'nenhuma'}")

    # ---------------------------------------------------------------- dilemas
    out("\n## Cartas em que o robô equilibrista quase sempre escolhe o mesmo lado\n(candidatas à revisão; várias são *tentações com custo adiado* que o robô não enxerga, como propina e licitação)" if md else "\n== Lado dominante (revisar; pode ser tentação com custo adiado) ==")
    weak = []
    for cid, cnt in bal["side"].items():
        tot = sum(cnt.values())
        if tot >= 30 and max(cnt.values()) / tot > 0.85:
            weak.append((cid, cnt.most_common(1)[0][0], max(cnt.values()) / tot))
    for cid, side, p in sorted(weak, key=lambda x: -x[2]):
        out(f"- {cid}: {side} em {p:.0%} dos casos")
    if not weak:
        out("- nenhuma (todas as cartas dividem as escolhas)")

    # ---------------------------------------------------------------- persistência
    out("\n## Sucessão: 6 mandatos seguidos com o mesmo save (robô equilibrista)" if md else "\n== Sucessão (6 mandatos) ==")
    seen_chain = Counter()
    ends_chain = Counter()
    seqs = 300
    for i in range(seqs):
        save = Save.memory()
        for m in range(6):
            run, cards, _ = play(content, bot_balanced, rng, save)
            seen_chain.update(set(cards))
            ends_chain[run.ending] += 1
    inh = [c for c in content.cards if c.startswith("heranca_")]
    out(f"- {seqs} sequências de 6 mandatos terminaram sem erro; glossário final: {len(save.glossary)}/{len(content.glossary)} termos")
    out("- cartas de herança (só aparecem após um final ruim): " + ", ".join(
        f"{c} em {seen_chain[c] / (seqs * 6):.1%} dos mandatos" for c in inh))
    never = [c for c in content.cards if seen_chain[c] == 0]
    out(f"- cartas que nunca apareceram em nenhuma sequência: {never or 'nenhuma'}")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
