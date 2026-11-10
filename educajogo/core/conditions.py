"""Mini-linguagem de condições usada por cartas, finais, objetivos e fluxo mensal.

Uma *lista* de condições significa E (todas precisam ser verdadeiras).
Cada condição é um dicionário. Exemplos:

    {"flag": "portal_publicado"}              flag do mandato atual ligada
    {"no_flag": "propina"}                    flag desligada
    {"meter": "cofre", "lt": 30}              medidor comparado (lt, lte, gt, gte, eq)
    {"counter": "multas", "gte": 2}           contador comparado
    {"month": ..., "gte": 12}                 mês do mandato (use {"month": true, "gte": 12})
    {"rel": "zeza", "gte": 1}                 relação com personagem
    {"seen": "vitor_1"} / {"not_seen": ...}   carta já apareceu neste mandato
    {"chose": "vitor_1", "side": "left"}      lado escolhido numa carta
    {"perm": "x"} / {"no_perm": "x"}          flag permanente (entre mandatos)
    {"selo": "mao_limpa"}                     selo conquistado alguma vez
    {"ending_seen": "operacao"}               final já visto alguma vez
    {"inherit": "operacao"}                   o mandato ANTERIOR terminou assim
    {"ending_kind": "victory"}                tipo do final deste mandato
    {"any": [[cond, ...], [cond, ...]]}       OU entre grupos de condições
"""

from __future__ import annotations

OPS = {
    "lt": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
    "gt": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "eq": lambda a, b: a == b,
}

# chave "principal" -> usada pelo validador para detectar condições mal escritas
CONDITION_KEYS = {
    "flag", "no_flag", "meter", "counter", "month", "rel", "seen", "not_seen",
    "chose", "perm", "no_perm", "selo", "ending_seen", "inherit", "ending_kind", "any",
}


def _compare(value, cond: dict) -> bool:
    for op, fn in OPS.items():
        if op in cond:
            return fn(value, cond[op])
    raise ValueError(f"condição sem operador de comparação: {cond}")


def check_one(cond: dict, run) -> bool:
    """Avalia UMA condição contra o estado `run` (core.engine.Run)."""
    if "any" in cond:
        return any(check(group, run) for group in cond["any"])
    if "flag" in cond:
        return cond["flag"] in run.flags
    if "no_flag" in cond:
        return cond["no_flag"] not in run.flags
    if "meter" in cond:
        return _compare(run.meters[cond["meter"]], cond)
    if "counter" in cond:
        return _compare(run.counters.get(cond["counter"], 0), cond)
    if "month" in cond:
        return _compare(run.month, cond)
    if "rel" in cond:
        return _compare(run.rel.get(cond["rel"], 0), cond)
    if "seen" in cond:
        return cond["seen"] in run.seen
    if "not_seen" in cond:
        return cond["not_seen"] not in run.seen
    if "chose" in cond:
        return run.choices.get(cond["chose"]) == cond["side"]
    if "perm" in cond:
        return cond["perm"] in run.perm.flags
    if "no_perm" in cond:
        return cond["no_perm"] not in run.perm.flags
    if "selo" in cond:
        return cond["selo"] in run.perm.selos
    if "ending_seen" in cond:
        return cond["ending_seen"] in run.perm.endings
    if "inherit" in cond:
        return run.inherit == cond["inherit"]
    if "ending_kind" in cond:
        return run.ending_kind == cond["ending_kind"]
    raise ValueError(f"condição desconhecida: {cond}")


def check(conds, run) -> bool:
    """Lista vazia/None = sempre verdadeiro."""
    if not conds:
        return True
    return all(check_one(c, run) for c in conds)


def walk(conds):
    """Percorre recursivamente todas as condições simples (para o validador)."""
    for c in conds or []:
        if "any" in c:
            for group in c["any"]:
                yield from walk(group)
        else:
            yield c
