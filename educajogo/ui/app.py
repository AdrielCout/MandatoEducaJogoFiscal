"""Aplicação: laço principal (assíncrono, compatível com pygbag/navegador), escala da tela e cenas.

O jogo desenha sempre numa superfície lógica de 1280x720; a janela pode ter qualquer tamanho
(a imagem é escalada mantendo a proporção e o mouse é convertido de volta).
"""

from __future__ import annotations

import asyncio

import pygame

from ..core.content import Content
from ..core.save import Save
from . import draw, theme as T
from .sfx import Sfx


class App:
    def __init__(self, save: Save | None = None, content: Content | None = None, size=(1280, 720), caption="Mandato"):
        pygame.init()
        draw.reset_caches()
        pygame.display.set_caption(caption)
        self.window = pygame.display.set_mode(size, pygame.RESIZABLE)
        self.canvas = pygame.Surface((T.W, T.H))
        self.clock = pygame.time.Clock()
        self.content = content or Content()
        self.save = save if save is not None else Save.load()
        self.sfx = Sfx(self.save.muted)
        self.running = True
        self.scene = None
        self.debug = False
        self.time = 0.0
        self._offset = (0, 0)
        self._scale = 1.0
        from .scenes import MenuScene                 # import tardio: evita ciclo app <-> cenas
        self.go(MenuScene(self))

    # ------------------------------------------------------------------ cenas
    def go(self, scene):
        self.scene = scene

    def quit(self):
        self.save.write()
        self.running = False

    # ------------------------------------------------------------------ entrada
    def to_logical(self, pos):
        ox, oy = self._offset
        s = self._scale or 1.0
        return (int((pos[0] - ox) / s), int((pos[1] - oy) / s))

    @property
    def mouse(self):
        return self.to_logical(pygame.mouse.get_pos())

    def handle(self, e: pygame.event.Event):
        if e.type == pygame.QUIT:
            self.quit()
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_F3:
            self.debug = not self.debug
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
            pygame.display.toggle_fullscreen()
            return
        if e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            d = dict(e.dict)
            d["pos"] = self.to_logical(e.pos)
            e = pygame.event.Event(e.type, d)
        self.scene.handle(e)

    # ------------------------------------------------------------------ quadro
    def update(self, dt: float):
        self.time += dt
        self.scene.update(dt)

    def render(self):
        self.canvas.blit(self_bg(), (0, 0))
        self.scene.draw(self.canvas)
        if self.debug:
            self.scene.draw_debug(self.canvas)
        ww, wh = self.window.get_size()
        s = min(ww / T.W, wh / T.H)
        self._scale = s
        size = (max(1, int(T.W * s)), max(1, int(T.H * s)))
        self._offset = ((ww - size[0]) // 2, (wh - size[1]) // 2)
        self.window.fill((6, 14, 20))
        img = self.canvas if size == (T.W, T.H) else pygame.transform.smoothscale(self.canvas, size)
        self.window.blit(img, self._offset)
        pygame.display.flip()

    def tick(self, dt: float | None = None):
        """Um quadro completo. `dt` é injetável para testes determinísticos."""
        if dt is None:
            dt = min(0.05, self.clock.tick(T.FPS) / 1000.0)
        for e in pygame.event.get():
            self.handle(e)
        self.update(dt)
        self.render()


def self_bg():
    return draw.background()


async def run(save: Save | None = None):
    """Laço principal. `await asyncio.sleep(0)` entrega o controle ao navegador (pygbag)."""
    app = App(save)
    while app.running:
        app.tick()
        await asyncio.sleep(0)
    pygame.quit()


def main():
    asyncio.run(run())
