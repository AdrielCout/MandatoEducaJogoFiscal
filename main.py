"""Mandato — Contas da Cidade (EducaJogo Fiscal).

Rodar no computador:      python main.py
Testes:                   python -m unittest discover -s tests -v

Controles: mouse (arraste a carta ou clique nos botões) ou ← → para decidir,
Enter para continuar, C caderno, H histórico, M mediador, S som, F3 depuração, F11 tela cheia.
"""

import asyncio
import sys

try:
    import pygame  # noqa: F401
except ImportError:
    print("O pygame-ce não está instalado neste Python.\n"
          f"Python em uso: {sys.executable}\n\n"
          "Instale com o MESMO Python que roda o jogo:\n"
          f'  "{sys.executable}" -m pip install -r requirements.txt\n\n'
          "No VS Code, confira também se o interpretador selecionado é o do .venv\n"
          "(Ctrl+Shift+P > 'Python: Select Interpreter').")
    sys.exit(1)

from educajogo.ui.app import run  # noqa: E402

asyncio.run(run())
