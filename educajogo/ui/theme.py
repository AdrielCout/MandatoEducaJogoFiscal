"""Constantes visuais. Toda a arte do jogo é gerada por código (sem imagens externas):
projeto leve, sem direitos autorais de terceiros e fácil de rodar em qualquer computador."""

W, H = 1280, 720
FPS = 60

# Identidade: "amanhecer em Novaluz" — azul-petróleo noturno, sol dourado, papel de prefeitura.
BG_TOP = (16, 38, 52)
BG_BOTTOM = (10, 24, 34)
SUN = (244, 190, 90)
PANEL = (24, 52, 68)
PANEL_2 = (32, 66, 86)
LINE = (62, 104, 126)
PAPER = (246, 238, 218)
PAPER_2 = (232, 220, 190)
INK = (38, 32, 28)
INK_SOFT = (96, 86, 74)
TEXT = (236, 243, 246)
MUTED = (150, 178, 192)
GOOD = (96, 208, 140)
BAD = (240, 98, 98)
WARN = (246, 184, 70)
WHITE = (255, 255, 255)

# Cada medidor tem cor E ícone E texto: nada depende só de cor (daltonismo).
METER_COLOR = {
    "povo": (118, 164, 246),
    "servicos": (62, 200, 168),
    "cofre": (246, 190, 76),
    "integridade": (204, 150, 232),
}

KIND_LABEL = {
    "pedido": "PEDIDO", "politica": "DECISÃO", "crise": "CRISE", "evento": "ACONTECIMENTO",
    "consequencia": "CONSEQUÊNCIA", "especial": "ESPECIAL",
}
KIND_COLOR = {
    "pedido": (70, 130, 200), "politica": (130, 96, 180), "crise": (206, 74, 66),
    "evento": (96, 120, 130), "consequencia": (214, 132, 44), "especial": (46, 150, 112),
}

END_COLOR = {"good": (96, 208, 140), "mid": (246, 190, 76), "bad": (240, 98, 98)}

# Geometria da carta (centralizada).
CARD_W, CARD_H = 440, 466
CARD_X = (W - CARD_W) // 2
CARD_Y = 126
