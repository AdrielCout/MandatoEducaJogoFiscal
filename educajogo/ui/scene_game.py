"""Cena da partida: carta arrastável, medidores, painel de resultado e painéis laterais."""

from __future__ import annotations

import random

import pygame

from ..core.engine import Run
from . import draw, theme as T
from .widgets import Button

DRAG_COMMIT = 110          # pixels arrastados para confirmar a decisão
METER_X = (110, 380, 650, 920)
METER_Y = 20


class GameScene:
    def __init__(self, app):
        self.app = app
        # `app.seed` (opcional) torna o mandato reprodutível: usado nas capturas de tela e na depuração
        self.run = Run(app.content, app.save, random.Random(getattr(app, "seed", None)))
        self.cfg = app.content.config
        self.card = self.run.next_card()
        self.phase = "enter"           # enter -> idle -> exit -> outcome -> (enter | fim)
        self.t = 0.0
        self.dx = 0.0
        self.dragging = False
        self.drag_x0 = 0
        self.res = None
        self.side = None
        self.disp = dict(self.run.meters)
        self.floats: list[dict] = []
        self.new_terms: list[str] = []
        self.new_selos: list[str] = []
        self.paused = False
        self.tips = self._build_tips()
        self.btn_left = Button((CARD_L, 610, 215, 62), "", lambda: self.pick("left"), accent=T.SUN, size=19)
        self.btn_right = Button((CARD_R, 610, 215, 62), "", lambda: self.pick("right"), accent=T.SUN, size=19)
        self.btn_next = Button((T.W // 2 - 110, 622, 220, 50), "Continuar", self.advance, key="Espaço", size=21)
        self.pause_buttons = [
            Button((T.W // 2 - 150, 300, 300, 56), "Continuar", lambda: self._pause(False), size=22),
            Button((T.W // 2 - 150, 372, 300, 56), "Voltar ao menu", self._to_menu, size=22),
        ]

    # ------------------------------------------------------------------ util
    @property
    def mode(self) -> str:
        """'card' enquanto há uma carta na tela (entrando, parada ou saindo); 'outcome' no painel de resultado."""
        return "card" if self.phase in ("enter", "idle", "exit") else "outcome"

    @property
    def btn(self) -> dict:
        return {"left": self.btn_left, "right": self.btn_right}

    def _build_tips(self):
        tips = {}
        for k in self.app.content.meter_keys:
            lo = next(e for e in self.app.content.endings_list if e.get("meter") == k and e.get("side") == "low")
            hi = next(e for e in self.app.content.endings_list if e.get("meter") == k and e.get("side") == "high")
            tips[k] = (lo["title"], hi["title"])
        return tips

    def _pause(self, v):
        self.paused = v
        self.app.sfx.play("click")

    def _to_menu(self):
        from .scene_menu import MenuScene
        self.app.save.write()
        self.app.go(MenuScene(self.app))

    def _preview_side(self):
        if self.phase != "idle":
            return None
        if self.dragging and abs(self.dx) > 25:
            return "left" if self.dx < 0 else "right"
        m = self.app.mouse
        if self.btn_left.hover(m):
            return "left"
        if self.btn_right.hover(m):
            return "right"
        return None

    # ------------------------------------------------------------------ decisões
    def pick(self, side: str):
        """Confirma a decisão. Só vale em 'idle': cliques repetidos durante a animação são ignorados."""
        if self.phase != "idle" or self.paused:
            return
        self.side = side
        self.res = self.run.choose(side)
        self.phase = "exit"
        self.t = 0.0
        self.dragging = False
        self.app.sfx.play("swipe")
        for k, v in self.res.deltas.items():
            if v:
                self.floats.append({"key": k, "text": f"{v:+d}", "color": T.GOOD if v > 0 else T.BAD, "t": 0.0})
        self.new_terms += [t for t in self.res.new_terms if t not in self.new_terms]
        self.new_selos += self.res.objectives

    def advance(self):
        if self.phase != "outcome":
            return
        self.app.sfx.play("click")
        if self.run.finished:
            from .scene_end import EndScene
            self.app.save.write()
            self.app.go(EndScene(self.app, self.run, self.new_terms, self.new_selos))
            return
        self.card = self.run.next_card()
        self.phase, self.t, self.dx = "enter", 0.0, 0.0

    # ------------------------------------------------------------------ eventos
    def handle(self, e):
        if self.paused:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self._pause(False)
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for b in self.pause_buttons:
                    if b.hover(e.pos):
                        b.click()
            return
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self._pause(True)
            elif e.key == pygame.K_m:
                self.app.save.muted = not self.app.save.muted
                self.app.sfx.muted = self.app.save.muted
            elif e.key == pygame.K_c:
                from .scene_memory import MemoryScene
                self.app.go(MemoryScene(self.app, back=self))
            elif self.phase == "idle" and e.key in (pygame.K_LEFT, pygame.K_a):
                self.pick("left")
            elif self.phase == "idle" and e.key in (pygame.K_RIGHT, pygame.K_d):
                self.pick("right")
            elif self.phase == "outcome" and e.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_RIGHT, pygame.K_KP_ENTER):
                self.advance()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.phase == "idle":
                if self.btn_left.hover(e.pos):
                    self.btn_left.click()
                elif self.btn_right.hover(e.pos):
                    self.btn_right.click()
                elif CARD_RECT.collidepoint(e.pos):
                    self.dragging, self.drag_x0 = True, e.pos[0] - self.dx
            elif self.phase == "outcome":
                self.advance()
        elif e.type == pygame.MOUSEMOTION and self.dragging:
            self.dx = max(-330, min(330, e.pos[0] - self.drag_x0))
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.dragging:
            self.dragging = False
            if abs(self.dx) >= DRAG_COMMIT:
                self.pick("left" if self.dx < 0 else "right")

    # ------------------------------------------------------------------ atualização
    def update(self, dt):
        if self.paused:
            return
        self.t += dt
        for k, v in self.run.meters.items():                       # medidores animam suavemente
            self.disp[k] += (v - self.disp[k]) * min(1.0, dt * 6)
        for f in self.floats:
            f["t"] += dt
        self.floats = [f for f in self.floats if f["t"] < 1.4]
        for b in (self.btn_left, self.btn_right, self.btn_next):
            b.update(dt)
        if self.phase == "enter" and self.t >= 0.28:
            self.phase, self.t = "idle", 0.0
        elif self.phase == "idle" and not self.dragging:
            self.dx *= max(0.0, 1 - dt * 14)                        # volta ao centro
        elif self.phase == "exit":
            target = -760 if self.side == "left" else 760
            self.dx += (target - self.dx) * min(1.0, dt * 9)
            if self.t >= 0.32:
                self.phase, self.t, self.dx = "outcome", 0.0, 0.0
                s = sum(self.res.deltas.values())
                if self.res.ended:
                    self.app.sfx.play("win" if self.app.content.endings[self.res.ended]["kind"] == "victory" else "lose")
                elif self.res.new_terms:
                    self.app.sfx.play("term")
                else:
                    self.app.sfx.play("good" if s >= 0 else "bad")

    # ------------------------------------------------------------------ desenho
    def draw(self, s):
        self._draw_meters(s)
        self._draw_left(s)
        self._draw_right(s)
        if self.phase in ("enter", "idle", "exit"):
            self._draw_card(s)
            self._draw_buttons(s)
        else:
            self._draw_outcome(s)
        self._draw_floats(s)
        self._draw_tooltip(s)
        draw.text(s, "Setas ← → ou arraste a carta  ·  C: Caderno  ·  Esc: pausa  ·  F3: depuração", 14, T.MUTED,
                  (T.W // 2, T.H - 14), anchor="midbottom")
        if self.paused:
            self._draw_pause(s)

    # ---- medidores
    def _draw_meters(self, s):
        side = self._preview_side()
        hints = self.run.hints(self.card, side) if (side and self.app.save.show_hints) else {}
        for i, (key, m) in enumerate(self.cfg["meters"].items()):
            x, y = METER_X[i], METER_Y
            val = self.disp[key]
            danger = self.run.danger(key)
            border = T.LINE if not danger else (T.BAD if danger == "low" else T.WARN)
            draw.panel(s, (x, y, 250, 92), T.PANEL, border, width=3 if danger else 2)
            col = T.METER_COLOR[key]
            pygame.draw.circle(s, col, (x + 36, y + 38), 24)
            draw.icon(s, m["icon"], x + 36, y + 38, 13, (14, 34, 46))
            draw.text(s, m["name"], 17, T.TEXT, (x + 70, y + 12), "bold")
            draw.text(s, m["sub"], 13, T.MUTED, (x + 70, y + 36))
            draw.text(s, str(int(round(val))), 20, T.TEXT, (x + 240, y + 9), "bold", "topright")
            if danger:
                draw.tri(s, danger == "high", x + 70 + 8, y + 56, 6, T.BAD if danger == "low" else T.WARN)
                draw.text(s, "baixo demais" if danger == "low" else "alto demais", 13,
                          T.BAD if danger == "low" else T.WARN, (x + 84, y + 49), "bold")
            bar = pygame.Rect(x + 14, y + 68, 222, 14)
            draw.panel(s, bar, (12, 28, 38), radius=7)
            fill = pygame.Rect(bar.x, bar.y, max(8, int(bar.w * val / 100)), bar.h)
            draw.panel(s, fill, T.BAD if danger == "low" else (T.WARN if danger == "high" else col), radius=7)
            for frac in (0.2, 0.8):                                 # zonas de perigo marcadas
                pygame.draw.line(s, T.TEXT, (bar.x + int(bar.w * frac), bar.y - 2), (bar.x + int(bar.w * frac), bar.bottom + 2), 2)
            lvl = hints.get(key)
            if lvl:
                pygame.draw.circle(s, T.WHITE, (x + 36, y + 10), 3 + lvl * 2)
                pygame.draw.circle(s, (14, 34, 46), (x + 36, y + 10), 3 + lvl * 2, 2)

    def _draw_floats(self, s):
        keys = list(self.cfg["meters"])
        for f in self.floats:
            i = keys.index(f["key"])
            a = max(0, min(255, int(255 * (1.4 - f["t"]) / 0.6)))
            img = draw.font(22, "bold").render(f["text"], True, f["color"])
            pill = pygame.Surface((img.get_width() + 16, img.get_height() + 6), pygame.SRCALPHA)
            draw.panel(pill, pill.get_rect(), (8, 20, 28), radius=10, alpha=230)
            pill.blit(img, (8, 3))
            pill.set_alpha(a)
            s.blit(pill, (METER_X[i] + 190, METER_Y + 90 + int(min(f["t"], 0.6) * 28)))   # cai para baixo do medidor

    def _draw_tooltip(self, s):
        m = self.app.mouse
        for i, key in enumerate(self.cfg["meters"]):
            r = pygame.Rect(METER_X[i], METER_Y, 250, 92)
            if r.collidepoint(m):
                lo, hi = self.tips[key]
                box = pygame.Rect(max(10, min(T.W - 330, r.x - 40)), r.bottom + 8, 320, 92)
                draw.panel(s, box, (10, 24, 32), T.SUN, alpha=245, shadow=True)
                draw.text(s, "Os DOIS extremos acabam o mandato:", 14, T.MUTED, (box.x + 12, box.y + 10))
                draw.text(s, f"Em 0:  {lo}", 16, T.BAD, (box.x + 12, box.y + 34), "bold")
                draw.text(s, f"Em 100:  {hi}", 16, T.WARN, (box.x + 12, box.y + 60), "bold")

    # ---- carta
    def _card_surface(self):
        c, run = self.card, self.run
        ch = self.app.content.characters[c["char"]]
        surf = pygame.Surface((T.CARD_W, T.CARD_H), pygame.SRCALPHA)
        draw.panel(surf, surf.get_rect(), T.PAPER, (120, 100, 70), radius=20, width=3)
        surf.blit(draw.portrait(c["char"], ch, (T.CARD_W - 24, 176)), (12, 12))
        kind = T.KIND_LABEL.get(c.get("type"), "")
        if kind:
            kw = draw.font(13, "bold").size(kind)[0] + 20
            draw.panel(surf, (22, 22, kw, 24), T.KIND_COLOR.get(c.get("type"), T.MUTED), radius=12)
            draw.text(surf, kind, 13, T.WHITE, (22 + kw // 2, 34), "bold", "center")
        draw.text(surf, ch["name"], 21, T.INK, (24, 196), "bold")
        draw.text(surf, ch["role"], 14, T.INK_SOFT, (24, 222))
        draw.paragraph(surf, run.fmt(c["text"]), 20, T.INK, (24, 250, T.CARD_W - 48, 190), gap=5)
        return surf

    def _draw_card(self, s):
        surf = self._card_surface()
        side = None
        if abs(self.dx) > 18:
            side = "left" if self.dx < 0 else "right"
        elif self.phase == "exit":
            side = self.side
        if side:                                                    # rótulo da escolha aparece ao arrastar
            a = min(1.0, abs(self.dx) / DRAG_COMMIT) if self.phase != "exit" else 1.0
            label = self.card[side]["label"]
            banner = pygame.Surface((T.CARD_W, 56), pygame.SRCALPHA)
            draw.panel(banner, banner.get_rect(), (28, 52, 68), radius=0, alpha=int(235 * a))
            f = draw.font(21, "bold").render(label, True, T.WHITE)
            f.set_alpha(int(255 * a))
            banner.blit(f, f.get_rect(center=banner.get_rect().center))
            surf.blit(banner, (0, T.CARD_H - 56))
        yoff, alpha = 0, 255
        if self.phase == "enter":
            p = min(1.0, self.t / 0.28)
            yoff, alpha = int((1 - p) * 50), int(255 * p)
        rot = -self.dx * 0.035
        img = surf if abs(rot) < 0.2 else pygame.transform.rotozoom(surf, rot, 1.0)
        img.set_alpha(alpha)
        cx = T.W // 2 + int(self.dx)
        cy = T.CARD_Y + T.CARD_H // 2 + yoff
        draw.panel(s, (cx - T.CARD_W // 2 + 4, cy - T.CARD_H // 2 + 8, T.CARD_W, T.CARD_H), (0, 0, 0), radius=20, alpha=60)
        s.blit(img, img.get_rect(center=(cx, cy)))

    def _draw_buttons(self, s):
        for b, side in ((self.btn_left, "left"), (self.btn_right, "right")):
            b.label = self.card[side]["label"]
            b.draw(s, self.app.mouse)
        draw.arrow(s, "left", CARD_L + 22, 641, 9, T.SUN)
        draw.arrow(s, "right", CARD_R + 215 - 22, 641, 9, T.SUN)

    # ---- resultado
    def _draw_outcome(self, s):
        r, c = self.res, self.card
        p = min(1.0, self.t / 0.2)
        rect = pygame.Rect(T.CARD_X, T.CARD_Y + int((1 - p) * 30), T.CARD_W, T.CARD_H)
        draw.panel(s, rect, (236, 246, 244), (70, 130, 120), radius=20, width=3, shadow=True)
        x, w = rect.x + 24, rect.w - 48
        draw.text(s, "O QUE ACONTECEU", 14, (46, 120, 104), (x, rect.y + 18), "bold")
        draw.text(s, f"Você escolheu: {r.label}", 18, T.INK, (x, rect.y + 40), "bold")
        y = draw.paragraph(s, r.outcome, 19, T.INK, (x, rect.y + 74, w, 150), gap=4)
        # variações dos medidores
        y = max(y + 6, rect.y + 190)
        chip_w = (w - 18) // 4
        for i, key in enumerate(self.cfg["meters"]):
            cx = x + i * (chip_w + 6)
            d, fl = r.deltas[key], r.flow[key]
            draw.panel(s, (cx, y, chip_w, 58), (222, 236, 234), radius=10)
            pygame.draw.circle(s, T.METER_COLOR[key], (cx + 20, y + 22), 13)
            draw.icon(s, self.cfg["meters"][key]["icon"], cx + 20, y + 22, 8, (14, 34, 46))
            col = (30, 130, 70) if d > 0 else ((190, 50, 50) if d < 0 else T.INK_SOFT)
            draw.text(s, f"{d:+d}" if d else "0", 20, col, (cx + 40, y + 10), "bold")
            fcol = (30, 130, 70) if fl > 0 else ((190, 50, 50) if fl < 0 else T.INK_SOFT)
            draw.text(s, f"fluxo {fl:+d}" if fl else "fluxo 0", 12, fcol, (cx + 8, y + 40))
        y += 68
        if self.app.save.mediator_mode and r.learn:
            g = self.app.content.glossary[r.learn]
            box = pygame.Rect(x, y, w, rect.bottom - y - 62)
            draw.panel(s, box, (252, 244, 214), (190, 150, 60), radius=10)
            tag = "NOVO NO CADERNO · " if r.new_terms else "CONCEITO · "
            draw.text(s, tag + g["title"], 14, (140, 96, 20), (box.x + 12, box.y + 8), "bold")
            draw.paragraph(s, g["text"], 15, T.INK, (box.x + 12, box.y + 30, box.w - 24, box.h - 34), gap=3)
        for o in r.objectives:
            draw.text(s, "Selo conquistado: " + next(x2["title"] for x2 in self.app.content.objectives if x2["id"] == o),
                      15, (30, 130, 70), (x, rect.bottom - 80), "bold")
        if r.ended:
            draw.text(s, "O mandato terminou.", 17, (190, 50, 50), (x, rect.bottom - 56), "bold")
        self.btn_next.label = "Ver prestação de contas" if r.ended else "Continuar"
        self.btn_next.rect.width = 300 if r.ended else 220
        self.btn_next.rect.centerx = T.W // 2
        self.btn_next.draw(s, self.app.mouse)

    # ---- painéis laterais
    def _draw_left(self, s):
        run = self.run
        rect = pygame.Rect(24, T.CARD_Y, 330, T.CARD_H)
        draw.panel(s, rect, T.PANEL, T.LINE, alpha=235)
        x, w = rect.x + 16, rect.w - 32
        draw.text(s, f"{run.mayor_t.capitalize()} {run.mayor_name}", 19, T.TEXT, (x, rect.y + 14), "bold")
        draw.text(s, f"{self.cfg['city']} · {run.mandate_no}º mandato", 14, T.MUTED, (x, rect.y + 40))
        months = min(run.month, self.cfg["mandate_months"])
        bar = pygame.Rect(x, rect.y + 68, w, 12)
        draw.panel(s, bar, (12, 28, 38), radius=6)
        draw.panel(s, (bar.x, bar.y, max(8, int(w * months / self.cfg["mandate_months"])), 12), T.SUN, radius=6)
        draw.text(s, f"Mês {months} de {self.cfg['mandate_months']}", 14, T.TEXT, (x, rect.y + 86))
        y = rect.y + 118
        pygame.draw.line(s, T.LINE, (x, y), (x + w, y))
        draw.text(s, "FLUXO A CADA DECISÃO", 13, T.SUN, (x, y + 8), "bold")
        draw.text(s, f"(passam {self.cfg['months_per_card']} meses)", 12, T.MUTED, (x + w, y + 9), anchor="topright")
        flow = run.flow_now
        cw = w // 4
        for i, key in enumerate(self.cfg["meters"]):
            v = round(flow[key])
            cx = x + i * cw
            pygame.draw.circle(s, T.METER_COLOR[key], (cx + 12, y + 44), 10)
            draw.icon(s, self.cfg["meters"][key]["icon"], cx + 12, y + 44, 6, (14, 34, 46))
            draw.text(s, f"{v:+d}" if v else "0", 17, T.GOOD if v > 0 else (T.BAD if v < 0 else T.MUTED), (cx + 28, y + 34), "bold")
        yy = y + 66
        for label, eff in run.flow_reasons():
            h = draw.paragraph_height(label, 13, w - 6, gap=2)
            if yy + h > rect.bottom - 10:
                draw.text(s, "…", 14, T.MUTED, (x, yy))
                break
            tags = "  ".join(f"{self.cfg['meters'][k]['name'][:3]} {v:+d}" for k, v in eff.items())
            draw.paragraph(s, label, 13, T.TEXT, (x, yy, w - 6, h), gap=2)
            draw.text(s, tags, 12, T.GOOD if sum(eff.values()) > 0 else T.BAD, (x, yy + h - 2), "bold")
            yy += h + 18

    def _draw_right(self, s):
        run = self.run
        rect = pygame.Rect(T.W - 24 - 330, T.CARD_Y, 330, T.CARD_H)
        draw.panel(s, rect, T.PANEL, T.LINE, alpha=235)
        x, w = rect.x + 16, rect.w - 32
        draw.text(s, "DIÁRIO DO MANDATO", 13, T.SUN, (x, rect.y + 14), "bold")
        y = rect.y + 38
        if not run.history:
            draw.paragraph(s, "Suas decisões aparecem aqui, com o conceito fiscal de cada uma.", 14, T.MUTED, (x, y, w, 60))
        for h in reversed(run.history[-5:]):
            ch = self.app.content.characters[h["char"]]["name"]
            draw.text(s, f"Mês {h['month']} · {ch}", 12, T.MUTED, (x, y))
            draw.text(s, h["label"], 15, T.TEXT, (x, y + 15), "bold")
            y += 44
        y = rect.bottom - 150
        pygame.draw.line(s, T.LINE, (x, y - 8), (x + w, y - 8))
        draw.text(s, "SELOS", 13, T.SUN, (x, y), "bold")
        for i, o in enumerate(self.app.content.objectives[:6]):
            got = o["id"] in run.obj_done
            earned = o["id"] in self.app.save.selos
            col = T.GOOD if got else (T.MUTED if earned else (70, 100, 116))
            yy = y + 22 + i * 20
            pygame.draw.circle(s, col, (x + 7, yy + 8), 6, 0 if got else 2)
            draw.text(s, o["title"], 14, T.TEXT if got else col, (x + 20, yy))

    # ---- pausa e depuração
    def _draw_pause(self, s):
        veil = pygame.Surface((T.W, T.H), pygame.SRCALPHA)
        veil.fill((4, 12, 18, 200))
        s.blit(veil, (0, 0))
        draw.text(s, "Pausa", 44, T.TEXT, (T.W // 2, 230), "bold", "center")
        draw.text(s, "Voltar ao menu descarta o mandato em andamento.", 16, T.MUTED, (T.W // 2, 272), anchor="center")
        for b in self.pause_buttons:
            b.draw(s, self.app.mouse)

    def draw_debug(self, s):
        run = self.run
        lines = [f"mês {run.month} · decisão {run.turn} · fase {self.phase}", "por que esta carta?"] + run.why[:6]
        lines += [f"flags: {', '.join(sorted(run.flags)) or '-'}",
                  f"contadores: {run.counters or '-'}", f"relações: {run.rel or '-'}",
                  f"agendadas: {[(e['card'], e['due']) for e in run.queue] or '-'}",
                  f"herança: {run.inherit or '-'}  ·  cartas vistas (permanente): {len(self.app.save.seen_cards)}"]
        box = pygame.Rect(10, T.H - 24 - 18 * len(lines) - 10, 760, 18 * len(lines) + 12)
        draw.panel(s, box, (0, 0, 0), (246, 190, 76), alpha=215, radius=8)
        for i, ln in enumerate(lines):
            draw.text(s, ln, 13, (240, 240, 200), (box.x + 8, box.y + 6 + i * 18))


CARD_L = T.W // 2 - 220
CARD_R = T.W // 2 + 5
CARD_RECT = pygame.Rect(T.CARD_X, T.CARD_Y, T.CARD_W, T.CARD_H)
