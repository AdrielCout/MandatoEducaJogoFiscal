"""Menu inicial: jogar, Caderno, como jogar e opções do mediador."""

from __future__ import annotations

import pygame

from . import draw, theme as T
from .widgets import Button


class MenuScene:
    def __init__(self, app):
        self.app = app
        self.show_help = False
        self.confirm_reset = 0.0
        self.t = 0.0
        sv = app.save
        self.main = [
            Button((70, 330, 360, 58), "Jogar", self.play, key="Enter", size=26, accent=T.SUN),
            Button((70, 402, 360, 52), "Caderno e memória da cidade", self.memory, key="C", size=19),
            Button((70, 468, 360, 52), "Como jogar", lambda: self._help(True), key="H", size=19),
        ]
        self.opts = [
            Button((500, 330, 330, 52), "", self.toggle_mediator, size=17),
            Button((500, 392, 330, 52), "", self.toggle_hints, size=17),
            Button((500, 454, 330, 52), "", self.toggle_sound, size=17),
            Button((500, 516, 330, 52), "", self.reset, size=17, accent=T.BAD),
            Button((500, 578, 330, 52), "Sair", app.quit, size=17),
        ]
        self._sync_labels()

    # ---- ações
    def play(self):
        from .scene_game import GameScene
        self.app.sfx.play("click")
        self.app.go(GameScene(self.app))

    def memory(self):
        from .scene_memory import MemoryScene
        self.app.sfx.play("click")
        self.app.go(MemoryScene(self.app))

    def _help(self, v):
        self.show_help = v
        self.app.sfx.play("click")

    def toggle_mediator(self):
        self.app.save.mediator_mode = not self.app.save.mediator_mode
        self._after()

    def toggle_hints(self):
        self.app.save.show_hints = not self.app.save.show_hints
        self._after()

    def toggle_sound(self):
        self.app.save.muted = not self.app.save.muted
        self.app.sfx.muted = self.app.save.muted
        self._after()

    def reset(self):
        if self.confirm_reset > 0:
            self.app.save.reset()
            self.confirm_reset = 0
        else:
            self.confirm_reset = 3.0
        self._after()

    def _after(self):
        self.app.save.write()
        self.app.sfx.play("click")
        self._sync_labels()

    def _sync_labels(self):
        sv = self.app.save
        o = self.opts
        o[0].label, o[0].sub = f"Modo mediador: {'LIGADO' if sv.mediator_mode else 'desligado'}", "mostra o conceito fiscal após cada escolha"
        o[1].label, o[1].sub = f"Dicas de impacto: {'LIGADAS' if sv.show_hints else 'desligadas'}", "pontos sobre os medidores ao arrastar"
        o[2].label, o[2].sub = f"Som: {'desligado' if sv.muted else 'LIGADO'}", "efeitos sonoros"
        o[3].label = "Clique de novo para APAGAR" if self.confirm_reset > 0 else "Apagar progresso salvo"
        o[3].sub = "zera Caderno, finais e mandatos" if self.confirm_reset <= 0 else "esta ação não pode ser desfeita"

    # ---- ciclo
    def handle(self, e):
        if self.show_help:
            if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self._help(False)
            return
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.play()
            elif e.key == pygame.K_c:
                self.memory()
            elif e.key == pygame.K_h:
                self._help(True)
            elif e.key == pygame.K_ESCAPE:
                self.app.quit()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for b in self.main + self.opts:
                if b.hover(e.pos):
                    b.click()
                    break

    def update(self, dt):
        self.t += dt
        if self.confirm_reset > 0:
            self.confirm_reset -= dt
            if self.confirm_reset <= 0:
                self._sync_labels()
        for b in self.main + self.opts:
            b.update(dt)

    def draw(self, s):
        import math
        sv, ct = self.app.save, self.app.content
        draw.text(s, "MANDATO", 84, T.TEXT, (70, 62), "serif", shadow=True)
        draw.text(s, "Contas da Cidade", 30, T.SUN, (74, 160), "bold")
        draw.paragraph(s, "Você é o prefeito de Novaluz. Quem paga, para onde vai e quem fiscaliza? "
                          "Decida em 48 meses e preste contas.", 18, T.MUTED, (74, 212, 400, 80), gap=5)
        draw.text(s, "EducaJogo Fiscal · Educação Fiscal para o Ensino Médio", 14, T.MUTED, (74, 292))
        for b in self.main + self.opts:
            b.draw(s, self.app.mouse)
        # carta decorativa balançando
        ch = ct.characters["tadeu"]
        card = pygame.Surface((300, 380), pygame.SRCALPHA)
        draw.panel(card, card.get_rect(), T.PAPER, (120, 100, 70), radius=18, width=3)
        card.blit(draw.portrait("tadeu", ch, (276, 190)), (12, 12))
        draw.text(card, ch["name"], 20, T.INK, (20, 214), "bold")
        draw.paragraph(card, "Bom dia! Nenhum medidor pode zerar nem lotar. Dinheiro parado também derruba o mandato.", 16, T.INK,
                       (20, 246, 260, 120), gap=4)
        img = pygame.transform.rotozoom(card, 6 * math.sin(self.t * 1.2), 1.0)
        s.blit(img, img.get_rect(center=(1030, 330)))
        # progresso
        info = (f"Mandatos: {sv.mandates}   ·   Caderno: {len(sv.glossary)}/{len(ct.glossary)}   ·   "
                f"Finais vistos: {len(sv.endings)}/{len(ct.endings)}   ·   Selos: {len(sv.selos)}/{len(ct.objectives)}")
        draw.text(s, info, 15, T.MUTED, (70, 664))
        if self.show_help:
            self._draw_help(s)

    def _draw_help(self, s):
        veil = pygame.Surface((T.W, T.H), pygame.SRCALPHA)
        veil.fill((4, 12, 18, 225))
        s.blit(veil, (0, 0))
        box = pygame.Rect(190, 90, 900, 540)
        draw.panel(s, box, T.PANEL, T.SUN, width=3, shadow=True)
        draw.text(s, "Como jogar", 34, T.TEXT, (box.x + 36, box.y + 26), "serif")
        steps = [
            ("Decida", "Cada carta traz um pedido ou problema. Arraste para a esquerda ou direita (ou use as setas) para escolher."),
            ("Equilibre", "Quatro medidores: Povo, Serviços, Cofre e Transparência. Zerar OU lotar qualquer um derruba o mandato."),
            ("Não existe resposta certa", "Toda escolha ajuda algo e custa outra coisa. Os pontos nos medidores mostram QUAIS mudam, não se sobem ou descem."),
            ("Veja o fluxo", "O painel da esquerda mostra receitas e despesas que se repetem a cada decisão. Gasto permanente pesa por anos."),
            ("Aprenda e herde", "Cada decisão rende um conceito de Educação Fiscal no Caderno. Se o mandato cair, o próximo prefeito herda as consequências."),
        ]
        y = box.y + 90
        for i, (h, t) in enumerate(steps):
            pygame.draw.circle(s, T.SUN, (box.x + 52, y + 18), 18)
            draw.text(s, str(i + 1), 20, (20, 30, 40), (box.x + 52, y + 18), "bold", "center")
            draw.text(s, h, 20, T.TEXT, (box.x + 90, y), "bold")
            y = draw.paragraph(s, t, 16, T.MUTED, (box.x + 90, y + 26, box.w - 130, 60), gap=3) + 14
        draw.text(s, "Clique ou aperte qualquer tecla para fechar", 14, T.SUN, (box.centerx, box.bottom - 24), anchor="center")

    def draw_debug(self, s):
        pass
