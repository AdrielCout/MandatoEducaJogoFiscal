"""Efeitos sonoros gerados por código (sem arquivos de áudio).

Se não houver dispositivo de som (computadores de escola, testes, navegador bloqueado),
o jogo continua normalmente em silêncio: nada aqui pode derrubar a partida.
"""

from __future__ import annotations

import math
from array import array

import pygame

RATE = 22050


def _tone(freqs, dur=0.12, vol=0.35, decay=6.0, sweep=0.0, shape="sine") -> bytes:
    """Gera uma sequência de notas (lista de frequências) com envelope exponencial."""
    out = array("h")
    n_per = int(RATE * dur)
    for f in freqs:
        for i in range(n_per):
            t = i / RATE
            ff = f * (1 + sweep * (i / n_per))
            ph = 2 * math.pi * ff * t
            v = math.sin(ph) if shape == "sine" else (2 / math.pi) * math.asin(math.sin(ph))
            env = math.exp(-decay * i / n_per) * min(1.0, i / 120)
            out.append(int(32767 * vol * v * env))
    return out.tobytes()


class Sfx:
    def __init__(self, muted: bool = False):
        self.muted = muted
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.ok = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=RATE, size=-16, channels=1, buffer=512)
            spec = {
                "click": _tone([740], 0.05, 0.25, 8),
                "swipe": _tone([420], 0.14, 0.22, 5, sweep=-0.45, shape="tri"),
                "good": _tone([523, 659, 784], 0.09, 0.30, 4),
                "bad": _tone([330, 262], 0.14, 0.32, 4, shape="tri"),
                "stamp": _tone([196], 0.16, 0.40, 9, shape="tri"),
                "win": _tone([523, 659, 784, 1047], 0.13, 0.32, 3),
                "lose": _tone([392, 330, 262, 196], 0.16, 0.32, 3, shape="tri"),
                "term": _tone([880, 1175], 0.08, 0.22, 5),
            }
            self.sounds = {k: pygame.mixer.Sound(buffer=v) for k, v in spec.items()}
            self.ok = True
        except (pygame.error, NotImplementedError, OSError):
            self.ok = False

    def play(self, name: str):
        if self.ok and not self.muted:
            try:
                self.sounds[name].play()
            except (pygame.error, KeyError):
                pass
