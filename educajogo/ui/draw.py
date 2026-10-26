"""Funções de desenho: fontes, texto com quebra de linha, painéis, ícones e retratos procedurais."""

from __future__ import annotations

import math
from pathlib import Path

import pygame

from . import theme as T

FONT_DIR = Path(__file__).resolve().parents[2] / "assets" / "fonts"


# --------------------------------------------------------------------------- fontes
class Fonts:
    """Fontes DejaVu embutidas em assets/fonts (cobrem acentos do português e funcionam no navegador)."""

    FILES = {"regular": "DejaVuSans.ttf", "bold": "DejaVuSans-Bold.ttf", "serif": "DejaVuSerif-Bold.ttf"}

    def __init__(self):
        self._cache: dict = {}
        self._wrap: dict = {}

    def get(self, size: int, style: str = "regular") -> pygame.font.Font:
        key = (size, style)
        if key not in self._cache:
            path = FONT_DIR / self.FILES[style]
            try:
                self._cache[key] = pygame.font.Font(str(path), size)
            except (FileNotFoundError, OSError):
                self._cache[key] = pygame.font.Font(None, int(size * 1.25))   # reserva: fonte padrão
        return self._cache[key]

    def wrap(self, font, text: str, width: int) -> list[str]:
        key = (id(font), text, width)
        hit = self._wrap.get(key)
        if hit is not None:
            return hit
        lines: list[str] = []
        for para in text.split("\n"):
            cur = ""
            for word in para.split():
                trial = f"{cur} {word}".strip()
                if font.size(trial)[0] <= width or not cur:
                    cur = trial
                else:
                    lines.append(cur)
                    cur = word
            lines.append(cur)
        if len(self._wrap) > 600:
            self._wrap.clear()
        self._wrap[key] = lines
        return lines


FONTS = Fonts()


def reset_caches():
    """Chamar depois de pygame.init(): fontes/superfícies de uma sessão anterior ficam inválidas."""
    global _BG
    FONTS._cache.clear()
    FONTS._wrap.clear()
    _PORTRAITS.clear()
    _BG = None


def font(size: int, style: str = "regular") -> pygame.font.Font:
    return FONTS.get(size, style)


# --------------------------------------------------------------------------- texto
def text(surf, s, size, color, pos, style="regular", anchor="topleft", shadow=False):
    f = font(size, style)
    img = f.render(s, True, color)
    r = img.get_rect(**{anchor: pos})
    if shadow:
        sh = f.render(s, True, (0, 0, 0))
        sh.set_alpha(120)
        surf.blit(sh, r.move(2, 2))
    surf.blit(img, r)
    return r


def fit_text(s: str, size: int, maxw: int, style: str = "regular") -> str:
    """Encurta o texto com reticências para caber em maxw pixels."""
    f = font(size, style)
    if f.size(s)[0] <= maxw:
        return s
    while s and f.size(s + "…")[0] > maxw:
        s = s[:-1]
    return s.rstrip() + "…"


def paragraph(surf, s, size, color, rect, style="regular", align="left", gap=5, max_lines=None) -> int:
    """Escreve texto com quebra de linha dentro de rect.width. Retorna o y logo abaixo."""
    rect = pygame.Rect(rect)
    f = font(size, style)
    lines = FONTS.wrap(f, s, rect.w)
    if max_lines:
        lines = lines[:max_lines]
    y = rect.y
    lh = f.get_linesize() + gap
    for line in lines:
        img = f.render(line, True, color)
        x = rect.x
        if align == "center":
            x = rect.x + (rect.w - img.get_width()) // 2
        surf.blit(img, (x, y))
        y += lh
    return y


def paragraph_height(s: str, size: int, width: int, style="regular", gap=5) -> int:
    f = font(size, style)
    return len(FONTS.wrap(f, s, width)) * (f.get_linesize() + gap)


# --------------------------------------------------------------------------- formas
def panel(surf, rect, fill, border=None, radius=14, width=2, alpha=None, shadow=False):
    rect = pygame.Rect(rect)
    if shadow:
        sh = pygame.Surface((rect.w + 24, rect.h + 24), pygame.SRCALPHA)
        for i, a in enumerate((18, 14, 10)):
            pygame.draw.rect(sh, (0, 0, 0, a), (12 - i * 4, 14 - i * 4 + 6, rect.w + i * 8, rect.h + i * 8),
                             border_radius=radius + i * 3)
        surf.blit(sh, (rect.x - 12, rect.y - 12))
    if alpha is not None:
        tmp = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(tmp, (*fill, alpha), tmp.get_rect(), border_radius=radius)
        if border:
            pygame.draw.rect(tmp, border, tmp.get_rect(), width, border_radius=radius)
        surf.blit(tmp, rect)
    else:
        pygame.draw.rect(surf, fill, rect, border_radius=radius)
        if border:
            pygame.draw.rect(surf, border, rect, width, border_radius=radius)


def gradient(size, top, bottom) -> pygame.Surface:
    s = pygame.Surface(size)
    h = size[1]
    for y in range(h):
        t = y / max(1, h - 1)
        pygame.draw.line(s, tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)), (0, y), (size[0], y))
    return s


def arrow(surf, direction, cx, cy, size, color):
    """Seta desenhada (não depende de fonte): 'left' | 'right' | 'up' | 'down'."""
    s = size
    if direction == "right":
        pts = [(cx - s, cy - s * .5), (cx + s * .1, cy - s * .5), (cx + s * .1, cy - s), (cx + s, cy),
               (cx + s * .1, cy + s), (cx + s * .1, cy + s * .5), (cx - s, cy + s * .5)]
    elif direction == "left":
        pts = [(cx + s, cy - s * .5), (cx - s * .1, cy - s * .5), (cx - s * .1, cy - s), (cx - s, cy),
               (cx - s * .1, cy + s), (cx - s * .1, cy + s * .5), (cx + s, cy + s * .5)]
    elif direction == "up":
        pts = [(cx - s * .5, cy + s), (cx - s * .5, cy - s * .1), (cx - s, cy - s * .1), (cx, cy - s),
               (cx + s, cy - s * .1), (cx + s * .5, cy - s * .1), (cx + s * .5, cy + s)]
    else:
        pts = [(cx - s * .5, cy - s), (cx - s * .5, cy + s * .1), (cx - s, cy + s * .1), (cx, cy + s),
               (cx + s, cy + s * .1), (cx + s * .5, cy + s * .1), (cx + s * .5, cy - s)]
    pygame.draw.polygon(surf, color, pts)


def tri(surf, up, cx, cy, size, color):
    if up:
        pts = [(cx - size, cy + size * .8), (cx + size, cy + size * .8), (cx, cy - size)]
    else:
        pts = [(cx - size, cy - size * .8), (cx + size, cy - size * .8), (cx, cy + size)]
    pygame.draw.polygon(surf, color, pts)


def check_mark(surf, cx, cy, size, color, width=4):
    pygame.draw.lines(surf, color, False, [(cx - size, cy), (cx - size * .3, cy + size * .7), (cx + size, cy - size * .7)], width)


def lock(surf, cx, cy, size, color):
    """Cadeado: haste em U (linhas + arco) sobre o corpo."""
    w = max(2, size // 3)
    pygame.draw.rect(surf, color, (cx - size, cy - size * .1, size * 2, size * 1.45), border_radius=3)
    pygame.draw.line(surf, color, (cx - size * .6, cy - size * .1), (cx - size * .6, cy - size * .75), w)
    pygame.draw.line(surf, color, (cx + size * .6, cy - size * .1), (cx + size * .6, cy - size * .75), w)
    pygame.draw.arc(surf, color, (cx - size * .6, cy - size * 1.4, size * 1.2, size * 1.3), 0, math.pi, w)
    pygame.draw.circle(surf, (18, 36, 48), (cx, int(cy + size * .5)), max(2, size // 4))


# --------------------------------------------------------------------------- ícones
def icon(surf, kind, cx, cy, r, color=T.WHITE):
    if kind == "coin":
        pygame.draw.circle(surf, color, (cx, cy), r, max(2, r // 5))
        pygame.draw.circle(surf, color, (cx, cy), int(r * .62), 2)
        text(surf, "$", max(10, int(r * 1.25)), color, (cx, cy + 1), "bold", "center")
    elif kind == "cross":
        t = int(r * .66)
        pygame.draw.rect(surf, color, (cx - t // 2, cy - r, t, r * 2), border_radius=3)
        pygame.draw.rect(surf, color, (cx - r, cy - t // 2, r * 2, t), border_radius=3)
    elif kind == "people":
        pygame.draw.circle(surf, color, (int(cx - r * .45), int(cy - r * .38)), int(r * .34))
        pygame.draw.circle(surf, color, (int(cx + r * .42), int(cy - r * .18)), int(r * .38))
        pygame.draw.ellipse(surf, color, (cx - r * 1.0, cy + r * .02, r * 1.0, r * 1.0))
        pygame.draw.ellipse(surf, color, (cx - r * .02, cy + r * .24, r * 1.1, r * 1.0))
    elif kind == "eye":
        pygame.draw.ellipse(surf, color, (cx - r, cy - r * .55, r * 2, r * 1.1), max(2, r // 6))
        pygame.draw.circle(surf, color, (cx, cy), int(r * .32))
    elif kind == "news":
        pygame.draw.rect(surf, color, (cx - r, cy - r * .8, r * 2, r * 1.6), 3, border_radius=3)
        for i in range(3):
            pygame.draw.line(surf, color, (cx - r * .6, cy - r * .3 + i * r * .45), (cx + r * .6, cy - r * .3 + i * r * .45), 2)


# --------------------------------------------------------------------------- retratos
_PORTRAITS: dict = {}


def portrait(char_id: str, char: dict, size: tuple[int, int]) -> pygame.Surface:
    """Retrato procedural em cache (um por personagem/tamanho)."""
    key = (char_id, size)
    if key not in _PORTRAITS:
        _PORTRAITS[key] = _draw_portrait(char, size)
    return _PORTRAITS[key]


def _draw_portrait(ch: dict, size) -> pygame.Surface:
    w, h = size
    surf = pygame.Surface(size, pygame.SRCALPHA)
    bg = pygame.Color(ch["bg"])
    surf.fill(bg)
    # luz de fundo suave (camada própria para o alfa MISTURAR com o fundo em vez de substituí-lo)
    halo = pygame.Surface(size, pygame.SRCALPHA)
    for i, a in enumerate((70, 70, 70)):
        pygame.draw.circle(halo, (255, 255, 255, a), (w // 2, int(h * .45)), int(h * (.62 - i * .13)))
    surf.blit(halo, (0, 0))

    if ch.get("kind") == "icon":                                  # cartas sem personagem: horizonte da cidade
        base = h - 26
        cols = [(120, 138, 156), (92, 112, 136), (140, 156, 174)]
        x = int(w * .12)
        for i, (bw, bh) in enumerate([(46, 96), (34, 132), (54, 78), (40, 112), (32, 64), (48, 100)]):
            pygame.draw.rect(surf, cols[i % 3], (x, base - bh, bw, bh))
            for wy in range(base - bh + 10, base - 10, 16):
                pygame.draw.rect(surf, (248, 226, 150), (x + 8, wy, 7, 8))
                pygame.draw.rect(surf, (248, 226, 150), (x + bw - 17, wy, 7, 8))
            x += bw + 8
        pygame.draw.rect(surf, (96, 122, 104), (0, base, w, 26))
        return _round(surf, 14)

    skin, hair, shirt = (pygame.Color(ch[k]) for k in ("skin", "hair", "shirt"))
    ink = (40, 30, 26)
    cx = w // 2
    hr = int(h * .21)                                              # raio da cabeça
    hy = int(h * .44)
    style = ch.get("hair_style", "short")
    if style == "long":                                            # cabelo por TRÁS do corpo
        pygame.draw.ellipse(surf, hair, (cx - int(hr * 1.2), hy - int(hr * 1.15), int(hr * 2.4), int(hr * 3.1)))
    # tronco
    pygame.draw.ellipse(surf, shirt, (cx - int(w * .30), int(h * .70), int(w * .60), int(h * .62)))
    # pescoço
    pygame.draw.rect(surf, skin.lerp((0, 0, 0), .12), (cx - int(hr * .32), hy + int(hr * .7), int(hr * .64), int(hr * .9)))
    # orelhas e cabeça
    for dx in (-1, 1):
        pygame.draw.circle(surf, skin, (cx + dx * int(hr * .98), hy + int(hr * .1)), int(hr * .22))
    pygame.draw.circle(surf, skin, (cx, hy), hr)
    # cabelo da frente
    if style in ("short", "bun", "long", "curly"):
        top = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.circle(top, hair, (cx, hy - int(hr * .05)), int(hr * 1.07))
        pygame.draw.rect(top, (0, 0, 0, 0), (0, hy - int(hr * .22), w, h))
        surf.blit(top, (0, 0))
        if style != "long":
            pygame.draw.circle(surf, hair, (cx - int(hr * .85), hy - int(hr * .2)), int(hr * .22))
            pygame.draw.circle(surf, hair, (cx + int(hr * .85), hy - int(hr * .2)), int(hr * .22))
    if style == "bun":
        pygame.draw.circle(surf, hair, (cx, hy - int(hr * 1.2)), int(hr * .42))
    if style == "curly":
        for i in range(-3, 4):
            pygame.draw.circle(surf, hair, (cx + int(i * hr * .3), hy - int(hr * .92 + abs(i) * hr * .03)), int(hr * .3))
    # rosto
    for dx in (-1, 1):
        ex = cx + dx * int(hr * .38)
        pygame.draw.ellipse(surf, (255, 255, 255), (ex - int(hr * .17), hy - int(hr * .17), int(hr * .34), int(hr * .26)))
        pygame.draw.circle(surf, ink, (ex, hy - int(hr * .04)), max(2, int(hr * .1)))
        pygame.draw.line(surf, ink, (ex - int(hr * .22), hy - int(hr * .32)), (ex + int(hr * .2), hy - int(hr * .36 + dx * 2)), 3)
    pygame.draw.arc(surf, ink, (cx - int(hr * .36), hy + int(hr * .12), int(hr * .72), int(hr * .5)), math.pi * 1.1, math.pi * 1.9, 3)
    acc = ch.get("acc", "")
    if acc == "glasses":
        for dx in (-1, 1):
            pygame.draw.circle(surf, ink, (cx + dx * int(hr * .38), hy - int(hr * .04)), int(hr * .3), 3)
        pygame.draw.line(surf, ink, (cx - int(hr * .1), hy - int(hr * .04)), (cx + int(hr * .1), hy - int(hr * .04)), 3)
    elif acc == "mustache":
        pygame.draw.ellipse(surf, (210, 210, 210), (cx - int(hr * .42), hy + int(hr * .14), int(hr * .84), int(hr * .22)))
    elif acc == "tie":
        pygame.draw.polygon(surf, (190, 52, 52), [(cx - 9, int(h * .78)), (cx + 9, int(h * .78)), (cx + 13, int(h * .98)), (cx, h), (cx - 13, int(h * .98))])
    elif acc == "apron":
        pygame.draw.polygon(surf, (252, 250, 244), [(cx - int(w * .17), h), (cx + int(w * .17), h), (cx + int(w * .12), int(h * .78)), (cx - int(w * .12), int(h * .78))])
    elif acc == "headphones":
        pygame.draw.arc(surf, (30, 30, 36), (cx - int(hr * 1.22), hy - int(hr * 1.3), int(hr * 2.44), int(hr * 2.3)), 0, math.pi, 6)
        for dx in (-1, 1):
            pygame.draw.circle(surf, (30, 30, 36), (cx + dx * int(hr * 1.16), hy + int(hr * .05)), int(hr * .3))
    elif acc == "hardhat":
        pygame.draw.ellipse(surf, (240, 190, 40), (cx - int(hr * 1.1), hy - int(hr * 1.15), int(hr * 2.2), int(hr * 1.3)))
        pygame.draw.rect(surf, (240, 190, 40), (cx - int(hr * 1.3), hy - int(hr * .38), int(hr * 2.6), int(hr * .2)), border_radius=4)
    elif acc == "coat":
        pygame.draw.polygon(surf, (250, 250, 250), [(cx - int(w * .28), h), (cx - int(hr * .6), int(h * .74)), (cx, int(h * .9)), (cx + int(hr * .6), int(h * .74)), (cx + int(w * .28), h)])
        pygame.draw.line(surf, (70, 140, 130), (cx - int(hr * .5), int(h * .82)), (cx + int(hr * .5), int(h * .9)), 4)
    elif acc == "book":
        pygame.draw.rect(surf, (150, 80, 60), (cx + int(w * .12), int(h * .8), int(w * .22), int(h * .18)), border_radius=3)
        pygame.draw.rect(surf, (250, 240, 220), (cx + int(w * .13), int(h * .81), int(w * .2), int(h * .03)))
    elif acc == "badge":
        pygame.draw.rect(surf, (250, 250, 250), (cx + int(w * .1), int(h * .8), int(w * .14), int(h * .1)), border_radius=3)
        pygame.draw.rect(surf, (70, 130, 200), (cx + int(w * .1), int(h * .8), int(w * .14), int(h * .03)))
    elif acc == "scarf":
        pygame.draw.ellipse(surf, (224, 96, 70), (cx - int(hr * .85), hy + int(hr * .85), int(hr * 1.7), int(hr * .6)))
    return _round(surf, 14)


def _round(surf: pygame.Surface, radius: int) -> pygame.Surface:
    mask = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
    out = surf.copy()
    out.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return out


# --------------------------------------------------------------------------- cenário
_BG: pygame.Surface | None = None


def background() -> pygame.Surface:
    """Amanhecer sobre a cidade de Novaluz (gerado uma vez e reaproveitado)."""
    global _BG
    if _BG is None:
        s = gradient((T.W, T.H), T.BG_TOP, T.BG_BOTTOM)
        # sol nascente atrás do horizonte
        sun = pygame.Surface((T.W, T.H), pygame.SRCALPHA)
        for r, a in ((330, 10), (250, 14), (180, 20), (120, 34)):
            pygame.draw.circle(sun, (*T.SUN, a), (T.W // 2, T.H - 70), r)
        s.blit(sun, (0, 0))
        # silhueta de prédios
        rnd = [(46, 96), (34, 140), (60, 80), (40, 170), (52, 110), (30, 150), (64, 90), (44, 130)]
        base = T.H
        x = -10
        i = 0
        while x < T.W:
            bw, bh = rnd[i % len(rnd)]
            col = (14 + (i % 3) * 3, 36 + (i % 3) * 3, 48 + (i % 3) * 3)
            pygame.draw.rect(s, col, (x, base - bh // 2 - 40, bw, bh))
            x += bw + 4
            i += 1
        _BG = s
    return _BG
