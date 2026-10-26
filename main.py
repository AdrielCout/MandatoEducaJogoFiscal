"""Mandato — Contas da Cidade (EducaJogo Fiscal).

Rodar no computador:      python main.py
Testes:                   python -m unittest discover -s tests -v

Controles: mouse (arraste a carta ou clique nos botões) ou ← → para decidir,
Enter para continuar, C caderno, H histórico, M mediador, S som, F3 depuração, F11 tela cheia.
"""

import asyncio

from educajogo.ui.app import run

asyncio.run(run())
