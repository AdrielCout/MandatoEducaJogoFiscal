"""Joga um mandato de verdade pelo laço do jogo (sem janela) e salva capturas de tela em docs/telas/.

Uso:  SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python tools/shots.py
Serve como teste de fumaça da interface E como evidência visual para o GDD.
"""
import os, random, sys
from pathlib import Path
os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pygame
from educajogo.core.save import Save
from educajogo.ui.app import App
from educajogo.ui.scene_game import GameScene
from educajogo.ui.scene_end import EndScene
from educajogo.ui.scene_memory import MemoryScene

OUT = Path(__file__).resolve().parent.parent / "docs" / "telas"
OUT.mkdir(parents=True, exist_ok=True)

def snap(app, name):
    app.tick(0.016); pygame.image.save(app.canvas, str(OUT / f"{name}.png"))

def settle(app, n=30):
    for _ in range(n): app.tick(0.02)

def key(app, k): app.handle(pygame.event.Event(pygame.KEYDOWN, {"key": k, "mod": 0, "unicode": ""}))
def mouse(app, typ, pos): app.handle(pygame.event.Event(typ, {"pos": pos, "button": 1, "buttons": (1,0,0), "rel": (0,0)}))

def main():
    rng = random.Random(11)
    app = App(save=Save.memory(), size=(1280, 720))
    settle(app); snap(app, "01_menu")
    app.scene.help = True; snap(app, "02_como_jogar"); app.scene.help = False
    key(app, pygame.K_RETURN); settle(app)
    assert isinstance(app.scene, GameScene)
    g = app.scene; snap(app, "03_carta_tutorial")
    shots = {1: "04_carta", 2: "05_resultado_conceito"}
    turn = 0
    while isinstance(app.scene, GameScene):
        g = app.scene
        if g.mode == "card":
            settle(app, 16)                                         # espera a animação de entrada terminar
            if turn == 1: snap(app, "04_carta")
            side = rng.choice(("left", "right"))
            if turn == 3:                                           # arrasto com o mouse: prévia + dicas de impacto
                mouse(app, pygame.MOUSEBUTTONDOWN, (640, 300)); mouse(app, pygame.MOUSEMOTION, (520, 300)); settle(app, 3)
                snap(app, "06_arrastando_dicas")
                mouse(app, pygame.MOUSEBUTTONUP, (520, 300))
            else:
                key(app, pygame.K_LEFT if side == "left" else pygame.K_RIGHT)
            settle(app, 20)
            if turn in shots: pass
            turn += 1
        else:
            if turn - 1 in shots: snap(app, shots[turn - 1]); shots.pop(turn - 1)
            key(app, pygame.K_SPACE); settle(app, 5)
            if turn == 6:
                app.debug = True; snap(app, "07_depuracao_F3"); app.debug = False
        if turn > 60: raise SystemExit("mandato não terminou")
    settle(app); assert isinstance(app.scene, EndScene), type(app.scene)
    snap(app, "08_fim_prestacao_de_contas")
    key(app, pygame.K_c); settle(app); assert isinstance(app.scene, MemoryScene)
    snap(app, "09_caderno")
    for i, name in ((1, "10_finais"), (2, "11_mandatos"), (3, "12_selos")):
        key(app, pygame.K_1 + i); settle(app, 3); snap(app, name)
    print("OK:", len(list(OUT.glob('*.png'))), "capturas em", OUT, "| final:", app.save.last_ending)

if __name__ == "__main__":
    main()
