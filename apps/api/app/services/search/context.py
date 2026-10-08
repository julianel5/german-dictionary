"""Shared search context and the stage interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from app.domain.enums import MATCH_TYPE_PRIORITY, MatchType
from app.domain.models import SearchCandidate
from german_morphology import MorphologicalAnalysis


@dataclass
class SearchContext:
    """Mutable state shared by the pipeline stages.

    Stages only communicate through this context: each stage contributes
    candidates and analyses, never re-runs another stage.
    """

    query: str
    limit: int = 20
    normalized: str = ""
    candidates: dict[str, SearchCandidate] = field(default_factory=dict)
    analyses: dict[str, list[MorphologicalAnalysis]] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.candidates

    def add_analysis(self, lexeme_id: str, analysis: MorphologicalAnalysis) -> None:
        self.analyses.setdefault(lexeme_id, []).append(analysis)

    def add_candidate(self, candidate: SearchCandidate) -> None:
        """Add/merge a candidate: the higher-priority match type wins.

        Ties keep the earlier contribution (stage order is deterministic);
        an exact surface row beats a merely-normalized one within the
        ``FORM``/``NORMALIZED`` boundary.
        """
        current = self.candidates.get(candidate.lexeme_id)
        if current is None:
            self.candidates[candidate.lexeme_id] = candidate
            return
        new_priority = MATCH_TYPE_PRIORITY[candidate.match_type]
        current_priority = MATCH_TYPE_PRIORITY[current.match_type]
        if new_priority > current_priority or (
            new_priority == current_priority
            and candidate.match_type == MatchType.FORM
            and current.matched_surface != self.query
            and candidate.matched_surface == self.query
        ):
            self.candidates[candidate.lexeme_id] = candidate


@runtime_checkable
class SearchStage(Protocol):
    """One independent step of the search pipeline."""

    name: str

    def run(self, context: SearchContext) -> None: ...
