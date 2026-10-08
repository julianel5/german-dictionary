"""Text parsing service: word spans + morphological analyses.

Depends only on the MorphologyEngine abstraction; when no engine is
configured, tokens are still returned with empty analysis lists.
"""

from __future__ import annotations

import re

from app.schemas.mappers import features_dto
from app.schemas.parse import ParseAnalysisDTO, ParseResponse, ParseTokenDTO
from german_morphology import MorphologyEngine

_WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)?", re.UNICODE)
_MAX_ANALYSES_PER_TOKEN = 5


class ParseService:
    def __init__(self, engine: MorphologyEngine | None) -> None:
        self._engine = engine

    def parse(self, text: str) -> ParseResponse:
        tokens: list[ParseTokenDTO] = []
        for match in _WORD.finditer(text):
            surface = match.group()
            analyses: list[ParseAnalysisDTO] = []
            if self._engine is not None:
                for analysis in self._engine.analyze(surface)[:_MAX_ANALYSES_PER_TOKEN]:
                    analyses.append(
                        ParseAnalysisDTO(
                            lemma=analysis.lemma,
                            part_of_speech=analysis.part_of_speech,
                            features=features_dto(analysis.features),
                            confidence=analysis.confidence,
                            engine=analysis.engine,
                        )
                    )
            tokens.append(
                ParseTokenDTO(
                    surface=surface,
                    start=match.start(),
                    end=match.end(),
                    analyses=analyses,
                )
            )
        return ParseResponse(
            text=text,
            engine=self._engine.name if self._engine is not None else None,
            tokens=tokens,
        )
