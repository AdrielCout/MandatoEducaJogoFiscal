# Mandato — Contas da Cidade

Jogo de decisões em cartas (estilo *Reigns*), em pygame-ce, sobre Educação Fiscal para o Ensino Médio.
Projeto de extensão EducaJogo Fiscal (NAF/Unichristus).

## Instalação

Requisito: **Python 3.10 ou mais novo** (https://www.python.org/downloads/).
No Windows, marque "Add python.exe to PATH" durante a instalação.

### Windows (PowerShell ou Prompt de Comando)

```bat
cd caminho\para\mandato
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Linux e macOS

```bash
cd caminho/para/mandato
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

A única dependência externa é o `pygame-ce` (versão fixada em `requirements.txt`).
O resto usa apenas a biblioteca padrão do Python.

## Executar

Com o ambiente virtual ativado:

```bash
python main.py
```

Controles: arraste a carta ou clique nos botões; use ← e → para decidir; Enter continua;
C abre o Caderno; H o histórico; M liga/desliga o Mediador; S o som; F3 a depuração; F11 tela cheia.

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes não abrem janela (rodam com SDL em modo "dummy").

## Ferramentas de conteúdo

```bash
python tools/validate.py     # confere referências entre cartas, personagens, finais e verbetes
python tools/simulate.py     # simula mandatos com jogadores robôs (equilíbrio)
```

## Estrutura

- `educajogo/core/` — motor do jogo, sem pygame (regras, cartas, finais, save)
- `educajogo/ui/` — interface em pygame-ce (cenas, desenho, som)
- `data/` — todo o conteúdo (cartas, personagens, finais, verbetes), em JSON
- `tests/` — testes do motor e da interface
- `tools/` — validador e simulador
- `docs/` — planejamento
