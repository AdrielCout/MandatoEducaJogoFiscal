"""Valida todo o conteúdo em data/ (referências cruzadas, flags, finais, textos longos).

Uso:  python tools/validate.py
Sai com código 1 se houver ERROS (avisos não falham).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from educajogo.core.content import Content, validate  # noqa: E402


def main() -> int:
    content = Content()
    errors, warns = validate(content)
    print(f"{len(content.cards)} cartas · {len(content.characters)} personagens · "
          f"{len(content.glossary)} termos · {len(content.endings_list)} finais · {len(content.objectives)} objetivos")
    for w in warns:
        print("  aviso:", w)
    for e in errors:
        print("  ERRO :", e)
    print("OK" if not errors else f"{len(errors)} erro(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
