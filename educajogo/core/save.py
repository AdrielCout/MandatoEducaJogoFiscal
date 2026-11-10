"""Estado PERMANENTE (sobrevive entre mandatos). O estado temporário vive em engine.Run."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Save:
    endings: set = field(default_factory=set)      # finais já vistos
    glossary: set = field(default_factory=set)     # termos do Caderno desbloqueados
    selos: set = field(default_factory=set)        # objetivos já conquistados
    flags: set = field(default_factory=set)        # flags permanentes de legado
    seen_cards: set = field(default_factory=set)   # cartas já vistas (Caderno / cobertura)
    history: list = field(default_factory=list)    # resumo de cada mandato
    last_ending: str | None = None                 # como o mandato anterior terminou
    mandates: int = 0
    mediator_mode: bool = True                     # mostra o painel "Conceito" após cada escolha
    muted: bool = False
    show_hints: bool = True                        # pontos de impacto sobre os medidores ao arrastar a carta
    path: Path | None = None

    # ---------- (de)serialização ----------
    def to_dict(self) -> dict:
        return {
            "version": 1,
            "endings": sorted(self.endings),
            "glossary": sorted(self.glossary),
            "selos": sorted(self.selos),
            "flags": sorted(self.flags),
            "seen_cards": sorted(self.seen_cards),
            "history": self.history[-30:],
            "last_ending": self.last_ending,
            "mandates": self.mandates,
            "mediator_mode": self.mediator_mode,
            "muted": self.muted,
            "show_hints": self.show_hints,
        }

    @classmethod
    def from_dict(cls, d: dict, path: Path | None = None) -> "Save":
        s = cls(path=path)
        s.endings = set(d.get("endings", []))
        s.glossary = set(d.get("glossary", []))
        s.selos = set(d.get("selos", []))
        s.flags = set(d.get("flags", []))
        s.seen_cards = set(d.get("seen_cards", []))
        s.history = list(d.get("history", []))
        s.last_ending = d.get("last_ending")
        s.mandates = int(d.get("mandates", 0))
        s.mediator_mode = bool(d.get("mediator_mode", True))
        s.muted = bool(d.get("muted", False))
        s.show_hints = bool(d.get("show_hints", True))
        return s

    # ---------- disco ----------
    @classmethod
    def default_path(cls) -> Path:
        base = os.environ.get("MANDATO_SAVE_DIR")
        if base:
            return Path(base) / "mandato_save.json"
        return Path.home() / ".mandato" / "mandato_save.json"

    @classmethod
    def load(cls, path: Path | None = None) -> "Save":
        path = path or cls.default_path()
        try:
            return cls.from_dict(json.loads(path.read_text(encoding="utf-8")), path)
        except (OSError, ValueError):
            return cls(path=path)  # arquivo ausente ou corrompido: recomeça limpo

    @classmethod
    def memory(cls) -> "Save":
        """Save sem arquivo (testes e simulador)."""
        return cls(path=None)

    def write(self) -> bool:
        if self.path is None:
            return False
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=1), encoding="utf-8")
            tmp.replace(self.path)  # troca atômica: não corrompe se fechar no meio
            return True
        except OSError:
            return False  # ex.: navegador sem disco; o jogo continua funcionando

    def reset(self) -> None:
        keep_path = self.path
        self.__dict__.update(Save(path=keep_path).__dict__)
