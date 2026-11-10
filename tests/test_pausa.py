"""Testes do menu de pausa durante a partida. Rodar: python -m unittest discover -s tests -v"""

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
from educajogo.ui.scenes import GameScene, HowToScene, MenuScene  # noqa: E402


def esc():
    return pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode="", scancode=0)


class PausaTests(unittest.TestCase):
    def setUp(self):
        self.app = App(save=Save.memory(), size=(1280, 720))
        self.app.scene.start()
        self.app.scene.begin()
        self.g = self.app.scene
        self.assertIsInstance(self.g, GameScene)

    def test_esc_abre_e_fecha_a_pausa(self):
        self.app.handle(esc())
        self.assertTrue(self.g.paused)
        self.app.handle(esc())
        self.assertFalse(self.g.paused)

    def test_botao_menu_abre_a_pausa(self):
        r = self.g.menu_btn.rect
        self.app.handle(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=r.center))
        self.assertTrue(self.g.paused)

    def test_decisao_bloqueada_durante_a_pausa(self):
        self.app.handle(esc())
        self.g.decide("left")
        self.assertIsNone(self.g.result)
        self.assertEqual(self.g.run.turn, 0)

    def test_voltar_ao_menu_leva_para_o_menu_sem_registrar_mandato(self):
        self.app.handle(esc())
        btn = self.g.pause_btns[1]
        self.app.handle(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=btn.rect.center))
        self.assertIsInstance(self.app.scene, MenuScene)
        self.assertEqual(self.app.save.history, [])
        self.assertEqual(self.app.save.mandates, 0)

    def test_desenha_com_pausa_aberta(self):
        self.app.handle(esc())
        self.app.tick(0.05)

    def test_esc_no_inicio_do_mandato_volta_ao_jogo_depois_de_ver_a_instrucao(self):
        self.app.go(HowToScene(self.app))
        self.app.handle(esc())
        self.assertIsInstance(self.app.scene, MenuScene)


if __name__ == "__main__":
    unittest.main()
