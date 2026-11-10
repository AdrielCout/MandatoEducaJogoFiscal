"""Classe base das cenas (menu, partida, fim, caderno)."""

from __future__ import annotations

import pygame

from . import draw, theme as T


class Scene:
    def __init__(self, app):
        self.app = app
        self.buttons: list = []

    # ciclo de vida
    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.click_buttons(e.pos)

    def update(self, dt):
        for b in self.buttons:
            b.update(dt)

    def draw(self, surf):
        pass

    def draw_debug(self, surf):
        pass

    # utilidades
    def click_buttons(self, pos) -> bool:
        for b in self.buttons:
            if b.hover(pos):
                self.app.sfx.play("click")
                b.click()
                return True
        return False

    def draw_buttons(self, surf):
        m = self.app.mouse
        for b in self.buttons:
            b.draw(surf, m)

    def debug_box(self, surf, lines, title="DEPURAÇÃO (F3)"):
        """Painel de depuração: mostra o estado interno para o mediador/professor."""
        w = 470
        h = 28 + 19 * len(lines) + 12
        r = pygame.Rect(8, T.H - h - 8, w, h)
        draw.panel(surf, r, (8, 16, 22), T.WARN, radius=8, alpha=232)
        draw.text(surf, title, 14, T.WARN, (r.x + 10, r.y + 6), "bold")
        for i, ln in enumerate(lines):
            draw.text(surf, ln[:78], 13, T.TEXT, (r.x + 10, r.y + 28 + i * 19))
