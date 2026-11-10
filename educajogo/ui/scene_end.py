"""Tela final: prestação de contas. A derrota também é progressão (guia, seção 4)."""

from __future__ import annotations

import pygame

from . import draw, theme as T
from .widgets import Button, Scroller


class EndScene:
    def __init__(self, app, run, new_terms, new_selos):
        self.app = app
        self.run = run
        self.new_terms = new_terms
        self.new_selos = new_selos
        self.sum = run.summary()
        self.end = self.sum["ending"]
        self.t = 0.0
        self.rows = self.sum["history"]
        self.scroll = Scroller(pygame.Rect(660, 292, 572, 292), len(self.rows) * 46, step=46)
        self.buttons = [
            Button((24, 636, 300, 56), "Próximo mandato", self.again, key="Enter", size=21),
            Button((340, 636, 220, 56), "Caderno", self.memory, key="C", size=21),
            Button((576, 636, 180, 56), "Menu", self.menu, key="Esc", size=21),
        ]
        app.save.write()
        tone = self.end["tone"]
        app.sfx.play("win" if tone == "good" else ("stamp" if tone == "mid" else "lose"))

    # ---- navegação
    def again(self):
        from .scene_game import GameScene
        self.app.go(GameScene(self.app))

    def memory(self):
        from .scene_memory import MemoryScene
        self.app.go(MemoryScene(self.app, back=self))

    def menu(self):
        from .scene_menu import MenuScene
        self.app.go(MenuScene(self.app))

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.again()
            elif e.key == pygame.K_c:
                self.memory()
            elif e.key == pygame.K_ESCAPE:
                self.menu()
            elif e.key == pygame.K_DOWN:
                self.scroll.wheel(-1)
            elif e.key == pygame.K_UP:
                self.scroll.wheel(1)
        elif e.type == pygame.MOUSEWHEEL:
            self.scroll.wheel(e.y)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for b in self.buttons:
                if b.hover(e.pos):
                    b.click()

    def update(self, dt):
        self.t += dt
        for b in self.buttons:
            b.update(dt)

    # ---- desenho
    def draw(self, s):
        cfg = self.app.content.config
        e, run = self.end, self.run
        col = T.END_COLOR[e["tone"]]
        # painel esquerdo: o que aconteceu e por quê
        left = pygame.Rect(24, 20, 612, 600)
        draw.panel(s, left, T.PANEL, col, width=3, alpha=240, shadow=True)
        x, w = left.x + 24, left.w - 48
        kind = {"victory": "MANDATO CONCLUÍDO", "fatal": "O MANDATO TERMINOU", "event": "O MANDATO TERMINOU"}[e["kind"]]
        draw.text(s, kind, 14, col, (x, left.y + 20), "bold")
        y = draw.paragraph(s, e["title"], 32, T.TEXT, (x, left.y + 46, w, 90), "serif", gap=4)
        draw.text(s, e["cause"], 15, T.MUTED, (x, y + 2))
        y = draw.paragraph(s, run.fmt(e["text"]), 18, T.TEXT, (x, y + 30, w, 170), gap=5)
        bh = draw.paragraph_height(e["concept"], 16, w - 28, gap=4) + 40
        box = pygame.Rect(x, y + 8, w, bh)
        draw.panel(s, box, (252, 244, 214), (190, 150, 60), radius=12)
        draw.text(s, "O CONCEITO FISCAL", 13, (140, 96, 20), (box.x + 14, box.y + 10), "bold")
        draw.paragraph(s, e["concept"], 16, T.INK, (box.x + 14, box.y + 32, box.w - 28, bh), gap=4)
        y = box.bottom + 14
        draw.text(s, "PARA CONVERSAR COM A TURMA", 13, T.SUN, (x, y), "bold")
        y += 22
        for q in e.get("discuss", []):
            pygame.draw.circle(s, T.SUN, (x + 5, y + 9), 4)
            y = draw.paragraph(s, q, 16, T.TEXT, (x + 18, y, w - 18, 60), gap=3) + 4

        # painel direito: prestação de contas
        right = pygame.Rect(652, 20, 604, 600)
        draw.panel(s, right, T.PANEL, T.LINE, alpha=240, shadow=True)
        rx, rw = right.x + 24, right.w - 48
        draw.text(s, "PRESTAÇÃO DE CONTAS", 14, T.SUN, (rx, right.y + 20), "bold")
        draw.text(s, f"{run.mayor_t.capitalize()} {run.mayor_name} · {self.sum['months']} meses · {self.sum['decisions']} decisões",
                  16, T.TEXT, (rx, right.y + 42), "bold")
        for i, key in enumerate(cfg["meters"]):
            by = right.y + 78 + i * 28
            v = self.sum["meters"][key]
            pygame.draw.circle(s, T.METER_COLOR[key], (rx + 11, by + 10), 11)
            draw.icon(s, cfg["meters"][key]["icon"], rx + 11, by + 10, 7, (14, 34, 46))
            draw.text(s, cfg["meters"][key]["name"], 15, T.TEXT, (rx + 30, by + 1))
            bar = pygame.Rect(rx + 170, by + 3, 320, 14)
            draw.panel(s, bar, (12, 28, 38), radius=7)
            bad = v <= 0 or v >= 100
            draw.panel(s, (bar.x, bar.y, max(6, int(bar.w * v / 100)), 14), T.BAD if bad else T.METER_COLOR[key], radius=7)
            draw.text(s, str(v), 15, T.TEXT, (bar.right + 12, by + 1), "bold")
        gy = right.y + 200
        if self.new_terms or self.new_selos:
            parts = []
            if self.new_terms:
                parts.append(f"{len(self.new_terms)} termo(s) novo(s) no Caderno")
            if self.new_selos:
                parts.append(f"{len(self.new_selos)} selo(s)")
            draw.text(s, "Desbloqueado: " + " · ".join(parts), 15, T.GOOD, (rx, gy), "bold")
        else:
            draw.text(s, f"Caderno: {len(self.app.save.glossary)}/{len(self.app.content.glossary)} termos · "
                         f"Finais vistos: {len(self.app.save.endings)}/{len(self.app.content.endings)}", 15, T.MUTED, (rx, gy))
        draw.text(s, "LINHA DO TEMPO DAS DECISÕES", 13, T.SUN, (rx, right.y + 256), "bold")

        area = self.scroll.area
        old = s.get_clip()
        s.set_clip(area)
        for i, h in enumerate(self.rows):
            yy = area.y + i * 46 - self.scroll.y
            if yy + 46 < area.y or yy > area.bottom:
                continue
            ch = self.app.content.characters[h["char"]]["name"]
            draw.text(s, f"Mês {h['month']}", 13, T.MUTED, (area.x, yy + 2))
            draw.text(s, ch, 13, T.MUTED, (area.x + 70, yy + 2))
            draw.text(s, h["label"], 16, T.TEXT, (area.x, yy + 18), "bold")
            if h.get("learn"):
                g = self.app.content.glossary[h["learn"]]["title"]
                draw.text(s, g, 13, T.SUN, (area.right, yy + 4), anchor="topright")
            pygame.draw.line(s, T.LINE, (area.x, yy + 44), (area.right, yy + 44))
        s.set_clip(old)
        self.scroll.draw_bar(s)
        for b in self.buttons:
            b.draw(s, self.app.mouse)

    def draw_debug(self, s):
        pass
