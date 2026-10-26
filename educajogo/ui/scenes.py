"""Cenas do jogo: menu, partida, prestação de contas, Caderno e histórico.

Cada cena recebe `app` e não conhece o motor por dentro: pede ações (decide, proceed)
e lê o estado de `Run` para desenhar. A regra do jogo fica toda em core/.
"""

from __future__ import annotations

import random

import pygame

from ..core.engine import Run
from . import draw
from . import theme as T
from .widgets import Button, Scroller

CY = 146            # topo da carta
MAX_DRAG = 120      # arrasto (em pixels) necessário para decidir


def dots(n: int) -> str:
    return "●" * n


class Scene:
    def __init__(self, app):
        self.app = app
        self.buttons: list[Button] = []

    # entrada ---------------------------------------------------------------
    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            self.key(e.key)
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            for b in self.buttons:
                if b.hover(e.pos):
                    b.click()
                    break

    def key(self, k):
        pass

    # quadro ----------------------------------------------------------------
    def update(self, dt):
        for b in self.buttons:
            b.update(dt)

    def draw(self, surf):
        pass

    def draw_debug(self, surf):
        pass

    def mname(self, k: str) -> str:
        return self.app.content.config["meters"][k]["name"]


# ============================================================================ menu
class MenuScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        s = app.save
        cx = T.W // 2
        self.buttons = [
            Button((cx - 220, 344, 440, 58), "Começar mandato", self.start, key="Enter", accent=T.SUN, size=24),
            Button((cx - 220, 416, 440, 52), "Caderno de Cidadania", self.glossary, key="C"),
            Button((cx - 220, 480, 440, 52), "Histórico de mandatos", self.history, key="H"),
            Button((cx - 220, 544, 214, 48), f"Mediador: {'sim' if s.mediator_mode else 'não'}",
                   self.toggle_mediator, key="M", size=18),
            Button((cx + 6, 544, 214, 48), f"Som: {'não' if s.muted else 'sim'}", self.toggle_sound, key="S", size=18),
            Button((cx - 220, 606, 440, 44), "Sair", app.quit, key="Esc", size=18),
        ]

    def start(self):
        run = Run(self.app.content, self.app.save, random.Random())
        self.app.go(GameScene(self.app, run))

    def glossary(self):
        self.app.go(GlossaryScene(self.app))

    def history(self):
        self.app.go(HistoryScene(self.app))

    def toggle_mediator(self):
        self.app.save.mediator_mode = not self.app.save.mediator_mode
        self.app.save.write()
        self.app.go(MenuScene(self.app))

    def toggle_sound(self):
        self.app.save.muted = not self.app.save.muted
        self.app.sfx.muted = self.app.save.muted
        self.app.save.write()
        self.app.go(MenuScene(self.app))

    def key(self, k):
        atalhos = {
            pygame.K_RETURN: self.start, pygame.K_KP_ENTER: self.start, pygame.K_c: self.glossary,
            pygame.K_h: self.history, pygame.K_m: self.toggle_mediator, pygame.K_s: self.toggle_sound,
            pygame.K_ESCAPE: self.app.quit,
        }
        f = atalhos.get(k)
        if f:
            f()

    def draw(self, surf):
        c, s = self.app.content, self.app.save
        cx = T.W // 2
        draw.text(surf, "MANDATO", 88, T.SUN, (cx, 118), "serif", "center", shadow=True)
        draw.text(surf, c.config["subtitle"], 26, T.TEXT, (cx, 208), "bold", "center")
        draw.paragraph(surf, "Governe Novaluz com os tributos da população. Cada decisão tem um custo, "
                       "e os dois extremos de cada força derrubam o mandato.",
                       19, T.MUTED, (cx - 400, 246, 800, 0), align="center")
        prog = (f"Selos {len(s.selos)}/{len(c.objectives)}   ·   Finais vistos {len(s.endings)}/{len(c.endings_list)}"
                f"   ·   Verbetes {len(s.glossary)}/{len(c.glossary)}")
        draw.text(surf, prog, 18, T.MUTED, (cx, 318), "regular", "center")
        for b in self.buttons:
            b.draw(surf, self.app.mouse)


# ============================================================================ partida
class GameScene(Scene):
    def __init__(self, app, run: Run):
        super().__init__(app)
        self.run = run
        self.shown = dict(run.meters)          # valores exibidos (animados até o valor real)
        self.result = None                     # Result da última decisão (painel de consequência)
        self.card = None
        self.dragging = False
        self.start_x = 0
        self.drag = 0.0
        self.anim = 0.0
        self.cont = Button((T.W // 2 - 150, 606, 300, 52), "Continuar", self.proceed, key="Enter",
                           accent=T.SUN, size=22)
        self.new_card()

    # ações ------------------------------------------------------------------
    def new_card(self):
        self.card = self.run.next_card()
        self.anim = self.drag = 0.0
        self.dragging = False
        self.buttons = [self._choice("left", 150), self._choice("right", 710)]

    def _choice(self, side: str, x: int) -> Button:
        opt = self.card[side]
        hints = self.run.hints(self.card, side)
        sub = "   ".join(f"{self.mname(k)} {dots(v)}" for k, v in hints.items()) or "sem efeito visível"
        return Button((x, 622, 420, 66), opt["label"], lambda s=side: self.decide(s),
                      key="←" if side == "left" else "→", size=22, sub=sub)

    def decide(self, side: str):
        if self.result is not None or self.run.finished or self.card is None:
            return                              # clique duplo ou animação: a decisão conta uma vez só
        self.result = self.run.choose(side)
        self.dragging = False
        self.app.sfx.play("stamp")

    def proceed(self):
        if self.result is None:
            return
        res, self.result = self.result, None
        if res.ended:
            self.app.save.write()
            self.app.go(EndScene(self.app, self.run))
            return
        self.new_card()

    # entrada ----------------------------------------------------------------
    def card_rect(self) -> pygame.Rect:
        return pygame.Rect(T.CARD_X + round(self.drag), CY + round((1 - self.anim) * 24), T.CARD_W, T.CARD_H)

    def handle(self, e):
        if self.result is not None:
            if e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.cont.rect.collidepoint(e.pos):
                self.proceed()
            elif e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.proceed()
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.card_rect().collidepoint(e.pos):
            self.dragging = True
            self.start_x = e.pos[0]
        elif e.type == pygame.MOUSEMOTION and self.dragging:
            self.drag = e.pos[0] - self.start_x
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.dragging:
            self.dragging = False
            if abs(self.drag) > MAX_DRAG:
                self.decide("left" if self.drag < 0 else "right")
            return                              # soltar o arrasto nunca clica em botão por acidente
        super().handle(e)

    def key(self, k):
        if k in (pygame.K_LEFT, pygame.K_a):
            self.decide("left")
        elif k in (pygame.K_RIGHT, pygame.K_d):
            self.decide("right")

    # quadro -----------------------------------------------------------------
    def update(self, dt):
        super().update(dt)
        self.anim = min(1.0, self.anim + dt * 3.5)
        if not self.dragging:
            self.drag += (0 - self.drag) * min(1.0, dt * 14)
        for k, v in self.run.meters.items():
            self.shown[k] += (v - self.shown[k]) * min(1.0, dt * 5)

    def draw(self, surf):
        self._top(surf)
        self._card(surf)
        if self.result is None:
            for b in self.buttons:
                b.draw(surf, self.app.mouse)
            draw.text(surf, "Arraste a carta, use ← → ou os botões.   ● = quanto o medidor mexe "
                      "(a direção fica escondida de propósito).", 15, T.MUTED, (T.W // 2, 698), "regular", "center")
        else:
            self._result(surf)

    def _top(self, surf):
        run, cfg = self.run, self.app.content.config
        draw.panel(surf, (20, 12, T.W - 40, 92), T.PANEL, border=T.LINE, radius=14)
        colw, gap = 288, 12
        for i, (k, m) in enumerate(cfg["meters"].items()):
            x, y = 36 + i * (colw + gap), 22
            col = T.METER_COLOR.get(k, T.TEXT)
            draw.icon(surf, m["icon"], x + 12, y + 12, 12, col)
            draw.text(surf, m["name"], 19, T.TEXT, (x + 32, y), "bold")
            draw.text(surf, str(round(self.shown[k])), 19, col, (x + colw, y), "bold", "topright")
            draw.panel(surf, (x, y + 34, colw, 14), T.PANEL_2, radius=7)
            fw = int(colw * max(0.0, min(100.0, self.shown[k])) / 100)
            if fw > 0:
                draw.panel(surf, (x, y + 34, max(8, fw), 14), col, radius=7)
            for lim in (cfg.get("danger_low", 20), cfg.get("danger_high", 80)):
                mx = x + int(colw * lim / 100)
                pygame.draw.line(surf, T.WHITE, (mx, y + 30), (mx, y + 52), 2)
            danger = run.danger(k)
            if danger:
                msg = "perigo: falta" if danger == "low" else "perigo: excesso"
                draw.text(surf, msg, 14, T.BAD, (x, y + 54), "bold")
        draw.text(surf, f"{run.mayor_name} · mês {run.month} de {cfg['mandate_months']}", 20, T.TEXT, (36, 114), "bold")
        draw.panel(surf, (760, 122, 480, 8), T.PANEL_2, radius=4)
        draw.panel(surf, (760, 122, max(8, int(480 * min(1, run.month / cfg["mandate_months"]))), 8), T.SUN, radius=4)

    def _card(self, surf):
        if self.card is None or self.result is not None:
            return
        c = self.card
        ch = self.app.content.characters[c["char"]]
        r = self.card_rect()
        draw.panel(surf, r, T.PAPER, radius=20, shadow=True)
        surf.blit(draw.portrait(c["char"], ch, (r.w - 32, 170)), (r.x + 16, r.y + 16))
        kind = c.get("type", "evento")
        label = T.KIND_LABEL.get(kind, kind.upper())
        tw = draw.font(14, "bold").size(label)[0] + 18
        tag = pygame.Rect(r.x + 26, r.y + 26, tw, 24)
        draw.panel(surf, tag, T.KIND_COLOR.get(kind, T.PANEL_2), radius=8)
        draw.text(surf, label, 14, T.WHITE, tag.center, "bold", "center")
        draw.text(surf, ch["name"], 21, T.INK, (r.x + 22, r.y + 196), "bold")
        draw.text(surf, ch.get("role", ""), 16, T.INK_SOFT, (r.x + 22, r.y + 222))
        draw.paragraph(surf, self.run.fmt(c["text"]), 22, T.INK, (r.x + 22, r.y + 252, r.w - 44, 0), gap=6)
        if c.get("story"):
            draw.text(surf, f"História: {c['story']}", 15, T.INK_SOFT, (r.x + 22, r.bottom - 28))
        if abs(self.drag) > 30:                  # indica para qual lado a carta está indo
            side = "left" if self.drag < 0 else "right"
            txt = c[side]["label"]
            pw = draw.font(22, "bold").size(txt)[0] + 30
            pill = pygame.Rect(0, 0, pw, 40)
            pill.center = (r.centerx, r.y + 96)
            draw.panel(surf, pill, T.WARN, radius=12)
            draw.text(surf, txt, 22, T.INK, pill.center, "bold", "center")

    def _result(self, surf):
        res, content = self.result, self.app.content
        rect = pygame.Rect(200, 146, 880, 512)
        draw.panel(surf, rect, T.PAPER, radius=20, shadow=True)
        x, w = rect.x + 28, rect.w - 56
        y = rect.y + 22
        draw.text(surf, "Consequência da sua escolha", 16, T.INK_SOFT, (x, y), "bold")
        y += 24
        draw.text(surf, res.label, 26, T.INK, (x, y), "serif")
        y += 42
        y = draw.paragraph(surf, res.outcome, 20, T.INK, (x, y, w, 0), gap=6) + 8
        chip_x = x
        for k, v in res.deltas.items():
            if v == 0:
                continue
            txt = f"{self.mname(k)} {v:+d}"
            cw = draw.font(18, "bold").size(txt)[0] + 20
            chip = pygame.Rect(chip_x, y, cw, 28)
            draw.panel(surf, chip, T.METER_COLOR[k], radius=8)
            draw.text(surf, txt, 18, T.INK, chip.center, "bold", "center")
            chip_x += cw + 10
        y += 36
        flows = [f"{self.mname(k)} {v:+d}" for k, v in res.flow.items() if v]
        if flows:
            draw.text(surf, "Fluxo do mês: " + ", ".join(flows), 17, T.INK_SOFT, (x, y))
            y += 28
        if self.app.save.mediator_mode and res.learn in content.glossary:
            term = content.glossary[res.learn]
            body_h = draw.paragraph_height(term["text"], 18, w - 32, gap=4)
            box = pygame.Rect(x, y + 4, w, body_h + 56)
            draw.panel(surf, box, T.PANEL, radius=14)
            draw.text(surf, f"Conceito: {term['title']}", 18, T.SUN, (box.x + 16, box.y + 12), "bold")
            if res.new_terms:
                draw.text(surf, "novo no Caderno", 14, T.TEXT, (box.right - 16, box.y + 14), "regular", "topright")
            draw.paragraph(surf, term["text"], 18, T.TEXT, (box.x + 16, box.y + 40, w - 32, 0), gap=4)
            y = box.bottom + 10
        for oid in res.objectives:
            title = next((o["title"] for o in content.objectives if o["id"] == oid), oid)
            draw.text(surf, f"Selo conquistado: {title}", 20, T.INK, (x, y), "bold")
            y += 30
        self.cont.rect = pygame.Rect(rect.centerx - 150, rect.bottom - 66, 300, 52)
        self.cont.draw(surf, self.app.mouse)

    def draw_debug(self, surf):
        lines = ["DEPURAÇÃO (F3)", f"carta: {self.card['id'] if self.card else '-'}",
                 f"mês {self.run.month} · decisão nº {self.run.turn}"]
        lines += [f"{k}: {v:.0f}" for k, v in self.run.meters.items()]
        lines += [w[:60] for w in self.run.why[:14]]
        h = 22 * len(lines) + 20
        draw.panel(surf, (884, 140, 380, h), (10, 20, 28), border=T.LINE, radius=10, alpha=235)
        for i, line in enumerate(lines):
            draw.text(surf, line, 15, T.TEXT, (898, 152 + i * 22))


# ============================================================================ fim
class EndScene(Scene):
    ROW = 26

    def __init__(self, app, run: Run):
        super().__init__(app)
        self.run = run
        self.sm = run.summary()
        self.e = self.sm["ending"]
        self.tone = T.END_COLOR.get(self.e.get("tone", "mid"), T.WARN)
        chars = app.content.characters
        self.rows = [f"Mês {h['month']:>2} · {chars.get(h['char'], {}).get('name', h['char'])}: {h['label']}"
                     for h in self.sm["history"]]
        self.scroll = Scroller(pygame.Rect(656, 370, 560, 236), content_h=len(self.rows) * self.ROW, step=self.ROW)
        cx = T.W // 2
        self.buttons = [
            Button((cx - 310, 626, 300, 56), "Próximo mandato", self.next_mandate, key="Enter", accent=T.SUN, size=21),
            Button((cx + 10, 626, 300, 56), "Menu", self.menu, key="Esc", size=21),
        ]
        app.sfx.play("win" if self.e.get("kind") == "victory" else "lose")

    def next_mandate(self):
        self.app.save.write()
        run = Run(self.app.content, self.app.save, random.Random())
        self.app.go(GameScene(self.app, run))

    def menu(self):
        self.app.save.write()
        self.app.go(MenuScene(self.app))

    def key(self, k):
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.next_mandate()
        elif k == pygame.K_ESCAPE:
            self.menu()

    def handle(self, e):
        if e.type == pygame.MOUSEWHEEL:
            self.scroll.wheel(e.y)
        super().handle(e)

    def draw(self, surf):
        c, sm, e = self.app.content, self.sm, self.e
        head = pygame.Rect(40, 110, 1200, 110)
        draw.panel(surf, head, T.PANEL, border=T.LINE, radius=16)
        draw.panel(surf, (head.x, head.y + 12, 8, head.h - 24), self.tone, radius=4)
        draw.text(surf, e["title"], 40, self.tone, (70, 124), "serif")
        draw.text(surf, e.get("cause", ""), 20, T.TEXT, (70, 180))
        draw.text(surf, f"{self.run.mayor_name}  ·  {sm['months']} meses  ·  {sm['decisions']} decisões",
                  20, T.MUTED, (1210, 128), "regular", "topright")

        # esquerda: o que aconteceu e o conceito
        r = pygame.Rect(40, 236, 580, 376)
        draw.panel(surf, r, T.PANEL, border=T.LINE, radius=16)
        x, w = r.x + 22, r.w - 44
        y = draw.paragraph(surf, self.run.fmt(e.get("text", "")), 19, T.TEXT, (x, r.y + 18, w, 0), gap=5) + 8
        draw.text(surf, "Conceito", 18, T.SUN, (x, y), "bold")
        y = draw.paragraph(surf, e.get("concept", ""), 17, T.TEXT, (x, y + 26, w, 0), gap=4) + 10
        draw.text(surf, "Para conversar", 18, T.SUN, (x, y), "bold")
        y += 26
        for q in e.get("discuss", []):
            y = draw.paragraph(surf, "• " + q, 17, T.MUTED, (x, y, w, 0), gap=3) + 4

        # direita: prestação de contas e linha do tempo
        r2 = pygame.Rect(640, 236, 600, 376)
        draw.panel(surf, r2, T.PANEL, border=T.LINE, radius=16)
        x2, y2 = r2.x + 20, r2.y + 16
        draw.text(surf, "Prestação de contas", 22, T.SUN, (x2, y2), "serif")
        y2 += 34
        titles = {o["id"]: o["title"] for o in c.objectives}
        draw.text(surf, f"Selos neste mandato: {len(sm['objectives'])}   ·   "
                  f"Conceitos aprendidos: {len(sm['learned'])}", 17, T.TEXT, (x2, y2))
        y2 += 26
        draw.text(surf, "  ·  ".join(f"{self.mname(k)} {v}" for k, v in sm["meters"].items()), 17, T.TEXT, (x2, y2))
        y2 += 30
        draw.text(surf, "Decisões do mandato", 18, T.SUN, (x2, y2), "bold")
        area = self.scroll.area
        surf.set_clip(area)
        for i, row in enumerate(self.rows):
            ry = area.y + i * self.ROW - self.scroll.y
            if ry + self.ROW < area.y or ry > area.bottom:
                continue
            draw.text(surf, row, 17, T.TEXT, (area.x + 4, ry + 3))
        surf.set_clip(None)
        self.scroll.draw_bar(surf)
        for b in self.buttons:
            b.draw(surf, self.app.mouse)


# ============================================================================ Caderno
class GlossaryScene(Scene):
    ROW = 36

    def __init__(self, app):
        super().__init__(app)
        self.keys = list(app.content.glossary.keys())
        self.sel = 0
        self.area = pygame.Rect(40, 150, 400, 500)
        self.scroll = Scroller(self.area, content_h=len(self.keys) * self.ROW, step=self.ROW)
        self.buttons = [Button((40, 662, 220, 48), "Voltar", self.back, key="Esc", size=20)]

    def back(self):
        self.app.go(MenuScene(self.app))

    def move(self, d: int):
        self.sel = max(0, min(len(self.keys) - 1, self.sel + d))
        y = self.sel * self.ROW
        if y < self.scroll.y:
            self.scroll.to(y)
        elif y + self.ROW > self.scroll.y + self.area.h:
            self.scroll.to(y + self.ROW - self.area.h)

    def key(self, k):
        if k == pygame.K_ESCAPE:
            self.back()
        elif k == pygame.K_DOWN:
            self.move(1)
        elif k == pygame.K_UP:
            self.move(-1)

    def handle(self, e):
        if e.type == pygame.MOUSEWHEEL:
            self.scroll.wheel(e.y)
            return
        if e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.area.collidepoint(e.pos):
            i = (e.pos[1] - self.area.y + self.scroll.y) // self.ROW
            if 0 <= i < len(self.keys):
                self.sel = i
            return
        super().handle(e)

    def draw(self, surf):
        g, s = self.app.content.glossary, self.app.save
        draw.text(surf, "Caderno de Cidadania", 34, T.SUN, (40, 84), "serif")
        draw.text(surf, f"{len(s.glossary)}/{len(g)} verbetes descobertos", 18, T.MUTED, (40, 122))
        draw.panel(surf, (30, 144, 420, 512), T.PANEL, radius=14)
        surf.set_clip(self.area)
        for i, k in enumerate(self.keys):
            y = self.area.y + i * self.ROW - self.scroll.y
            if y + self.ROW < self.area.y or y > self.area.bottom:
                continue
            row = pygame.Rect(self.area.x, y, self.area.w, self.ROW - 4)
            if i == self.sel:
                draw.panel(surf, row, T.PANEL_2, radius=8)
            ok = k in s.glossary
            title = g[k]["title"] if ok else "???"
            f = draw.font(17, "bold" if ok else "regular")
            while f.size(title)[0] > row.w - 24 and len(title) > 4:
                title = title[:-2].rstrip() + "…"
            draw.text(surf, title, 17, T.TEXT if ok else T.MUTED,
                      (row.x + 12, row.centery), "bold" if ok else "regular", "midleft")
        surf.set_clip(None)
        self.scroll.draw_bar(surf)

        panel = pygame.Rect(490, 144, 750, 512)
        draw.panel(surf, panel, T.PAPER, radius=16)
        k = self.keys[self.sel]
        if k in s.glossary:
            t = g[k]
            draw.text(surf, t["title"], 30, T.INK, (520, 170), "serif")
            draw.text(surf, t.get("topic", ""), 18, T.INK_SOFT, (520, 210))
            draw.paragraph(surf, t["text"], 22, T.INK, (520, 252, 690, 0), gap=8)
        else:
            draw.text(surf, "Jogue um mandato para descobrir este verbete.", 20, T.INK_SOFT, (520, 172))
        for b in self.buttons:
            b.draw(surf, self.app.mouse)


# ============================================================================ histórico
class HistoryScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.rows = list(reversed(app.save.history))[:10]
        self.buttons = [Button((40, 662, 220, 48), "Voltar", self.back, key="Esc", size=20)]

    def back(self):
        self.app.go(MenuScene(self.app))

    def key(self, k):
        if k == pygame.K_ESCAPE:
            self.back()

    def draw(self, surf):
        draw.text(surf, "Histórico de mandatos", 34, T.SUN, (40, 96), "serif")
        if not self.rows:
            draw.text(surf, "Nenhum mandato concluído ainda. Comece um e a história fica registrada aqui.",
                      20, T.TEXT, (40, 170))
        endings = self.app.content.endings
        for i, h in enumerate(self.rows):
            y = 150 + i * 46
            row = pygame.Rect(40, y, 1200, 40)
            draw.panel(surf, row, T.PANEL, border=T.LINE, radius=10)
            title = endings.get(h["ending"], {}).get("title", h["ending"])
            draw.text(surf, f"Mandato {h['n']}  ·  {h['mayor']}  ·  {title}", 19, T.TEXT, (56, y + 20),
                      "bold", "midleft")
            draw.text(surf, f"{h['months']} meses  ·  {h['decisions']} decisões", 17, T.MUTED,
                      (1224, y + 20), "regular", "midright")
        for b in self.buttons:
            b.draw(surf, self.app.mouse)
