"""Stage 7: deterministic candidate ranking.

Score composition (priority dominates; components never let a lower
match type overtake a higher one):

* match-type priority * 1000   (lemma 6 > form 5 > normalized 4 >
  morphology 3 > definition 2 > fuzzy 1)
* + morphological certainty * 100   (constant 1.0 for non-morph matches)
* + fuzzy similarity * 50           (0 unless fuzzy matched)
* + frequency bonus 0..100          (100 / (1 + log10(rank)); 0 if unknown)

Ties break on (normalized lemma, lexeme id) — the ordering is fully
deterministic.
"""

from __future__ import annotations

import math

from app.domain.enums import MATCH_TYPE_PRIORITY
from app.domain.models import FrequencyInfo, RankedCandidate, SearchCandidate
from app.domain.models import Lexeme as DomainLexeme
from app.orm import models as orm
from app.repositories import mappers
from app.services.search.context import SearchContext


def match_score(candidate: SearchCandidate, frequency: FrequencyInfo | None) -> float:
    priority = MATCH_TYPE_PRIORITY[candidate.match_type]
    score = priority * 1000.0
    score += max(0.0, min(1.0, candidate.morph_certainty)) * 100.0
    score += max(0.0, min(1.0, candidate.similarity)) * 50.0
    if frequency is not None and frequency.rank >= 1:
        score += 100.0 / (1.0 + math.log10(frequency.rank))
    return round(score, 6)


class SearchRanker:
    def rank(
        self,
        context: SearchContext,
        lexemes: dict[str, orm.Lexeme],
        frequency: dict[str, FrequencyInfo],
    ) -> list[RankedCandidate]:
        ranked: list[RankedCandidate] = []
        for lexeme_id, candidate in context.candidates.items():
            row = lexemes.get(lexeme_id)
            if row is None:
                continue
            lexeme: DomainLexeme = mappers.to_lexeme(row)
            frequency_info = frequency.get(lexeme_id)
            ranked.append(
                RankedCandidate(
                    candidate=candidate,
                    lexeme=lexeme,
                    frequency_rank=frequency_info.rank if frequency_info else None,
                    score=match_score(candidate, frequency_info),
                )
            )
        ranked.sort(key=lambda item: (-item.score, item.lexeme.normalized_lemma, item.lexeme.id))
        return ranked[: context.limit]
