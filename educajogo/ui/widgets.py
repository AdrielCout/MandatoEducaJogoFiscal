"""Componentes reutilizáveis: botão e rolagem."""

from __future__ import annotations

import pygame

from . import draw, theme as T


class Button:
    """Botão com texto, atalho de teclado opcional e estados normal/hover/desativado."""

    def __init__(self, rect, label, on_click, key=None, accent=None, size=22, sub=None, pad=56):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.key = key
        self.accent = accent or T.SUN
        self.size = size
        self.sub = sub
        self.pad = pad                                  # espaço lateral reservado (setas, atalhos)
        self.enabled = True
        self._press = 0.0

    def hover(self, pos) -> bool:
        return self.enabled and self.rect.collidepoint(pos)

    def click(self):
        if self.enabled:
            self._press = 0.12
            self.on_click()

    def update(self, dt):
        self._press = max(0.0, self._press - dt)

    def draw(self, surf, mouse):
        hov = self.hover(mouse)
        r = self.rect.copy()
        if self._press > 0:
            r.inflate_ip(-4, -4)
        fill = T.PANEL_2 if not hov else (44, 90, 114)
        if not self.enabled:
            fill = (30, 48, 58)
        draw.panel(surf, r, fill, self.accent if hov else T.LINE, radius=12, width=3 if hov else 2)
        col = T.TEXT if self.enabled else (110, 134, 146)
        # rótulo longo: primeiro encolhe a fonte; se ainda não couber, quebra em até 2 linhas (nunca vaza do botão)
        size = self.size
        max_lines = 1 if self.sub else 2
        while True:
            lines = draw.FONTS.wrap(draw.font(size, "bold"), self.label, r.w - self.pad)
            if len(lines) <= max_lines or size <= 14:
                break
            size -= 1
        if self.sub:
            draw.text(surf, lines[0], size, col, (r.centerx, r.centery - 9), "bold", "center")
            draw.text(surf, self.sub, 14, T.MUTED, (r.centerx, r.centery + 15), "regular", "center")
        else:
            lh = draw.font(size, "bold").get_linesize()
            y0 = r.centery - (len(lines) * lh) // 2 + lh // 2
            for n, ln in enumerate(lines):
                draw.text(surf, ln, size, col, (r.centerx, y0 + n * lh), "bold", "center")
        if self.key:
            draw.text(surf, self.key, 13, T.MUTED, (r.right - 8, r.top + 6), "regular", "topright")


class Scroller:
    """Rolagem vertical simples para listas longas (roda do mouse e setas)."""

    def __init__(self, area: pygame.Rect, content_h: int = 0, step: int = 40):
        self.area = pygame.Rect(area)
        self.content_h = content_h
        self.step = step
        self.y = 0

    @property
    def max(self) -> int:
        return max(0, self.content_h - self.area.h)

    def wheel(self, dy: int):
        self.y = max(0, min(self.max, self.y - dy * self.step))

    def to(self, y: int):
        self.y = max(0, min(self.max, y))

    def draw_bar(self, surf):
        if self.max <= 0:
            return
        track = pygame.Rect(self.area.right + 6, self.area.y, 6, self.area.h)
        draw.panel(surf, track, T.PANEL_2, radius=3)
        h = max(30, int(self.area.h * self.area.h / self.content_h))
        y = track.y + int((self.area.h - h) * (self.y / self.max))
        draw.panel(surf, (track.x, y, 6, h), T.MUTED, radius=3)
