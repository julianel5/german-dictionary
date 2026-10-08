"""Stage 4: morphological analysis of the query.

Runs only through the :class:`MorphologyEngine` abstraction — this module
never imports a concrete engine. Analyses whose lemma does not resolve to
a stored lexeme are dropped rather than fabricated.
"""

from __future__ import annotations

from app.domain.enums import MatchType
from app.domain.models import SearchCandidate
from app.repositories.lexeme_repo import LexemeRepository
from app.repositories.lookup_repo import LookupRepository
from app.services.search.context import SearchContext
from german_morphology import MorphologyEngine


class MorphologyStage:
    name = "morphology"

    def __init__(
        self,
        engine: MorphologyEngine | None,
        lexemes: LexemeRepository,
        lookups: LookupRepository,
    ) -> None:
        self._engine = engine
        self._lexemes = lexemes
        self._lookups = lookups

    def run(self, context: SearchContext) -> None:
        if self._engine is None or not context.query.strip():
            return
        for analysis in self._engine.analyze(context.query):
            if not analysis.normalized_lemma:
                continue
            confidence = max(0.0, min(1.0, analysis.confidence))
            for lexeme in self._lexemes.by_normalized_lemma(analysis.normalized_lemma):
                context.add_analysis(lexeme.id, analysis)
                stored_form = self._lookups.form_for_lexeme(lexeme.id, context.normalized)
                context.add_candidate(
                    SearchCandidate(
                        lexeme_id=lexeme.id,
                        match_type=MatchType.MORPHOLOGY,
                        matched_surface=context.query,
                        word_form_id=stored_form.id if stored_form else None,
                        morph_certainty=confidence,
                        analysis=analysis,
                    )
                )
