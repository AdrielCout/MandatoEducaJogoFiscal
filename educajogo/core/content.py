"""Carrega e VALIDA o conteúdo em data/. Todo o conteúdo do jogo é dado, não código."""

from __future__ import annotations

import json
from pathlib import Path

from .conditions import CONDITION_KEYS, walk

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

MAX_CARD_TEXT = 175
MAX_LABEL = 26


class Content:
    def __init__(self, data_dir: Path | None = None):
        d = Path(data_dir or DATA_DIR)
        self.config = self._load(d / "config.json")
        self.characters = self._load(d / "characters.json")
        self.glossary = self._load(d / "glossary.json")
        self.objectives = self._load(d / "objectives.json")
        self.endings_list = self._load(d / "endings.json")
        self.endings = {e["id"]: e for e in self.endings_list}
        self.cards: dict[str, dict] = {}
        self.card_order: list[str] = []
        for f in sorted(d.glob("cards_*.json")):
            for c in self._load(f):
                c["_file"] = f.name
                if c["id"] in self.cards:
                    raise ValueError(f"id de carta duplicado: {c['id']}")
                self.cards[c["id"]] = c
                self.card_order.append(c["id"])

    @staticmethod
    def _load(path: Path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    @property
    def meter_keys(self) -> list[str]:
        return list(self.config["meters"].keys())


def validate(content: Content) -> tuple[list[str], list[str]]:
    """Retorna (erros, avisos). Erro = o jogo pode quebrar; aviso = provável deslize."""
    errors: list[str] = []
    warns: list[str] = []
    meters = set(content.meter_keys)
    chars = set(content.characters)
    terms = set(content.glossary)
    cards = content.cards

    flags_set: set[str] = set()
    flags_used: set[str] = set()
    perm_set: set[str] = set()
    perm_used: set[str] = set()

    def scan_conds(where: str, conds):
        for c in walk(conds):
            keys = set(c) & CONDITION_KEYS
            if len(keys) != 1:
                errors.append(f"{where}: condição inválida {c}")
                continue
            if "flag" in c:
                flags_used.add(c["flag"])
            if "no_flag" in c:
                flags_used.add(c["no_flag"])
            if "perm" in c:
                perm_used.add(c["perm"])
            if "no_perm" in c:
                perm_used.add(c["no_perm"])
            if "meter" in c and c["meter"] not in meters:
                errors.append(f"{where}: medidor inexistente '{c['meter']}'")
            if "seen" in c and c["seen"] not in cards:
                errors.append(f"{where}: seen -> carta inexistente '{c['seen']}'")
            if "not_seen" in c and c["not_seen"] not in cards:
                errors.append(f"{where}: not_seen -> carta inexistente '{c['not_seen']}'")
            if "chose" in c and c["chose"] not in cards:
                errors.append(f"{where}: chose -> carta inexistente '{c['chose']}'")
            if "rel" in c and c["rel"] not in chars:
                errors.append(f"{where}: rel -> personagem inexistente '{c['rel']}'")
            for key in ("ending_seen", "inherit"):
                if key in c and c[key] not in content.endings:
                    errors.append(f"{where}: {key} -> final inexistente '{c[key]}'")

    def scan_effects(where: str, opt: dict):
        for k in opt.get("effects", {}):
            if k not in meters:
                errors.append(f"{where}: medidor inexistente '{k}' em effects")
        flags_set.update(opt.get("flags_set", []))
        perm_set.update(opt.get("perm", []))
        for ch in opt.get("rel", {}):
            if ch not in chars:
                errors.append(f"{where}: rel -> personagem inexistente '{ch}'")
        for s in opt.get("schedule", []):
            if s["card"] not in cards:
                errors.append(f"{where}: schedule -> carta inexistente '{s['card']}'")
            scan_conds(where + ".schedule.if", s.get("if"))
        for cid in opt.get("cancel", []):
            if cid not in cards:
                errors.append(f"{where}: cancel -> carta inexistente '{cid}'")
        if "end" in opt and opt["end"] not in content.endings:
            errors.append(f"{where}: end -> final inexistente '{opt['end']}'")
        if opt.get("learn") and opt["learn"] not in terms:
            errors.append(f"{where}: learn -> termo inexistente '{opt['learn']}'")

    # ----- cartas -----
    scheduled_targets: set[str] = set()
    for cid, c in cards.items():
        w = f"carta {cid}"
        if c.get("char") not in chars:
            errors.append(f"{w}: personagem inexistente '{c.get('char')}'")
        if len(c["text"]) > MAX_CARD_TEXT:
            warns.append(f"{w}: texto longo ({len(c['text'])} car.; limite {MAX_CARD_TEXT})")
        for side in ("left", "right"):
            if side not in c:
                errors.append(f"{w}: falta '{side}'")
                continue
            opt = c[side]
            if "label" not in opt or "outcome" not in opt:
                errors.append(f"{w}.{side}: precisa de 'label' e 'outcome'")
                continue
            if len(opt["label"]) > MAX_LABEL:
                warns.append(f"{w}.{side}: rótulo longo '{opt['label']}'")
            scan_effects(f"{w}.{side}", opt)
            for s in opt.get("schedule", []):
                scheduled_targets.add(s["card"])
        if c.get("learn") and c["learn"] not in terms:
            errors.append(f"{w}: learn -> termo inexistente '{c['learn']}'")
        scan_conds(w + ".req", c.get("req"))
        for b in c.get("boost", []):
            scan_conds(w + ".boost", b.get("when"))
        # mesma escolha entregando efeito total zero em ambas -> não é dilema
        for side in ("left", "right"):
            if side in c and not any(c[side].get("effects", {}).values()) and not c[side].get("schedule") and not c[side].get("flags_set") and not c[side].get("end"):
                warns.append(f"{w}.{side}: opção sem nenhum efeito")

    for cid, c in cards.items():
        if c.get("weight", 10) == 0 and cid not in scheduled_targets and cid != content.config.get("intro_card"):
            errors.append(f"carta {cid}: weight 0 e ninguém a agenda (nunca aparece)")

    if content.config.get("intro_card") not in cards:
        errors.append("config.intro_card aponta para carta inexistente")

    # ----- fluxo mensal -----
    for i, r in enumerate(content.config.get("recurring", [])):
        scan_conds(f"recurring[{i}]", r.get("when"))
        for k in r["effects"]:
            if k not in meters:
                errors.append(f"recurring[{i}]: medidor inexistente '{k}'")
    for i, m in enumerate(content.config.get("start_mods", [])):
        scan_conds(f"start_mods[{i}]", m.get("when"))

    # ----- finais -----
    for m in meters:
        for side in ("low", "high"):
            if not any(e.get("kind") == "fatal" and e.get("meter") == m and e.get("side") == side for e in content.endings_list):
                errors.append(f"falta final fatal para {m}/{side}")
    victories = [e for e in content.endings_list if e["kind"] == "victory"]
    if not victories:
        errors.append("nenhum final de vitória")
    elif victories[-1].get("when"):
        errors.append("o último final de vitória precisa ser o 'padrão' (sem 'when')")
    for e in content.endings_list:
        scan_conds(f"final {e['id']}", e.get("when"))
        perm_set.update(e.get("perm", []))
        for t in e.get("learn", []):
            if t not in terms:
                errors.append(f"final {e['id']}: termo inexistente '{t}'")

    # ----- objetivos -----
    for o in content.objectives:
        scan_conds(f"objetivo {o['id']}", o.get("when"))

    # ----- termos do glossário nunca usados -----
    used_terms = set()
    for c in cards.values():
        if c.get("learn"):
            used_terms.add(c["learn"])
        for side in ("left", "right"):
            if c.get(side, {}).get("learn"):
                used_terms.add(c[side]["learn"])
    for e in content.endings_list:
        used_terms.update(e.get("learn", []))
    for t in sorted(terms - used_terms):
        warns.append(f"termo do glossário '{t}' nunca é ensinado por nenhuma carta ou final")

    # ----- consistência de flags -----
    for f in sorted(flags_used - flags_set):
        warns.append(f"flag '{f}' é lida mas nunca é ligada por nenhuma opção")
    for f in sorted(flags_set - flags_used):
        warns.append(f"flag '{f}' é ligada mas nunca é lida (talvez inútil)")
    for f in sorted(perm_used - perm_set):
        warns.append(f"flag permanente '{f}' é lida mas nunca ligada")
    return errors, warns
