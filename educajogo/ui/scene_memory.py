"""Memória da cidade: Caderno de Cidadania, finais vistos, mandatos anteriores e selos.

É o estado PERMANENTE do jogo (sobrevive entre mandatos e entre sessões).
"""

from __future__ import annotations

import pygame

from . import draw, theme as T
from .widgets import Button, Scroller

TABS = ["Caderno", "Finais", "Mandatos", "Selos"]


class MemoryScene:
    def __init__(self, app, back=None):
        self.app = app
        self.back = back
        self.tab = 0
        self.terms = list(app.content.glossary.items())
        unlocked = [i for i, (k, _) in enumerate(self.terms) if k in app.save.glossary]
        self.sel = unlocked[0] if unlocked else 0
        self.row_h = 36
        self.scroll = Scroller(pygame.Rect(30, 112, 400, 500), len(self.terms) * self.row_h, step=self.row_h)
        self.tab_buttons = [Button((30 + i * 176, 22, 166, 46), n, (lambda i=i: self.set_tab(i)), size=18) for i, n in enumerate(TABS)]
        self.btn_back = Button((1040, 22, 210, 46), "Voltar", self.leave, key="Esc", size=18)

    def set_tab(self, i):
        self.tab = i % len(TABS)
        self.app.sfx.play("click")

    def leave(self):
        self.app.sfx.play("click")
        if callable(self.back):
            self.back()
        elif self.back is not None:
            self.app.go(self.back)
        else:
            from .scene_menu import MenuScene
            self.app.go(MenuScene(self.app))

    # ---- eventos
    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.leave()
            elif pygame.K_1 <= e.key <= pygame.K_4:
                self.set_tab(e.key - pygame.K_1)
            elif e.key == pygame.K_RIGHT:
                self.set_tab(self.tab + 1)
            elif e.key == pygame.K_LEFT:
                self.set_tab(self.tab - 1)
            elif self.tab == 0 and e.key in (pygame.K_DOWN, pygame.K_UP):
                self.sel = max(0, min(len(self.terms) - 1, self.sel + (1 if e.key == pygame.K_DOWN else -1)))
                self.scroll.to(max(0, self.sel * self.row_h - self.scroll.area.h // 2))
        elif e.type == pygame.MOUSEWHEEL and self.tab == 0:
            self.scroll.wheel(e.y)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for b in self.tab_buttons + [self.btn_back]:
                if b.hover(e.pos):
                    b.click()
                    return
            if self.tab == 0 and self.scroll.area.collidepoint(e.pos):
                i = (e.pos[1] - self.scroll.area.y + self.scroll.y) // self.row_h
                if 0 <= i < len(self.terms):
                    self.sel = i
                    self.app.sfx.play("click")

    def update(self, dt):
        for b in self.tab_buttons + [self.btn_back]:
            b.update(dt)

    # ---- desenho
    def draw(self, s):
        for i, b in enumerate(self.tab_buttons):
            b.accent = T.SUN if i == self.tab else T.LINE
            b.draw(s, self.app.mouse)
            if i == self.tab:
                pygame.draw.rect(s, T.SUN, (b.rect.x + 14, b.rect.bottom + 4, b.rect.w - 28, 4), border_radius=2)
        self.btn_back.draw(s, self.app.mouse)
        [self._caderno, self._finais, self._mandatos, self._selos][self.tab](s)

    def _caderno(self, s):
        sv = self.app.save
        draw.text(s, f"{len(sv.glossary)} de {len(self.terms)} termos desbloqueados", 14, T.MUTED, (440, 82))
        area = self.scroll.area
        old = s.get_clip()
        s.set_clip(area)
        last_topic = None
        for i, (k, g) in enumerate(self.terms):
            y = area.y + i * self.row_h - self.scroll.y
            if y + self.row_h < area.y or y > area.bottom:
                continue
            got = k in sv.glossary
            r = pygame.Rect(area.x, y + 2, area.w, self.row_h - 4)
            draw.panel(s, r, T.PANEL_2 if i == self.sel else T.PANEL, T.SUN if i == self.sel else None, radius=8)
            if got:
                draw.check_mark(s, r.x + 16, r.centery, 6, T.GOOD, 3)
                draw.text(s, g["title"], 16, T.TEXT, (r.x + 36, r.y + 6), "bold" if i == self.sel else "regular")
            else:
                draw.lock(s, r.x + 16, r.centery - 1, 6, (96, 126, 140))
                draw.text(s, "? ? ?", 16, (96, 126, 140), (r.x + 36, r.y + 6))
        s.set_clip(old)
        self.scroll.draw_bar(s)
        k, g = self.terms[self.sel]
        box = pygame.Rect(460, 112, 790, 500)
        draw.panel(s, box, T.PANEL, T.LINE, alpha=240)
        if k in sv.glossary:
            draw.text(s, g["topic"].upper(), 13, T.SUN, (box.x + 30, box.y + 26), "bold")
            y = draw.paragraph(s, g["title"], 32, T.TEXT, (box.x + 30, box.y + 50, box.w - 60, 90), "serif", gap=4)
            draw.paragraph(s, g["text"], 20, T.TEXT, (box.x + 30, y + 16, box.w - 60, 320), gap=8)
        else:
            draw.lock(s, box.centerx, box.centery - 30, 22, (96, 126, 140))
            draw.text(s, "Termo ainda não descoberto", 22, T.MUTED, (box.centerx, box.centery + 20), "bold", "center")
            draw.text(s, f"Tema: {g['topic']}", 16, T.MUTED, (box.centerx, box.centery + 52), anchor="center")
            draw.text(s, "Jogue e tome decisões ligadas a este assunto para desbloquear.", 15, T.MUTED, (box.centerx, box.centery + 80), anchor="center")

    def _finais(self, s):
        sv, ct = self.app.save, self.app.content
        draw.text(s, f"{len(sv.endings)} de {len(ct.endings)} finais descobertos", 14, T.MUTED, (30, 82))
        for i, e in enumerate(ct.endings_list):
            r = pygame.Rect(30 + (i % 3) * 410, 112 + (i // 3) * 126, 396, 112)
            got = e["id"] in sv.endings
            draw.panel(s, r, T.PANEL, T.END_COLOR[e["tone"]] if got else T.LINE, width=3 if got else 2, alpha=240)
            pygame.draw.rect(s, T.END_COLOR[e["tone"]] if got else (60, 90, 106), (r.x, r.y + 10, 8, r.h - 20), border_radius=4)
            if got:
                draw.paragraph(s, e["title"], 18, T.TEXT, (r.x + 24, r.y + 12, r.w - 40, 50), "bold", gap=2)
                draw.paragraph(s, e["cause"], 14, T.MUTED, (r.x + 24, r.y + 66, r.w - 40, 40), gap=2)
            else:
                draw.lock(s, r.x + 40, r.centery - 2, 12, (96, 126, 140))
                draw.text(s, "Final ainda não visto", 16, (96, 126, 140), (r.x + 70, r.centery - 10))

    def _mandatos(self, s):
        sv, ct = self.app.save, self.app.content
        draw.text(s, "Cada mandato fica registrado. O próximo prefeito herda como o anterior terminou.", 14, T.MUTED, (30, 82))
        if not sv.history:
            draw.text(s, "Nenhum mandato concluído ainda.", 22, T.MUTED, (T.W // 2, 300), "bold", "center")
            return
        y = 112
        for h in reversed(sv.history[-9:]):
            e = ct.endings.get(h["ending"])
            r = pygame.Rect(30, y, 1220, 52)
            draw.panel(s, r, T.PANEL, T.END_COLOR[e["tone"]] if e else T.LINE, alpha=240)
            draw.text(s, f"{h['n']}º", 20, T.SUN, (r.x + 18, r.y + 13), "bold")
            draw.text(s, h["mayor"], 17, T.TEXT, (r.x + 80, r.y + 14), "bold")
            draw.text(s, e["title"] if e else h["ending"], 17, T.TEXT, (r.x + 330, r.y + 14))
            draw.text(s, f"{h['months']} meses · {h['decisions']} decisões", 15, T.MUTED, (r.right - 16, r.y + 16), anchor="topright")
            y += 58

    def _selos(self, s):
        sv, ct = self.app.save, self.app.content
        draw.text(s, f"{len(sv.selos)} de {len(ct.objectives)} selos conquistados", 14, T.MUTED, (30, 82))
        for i, o in enumerate(ct.objectives):
            r = pygame.Rect(30 + (i % 2) * 620, 112 + (i // 2) * 130, 600, 112)
            got = o["id"] in sv.selos
            draw.panel(s, r, T.PANEL, T.GOOD if got else T.LINE, width=3 if got else 2, alpha=240)
            pygame.draw.circle(s, T.GOOD if got else (60, 90, 106), (r.x + 50, r.centery), 28, 0 if got else 3)
            if got:
                draw.check_mark(s, r.x + 50, r.centery, 12, (14, 34, 46), 5)
            else:
                draw.lock(s, r.x + 50, r.centery - 2, 10, (96, 126, 140))
            draw.text(s, o["title"], 20, T.TEXT if got else T.MUTED, (r.x + 98, r.y + 22), "bold")
            draw.paragraph(s, o["desc"], 15, T.MUTED, (r.x + 98, r.y + 52, r.w - 120, 50), gap=3)

    def draw_debug(self, s):
        pass
