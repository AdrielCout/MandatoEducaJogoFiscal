"""Testes da interface, sem janela (SDL em modo 'dummy'). Rodar: python -m unittest discover -s tests -v"""

import os
import random
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["MANDATO_SAVE_DIR"] = tempfile.mkdtemp(prefix="mandato_test_")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame  # noqa: E402

from educajogo.core.save import Save  # noqa: E402
from educajogo.ui.app import App  # noqa: E402
from educajogo.ui.scenes import EndScene, GameScene, GlossaryScene, HistoryScene, MenuScene  # noqa: E402


def click(pos):
    return [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos),
            pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos)]


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.app = App(save=Save.memory(), size=(1280, 720))

    def test_menu_desenha(self):
        self.assertIsInstance(self.app.scene, MenuScene)
        self.app.tick(0.05)

    def test_botao_comecar_abre_partida(self):
        self.app.scene.start()
        self.assertIsInstance(self.app.scene, GameScene)
        self.app.debug = True
        self.app.tick(0.05)                    # desenha com depuração ligada
        self.app.debug = False

    def test_partida_completa_so_pela_interface(self):
        rng = random.Random(4)
        self.app.scene.start()
        steps = 0
        while not isinstance(self.app.scene, EndScene):
            g = self.app.scene
            g.decide(rng.choice(("left", "right")))
            self.app.tick(0.05)                # desenha o painel de consequência
            g.proceed()
            self.app.tick(0.05)
            steps += 1
            self.assertLess(steps, 200, "mandato não terminou")
        self.assertTrue(self.app.scene.run.finished)
        self.app.tick(0.05)

    def test_clique_duplo_conta_uma_vez(self):
        self.app.scene.start()
        g = self.app.scene
        g.decide("left")
        turno = g.run.turn
        g.decide("left")                      # segundo clique enquanto o painel está aberto
        g.decide("right")
        self.assertEqual(g.run.turn, turno)

    def test_arrastar_a_carta_decide(self):
        self.app.scene.start()
        g = self.app.scene
        cx, cy = g.card_rect().center
        self.app.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(cx, cy)))
        self.app.handle(pygame.event.Event(pygame.MOUSEMOTION, pos=(cx - 220, cy), rel=(0, 0), buttons=(1, 0, 0)))
        self.app.handle(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(cx - 220, cy)))
        self.assertIsNotNone(g.result)
        self.assertEqual(g.result.side, "left")

    def test_arrastar_pouco_nao_decide(self):
        self.app.scene.start()
        g = self.app.scene
        cx, cy = g.card_rect().center
        self.app.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(cx, cy)))
        self.app.handle(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(cx + 10, cy)))
        self.assertIsNone(g.result)

    def test_teclas_decidem(self):
        self.app.scene.start()
        g = self.app.scene
        g.key(pygame.K_RIGHT)
        self.assertEqual(g.result.side, "right")

    def test_caderno_e_historico_desenham(self):
        self.app.go(GlossaryScene(self.app))
        self.app.tick(0.05)
        self.app.go(HistoryScene(self.app))
        self.app.tick(0.05)

    def test_clique_no_menu_vai_para_caderno(self):
        menu = self.app.scene
        glossary_btn = menu.buttons[1]
        for e in click(glossary_btn.rect.center):
            self.app.handle(e)
        self.assertIsInstance(self.app.scene, GlossaryScene)

    def test_mediador_liga_e_desliga(self):
        before = self.app.save.mediator_mode
        self.app.scene.toggle_mediator()
        self.assertNotEqual(self.app.save.mediator_mode, before)

    def test_fim_do_mandato_grava_historico(self):
        self.app.scene.start()
        rng = random.Random(9)
        while not isinstance(self.app.scene, EndScene):
            self.app.scene.decide(rng.choice(("left", "right")))
            self.app.scene.proceed()
        self.assertEqual(len(self.app.save.history), 1)
        self.app.scene.next_mandate()
        self.assertIsInstance(self.app.scene, GameScene)
        self.assertEqual(self.app.scene.run.mandate_no, 2)


if __name__ == "__main__":
    unittest.main()
