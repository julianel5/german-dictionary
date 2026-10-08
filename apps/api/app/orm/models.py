"""SQLAlchemy ORM models (SQLAlchemy 2.x typed style).

Database schema intentionally separates: lexeme, sense, word form,
morphological features, lookup index, frequency, lexical relations and
example sentences. Generic column types keep the schema portable between
PostgreSQL (production/docker) and SQLite (zero-setup local/tests);
PostgreSQL-specific behavior (FTS, pg_trgm) lives in the Alembic migration
and in the dialect-aware search repositories.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def new_id() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class Lexeme(Base):
    __tablename__ = "lexemes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    lemma: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_lemma: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="de")
    part_of_speech: Mapped[str] = mapped_column(String(32), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(16))
    register: Mapped[str | None] = mapped_column(String(64))
    domain: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    senses: Mapped[list[Sense]] = relationship(
        back_populates="lexeme",
        cascade="all, delete-orphan",
        order_by="Sense.sense_index",
    )
    word_forms: Mapped[list[WordForm]] = relationship(
        back_populates="lexeme",
        cascade="all, delete-orphan",
        order_by="WordForm.surface",
    )
    lookups: Mapped[list[Lookup]] = relationship(
        back_populates="lexeme",
        cascade="all, delete-orphan",
    )
    frequency_rows: Mapped[list[Frequency]] = relationship(
        back_populates="lexeme",
        cascade="all, delete-orphan",
    )
    relations_as_source: Mapped[list[LexicalRelation]] = relationship(
        back_populates="source_lexeme",
        cascade="all, delete-orphan",
        foreign_keys="LexicalRelation.source_lexeme_id",
    )
    relations_as_target: Mapped[list[LexicalRelation]] = relationship(
        back_populates="target_lexeme",
        cascade="all, delete-orphan",
        foreign_keys="LexicalRelation.target_lexeme_id",
    )


class Sense(Base):
    __tablename__ = "senses"
    __table_args__ = (UniqueConstraint("lexeme_id", "sense_index", name="uq_sense_index"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    lexeme_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lexemes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sense_index: Mapped[int] = mapped_column(Integer, nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    register: Mapped[str | None] = mapped_column(String(64))
    domain: Mapped[str | None] = mapped_column(String(64))

    lexeme: Mapped[Lexeme] = relationship(back_populates="senses")


class WordForm(Base):
    __tablename__ = "word_forms"
    __table_args__ = (UniqueConstraint("lexeme_id", "surface", name="uq_wordform_surface"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    lexeme_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lexemes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    surface: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_surface: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    form_type: Mapped[str] = mapped_column(String(32), nullable=False)
    is_searchable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    lexeme: Mapped[Lexeme] = relationship(back_populates="word_forms")
    features: Mapped[MorphologicalFeatures | None] = relationship(
        back_populates="word_form",
        cascade="all, delete-orphan",
        uselist=False,
    )
    example_words: Mapped[list[ExampleWord]] = relationship(
        back_populates="word_form",
        cascade="all, delete-orphan",
    )


class MorphologicalFeatures(Base):
    """Structured grammatical features attached to a word form.

    Common searchable features are first-class columns; rare or
    engine-specific attributes live in the ``extra`` JSON object.
    """

    __tablename__ = "morphological_features"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    word_form_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("word_forms.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    case: Mapped[str | None] = mapped_column(String(16))
    number: Mapped[str | None] = mapped_column(String(16))
    gender: Mapped[str | None] = mapped_column(String(16))
    person: Mapped[str | None] = mapped_column(String(8))
    tense: Mapped[str | None] = mapped_column(String(16))
    mood: Mapped[str | None] = mapped_column(String(16))
    degree: Mapped[str | None] = mapped_column(String(16))
    voice: Mapped[str | None] = mapped_column(String(16))
    verb_form: Mapped[str | None] = mapped_column(String(16))
    adjective_form: Mapped[str | None] = mapped_column(String(32))
    extra: Mapped[dict | None] = mapped_column(JSON)

    word_form: Mapped[WordForm] = relationship(back_populates="features")


class Lookup(Base):
    """Lookup index: normalized surface form -> lexeme + word form."""

    __tablename__ = "lookups"
    __table_args__ = (
        UniqueConstraint("normalized_surface", "word_form_id", name="uq_lookup_surface_form"),
        Index("ix_lookups_normalized_surface", "normalized_surface"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    normalized_surface: Mapped[str] = mapped_column(String(255), nullable=False)
    lexeme_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lexemes.id", ondelete="CASCADE"), nullable=False
    )
    word_form_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("word_forms.id", ondelete="CASCADE"), nullable=False
    )

    lexeme: Mapped[Lexeme] = relationship(back_populates="lookups")
    word_form: Mapped[WordForm] = relationship()


class Frequency(Base):
    """Corpus frequency data; supports multiple corpora and optional
    word-form granularity."""

    __tablename__ = "frequencies"
    __table_args__ = (
        UniqueConstraint("corpus", "lexeme_id", "word_form_id", name="uq_frequency_corpus"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    lexeme_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lexemes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    word_form_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("word_forms.id", ondelete="CASCADE")
    )
    corpus: Mapped[str] = mapped_column(String(64), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)

    lexeme: Mapped[Lexeme] = relationship(back_populates="frequency_rows")
    word_form: Mapped[WordForm | None] = relationship()


class LexicalRelation(Base):
    __tablename__ = "lexical_relations"
    __table_args__ = (
        UniqueConstraint(
            "source_lexeme_id",
            "target_lexeme_id",
            "relation_type",
            name="uq_lexical_relation",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_lexeme_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lexemes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_lexeme_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lexemes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False)

    source_lexeme: Mapped[Lexeme] = relationship(
        back_populates="relations_as_source", foreign_keys=[source_lexeme_id]
    )
    target_lexeme: Mapped[Lexeme] = relationship(
        back_populates="relations_as_target", foreign_keys=[target_lexeme_id]
    )


class ExampleSentence(Base):
    __tablename__ = "example_sentences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    translation: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(255))

    words: Mapped[list[ExampleWord]] = relationship(
        back_populates="sentence",
        cascade="all, delete-orphan",
    )


class ExampleWord(Base):
    """Links an example sentence back to a specific word form with offsets."""

    __tablename__ = "example_words"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    example_sentence_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("example_sentences.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    word_form_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("word_forms.id", ondelete="CASCADE"), index=True
    )
    start_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    end_offset: Mapped[int] = mapped_column(Integer, nullable=False)

    sentence: Mapped[ExampleSentence] = relationship(back_populates="words")
    word_form: Mapped[WordForm | None] = relationship(back_populates="example_words")
