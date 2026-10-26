"""Joga o jogo SEM janela (driver de vídeo 'dummy'), navega por todas as telas e salva capturas.

Serve de teste de ponta a ponta (menu -> partida -> arrastar carta -> resultado -> fim -> Caderno)
e gera as imagens de interface usadas no GDD.

Uso:  python tools/screenshots.py [pasta_de_saida]     (padrão: docs/telas)
"""

import os
import random
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame  # noqa: E402

from educajogo.core.save import Save  # noqa: E402
from educajogo.ui.app import App  # noqa: E402
from educajogo.ui.scene_end import EndScene  # noqa: E402
from educajogo.ui.scene_game import GameScene  # noqa: E402


def key(app, k):
    app.handle(pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0))


def mouse(app, kind, pos, **kw):
    kw.setdefault("button", 1)
    app.handle(pygame.event.Event(kind, pos=pos, **kw))


def frames(app, n=20, dt=0.016):
    for _ in range(n):
        app.tick(dt)


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "docs" / "telas"
    out.mkdir(parents=True, exist_ok=True)
    random.seed(11)
    app = App(save=Save.memory())
    app.seed = 21                                   # mandato reprodutível

    def shot(name):
        frames(app, 2)
        pygame.image.save(app.canvas, str(out / f"{name}.png"))
        print("  capturada:", name)

    frames(app, 3)
    shot("01_menu")
    key(app, pygame.K_h)
    shot("02_como_jogar")
    key(app, pygame.K_SPACE)

    key(app, pygame.K_RETURN)
    assert isinstance(app.scene, GameScene), "Enter deveria abrir a partida"
    frames(app, 30)
    g = app.scene
    # a carta de abertura é decidida pelo teclado; depois, arrastamos de verdade com o mouse
    key(app, pygame.K_RIGHT)
    frames(app, 40)
    shot("04_resultado")
    key(app, pygame.K_SPACE)
    frames(app, 30)
    shot("03_carta")
    mouse(app, pygame.MOUSEBUTTONDOWN, (640, 340))
    mouse(app, pygame.MOUSEMOTION, (560, 340), rel=(-80, 0), buttons=(1, 0, 0))
    frames(app, 3)
    shot("05_arrastando")
    mouse(app, pygame.MOUSEMOTION, (470, 340), rel=(-90, 0), buttons=(1, 0, 0))
    mouse(app, pygame.MOUSEBUTTONUP, (470, 340))
    assert g.phase == "exit", f"soltar a carta além do limite deveria decidir (fase={g.phase})"
    frames(app, 40)
    assert g.phase == "outcome"

    # joga até o fim, tirando uma foto no meio do mandato
    rng = random.Random(4)
    took_mid = False
    guard = 0
    while not isinstance(app.scene, EndScene):
        guard += 1
        assert guard < 400, "o mandato não terminou"
        sc = app.scene
        if sc.phase == "idle":
            if not took_mid and sc.run.month >= 20 and sc.run.history:
                shot("06_meio_do_mandato")
                took_mid = True
            key(app, rng.choice((pygame.K_LEFT, pygame.K_RIGHT)))
        elif sc.phase == "outcome":
            key(app, pygame.K_SPACE)
        frames(app, 3)
    frames(app, 10)
    shot("07_prestacao_de_contas")
    print("  final:", app.scene.end["title"], "| meses:", app.scene.sum["months"], "| decisões:", app.scene.sum["decisions"])

    key(app, pygame.K_c)
    for i, name in enumerate(("08_caderno", "09_finais", "10_mandatos", "11_selos")):
        frames(app, 3)
        shot(name)
        key(app, pygame.K_RIGHT)
    key(app, pygame.K_ESCAPE)
    assert isinstance(app.scene, EndScene), "Esc na memória deveria voltar à tela final"

    # segundo mandato: sucessão e herança
    app.seed = 22
    key(app, pygame.K_RETURN)
    assert isinstance(app.scene, GameScene) and app.scene.run.mandate_no == 2
    key(app, pygame.K_F3)
    frames(app, 30)
    shot("12_depuracao_F3")
    print("OK: fluxo completo sem erros")


if __name__ == "__main__":
    main()
