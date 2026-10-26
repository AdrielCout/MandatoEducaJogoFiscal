"""Testes do motor (sem pygame). Rodar:  python -m unittest discover -s tests -v

Cobrem a lista de verificação da seção 16 do guia de design: limites de derrota, efeitos
aplicados uma única vez, condições, eventos encadeados, sucessão e persistência.
"""

import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from educajogo.core.conditions import check  # noqa: E402
from educajogo.core.content import Content, validate  # noqa: E402
from educajogo.core.engine import Run  # noqa: E402
from educajogo.core.save import Save  # noqa: E402

CONTENT = Content()


def new_run(seed=1, save=None):
    return Run(CONTENT, save or Save.memory(), random.Random(seed))


def fake_card(left_fx=None, right_fx=None, **extra):
    """Carta sintética para testar regras isoladamente."""
    card = {
        "id": "_teste", "char": "tadeu", "type": "evento", "text": "x",
        "left": {"label": "a", "outcome": "o", "effects": left_fx or {}},
        "right": {"label": "b", "outcome": "o", "effects": right_fx or {}},
    }
    card.update(extra)
    return card


class ConteudoTests(unittest.TestCase):
    def test_conteudo_valido(self):
        errors, _ = validate(CONTENT)
        self.assertEqual(errors, [])

    def test_nenhuma_opcao_domina_a_outra(self):
        """Regra de design: NÃO existe resposta 'certa'. Uma opção domina a outra quando é
        melhor ou igual em todos os medidores. Isso transformaria a carta em quiz."""
        meters = CONTENT.meter_keys
        for cid, c in CONTENT.cards.items():
            if c.get("tutorial"):                  # a carta de abertura é a única exceção declarada
                continue
            a = [c["left"].get("effects", {}).get(m, 0) for m in meters]
            b = [c["right"].get("effects", {}).get(m, 0) for m in meters]
            if all(x >= y for x, y in zip(a, b)) or all(y >= x for x, y in zip(a, b)):
                self.fail(f"{cid}: uma opção é melhor ou igual à outra em todos os medidores {a} vs {b}")

    def test_os_dois_lados_de_cada_medidor_tem_final(self):
        for m in CONTENT.meter_keys:
            for side in ("low", "high"):
                self.assertTrue(any(e.get("meter") == m and e.get("side") == side for e in CONTENT.endings_list))


class MotorTests(unittest.TestCase):
    def test_primeira_carta_e_a_abertura(self):
        self.assertEqual(new_run().next_card()["id"], "intro")

    def test_next_card_e_idempotente_ate_escolher(self):
        r = new_run()
        self.assertIs(r.next_card(), r.next_card())

    def test_escolha_e_aplicada_uma_unica_vez(self):
        r = new_run()
        r.next_card()
        r.choose("left")
        with self.assertRaises(RuntimeError):
            r.choose("left")                       # clique duplo / animação: não conta de novo
        self.assertEqual(r.turn, 1)

    def test_efeitos_somam_e_fluxo_mensal_e_aplicado(self):
        r = new_run()
        r.current = fake_card({"povo": 10, "cofre": -5})
        before = dict(r.meters)
        res = r.choose("left")
        self.assertEqual(res.deltas["povo"], 10)
        self.assertEqual(res.deltas["cofre"], -5)
        flow_cofre = sum(e["cofre"] for _, e in r.flow_reasons() if "cofre" in e)
        # o fluxo vale para o mês (2 meses = escala 1)
        self.assertAlmostEqual(r.meters["cofre"], before["cofre"] - 5 + res.flow["cofre"], delta=1.01)
        self.assertEqual(r.month, 2)

    def test_limite_fatal_inferior_e_superior(self):
        for meter, sign, ending in (("cofre", -1, "cofre_baixo"), ("cofre", 1, "cofre_alto"),
                                    ("povo", -1, "povo_baixo"), ("integridade", 1, "integridade_alto")):
            r = new_run()
            r.current = fake_card({meter: 200 * sign})
            res = r.choose("left")
            self.assertEqual(res.ended, ending)
            self.assertTrue(r.finished)
            self.assertTrue(0 <= r.meters[meter] <= 100)       # nunca fora da escala

    def test_final_por_evento_tem_prioridade_sobre_medidor(self):
        r = new_run()
        card = fake_card({"cofre": -200})
        card["left"]["end"] = "operacao"
        r.current = card
        self.assertEqual(r.choose("left").ended, "operacao")

    def test_vitoria_ao_completar_48_meses(self):
        r = new_run()
        r.month = 46
        r.meters = {k: 50.0 for k in r.meters}
        r.current = fake_card()
        res = r.choose("left")
        self.assertEqual(res.ended, "mandato_exemplar")
        self.assertEqual(r.ending_kind, "victory")

    def test_mandato_sob_suspeita_quando_houve_propina(self):
        r = new_run()
        r.month = 46
        r.meters = {k: 50.0 for k in r.meters}
        r.flags.add("propina")
        r.current = fake_card()
        self.assertEqual(r.choose("left").ended, "mandato_sob_suspeita")

    def test_consequencia_adiada_e_forcada_no_mes_certo(self):
        r = new_run(seed=3)
        r.current = CONTENT.cards["vitor_1"]
        r.choose("left")                                       # aceita o "acordo" (propina)
        self.assertIn("propina", r.flags)
        aparecidas = []
        for _ in range(12):
            if r.finished:
                break
            aparecidas.append(r.next_card()["id"])
            r.choose("left" if r.current is None else "left")
        self.assertIn("operacao_1", aparecidas, "a propina precisa voltar como investigação")

    def test_carta_nao_repete_no_mesmo_mandato(self):
        r = new_run(seed=5)
        ids = []
        while not r.finished and len(ids) < 40:
            c = r.next_card()
            ids.append(c["id"])
            r.choose(random.Random(len(ids)).choice(("left", "right")))
        repetiveis = {i for i, c in CONTENT.cards.items() if c.get("repeat")}
        dup = {i for i in ids if ids.count(i) > 1} - repetiveis
        self.assertEqual(dup, set())

    def test_nunca_fica_sem_carta(self):
        """Mil mandatos aleatórios: sempre há carta e o mandato sempre termina."""
        rng = random.Random(7)
        for _ in range(300):
            r = Run(CONTENT, Save.memory(), random.Random(rng.random()))
            guard = 0
            while not r.finished:
                self.assertIsNotNone(r.next_card())
                r.choose(rng.choice(("left", "right")))
                guard += 1
                self.assertLess(guard, 100)

    def test_dicas_nao_revelam_direcao(self):
        r = new_run()
        card = CONTENT.cards["saude_posto"]
        hints = r.hints(card, "left")
        self.assertTrue(all(v in (1, 2, 3) for v in hints.values()))

    def test_aprendizado_registrado_uma_vez(self):
        r = new_run()
        r.current = CONTENT.cards["saude_posto"]
        res = r.choose("left")
        self.assertEqual(res.new_terms, ["minimos_constitucionais"])
        r.current = CONTENT.cards["escola_flores"]
        r.current = fake_card(learn="minimos_constitucionais")
        self.assertEqual(r.choose("left").new_terms, [])


class CondicoesTests(unittest.TestCase):
    def test_operadores_e_ou(self):
        r = new_run()
        r.meters["cofre"] = 30
        r.flags.add("x")
        self.assertTrue(check([{"meter": "cofre", "lt": 31}, {"flag": "x"}], r))
        self.assertFalse(check([{"meter": "cofre", "gt": 31}], r))
        self.assertTrue(check([{"any": [[{"flag": "nao"}], [{"flag": "x"}]]}], r))
        self.assertTrue(check(None, r))

    def test_condicao_desconhecida_falha_alto(self):
        with self.assertRaises(ValueError):
            check([{"banana": 1}], new_run())


class PersistenciaTests(unittest.TestCase):
    def test_save_ida_e_volta(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.json"
            s = Save(path=p)
            s.glossary.update({"tributo", "lrf"})
            s.flags.add("herdou_operacao")
            s.mandates = 3
            s.mediator_mode = False
            self.assertTrue(s.write())
            t = Save.load(p)
            self.assertEqual(t.glossary, {"tributo", "lrf"})
            self.assertEqual(t.flags, {"herdou_operacao"})
            self.assertEqual((t.mandates, t.mediator_mode), (3, False))

    def test_save_corrompido_recomeca_limpo(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "s.json"
            p.write_text("{ isto nao e json", encoding="utf-8")
            self.assertEqual(Save.load(p).mandates, 0)

    def test_save_em_local_sem_permissao_nao_derruba_o_jogo(self):
        s = Save(path=Path("/proc/nao_pode/escrever.json"))
        self.assertFalse(s.write())

    def test_sucessao_herda_o_fim_anterior(self):
        save = Save.memory()
        r1 = Run(CONTENT, save, random.Random(1))
        r1.current = fake_card({"cofre": -200})
        self.assertEqual(r1.choose("left").ended, "cofre_baixo")
        r2 = Run(CONTENT, save, random.Random(1))
        self.assertEqual(r2.inherit, "cofre_baixo")
        self.assertNotEqual(r2.mayor_name, r1.mayor_name)      # novo(a) prefeito(a)
        self.assertEqual(r2.mandate_no, 2)
        self.assertIn("cofre_baixo", save.endings)
        self.assertEqual(save.history[0]["ending"], "cofre_baixo")

    def test_estado_permanente_nao_vaza_para_o_temporario(self):
        save = Save.memory()
        r1 = Run(CONTENT, save, random.Random(2))
        r1.flags.add("propina")
        r1.current = fake_card({"cofre": -200})
        r1.choose("left")
        r2 = Run(CONTENT, save, random.Random(2))
        self.assertNotIn("propina", r2.flags)                   # flags do mandato não atravessam


if __name__ == "__main__":
    unittest.main()
