from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from utils.budgeting import count_words


class GroundedDefinition(BaseModel):
    term: str = Field(description="Concise concept or term name")
    definition: str = Field(
        description="Short learner-friendly definition grounded in the retrieved evidence"
    )
    reference_ids: list[str] = Field(
        default_factory=list,
        description="IDs of source references that support this definition",
    )


class GroundedExample(BaseModel):
    title: str = Field(description="Short label for the example")
    summary: str = Field(
        description="Concise explanation of the example grounded in the evidence"
    )
    reference_ids: list[str] = Field(
        default_factory=list,
        description="IDs of source references that support this example",
    )


class SourceFact(BaseModel):
    fact: str = Field(description="Atomic factual statement supported by the source")
    reference_ids: list[str] = Field(
        default_factory=list,
        description="IDs of source references that support this fact",
    )


class SourceReference(BaseModel):
    reference_id: str = Field(description="Stable reference identifier such as ref_01")
    document_name: str = Field(description="PDF document name")
    locator: str = Field(description="Page and chunk locator such as page 5, chunk 2")
    chunk_id: str = Field(description="Stable chunk identifier from retrieval")
    similarity_score: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Vector-search similarity score when available",
    )


class GroundedNotes(BaseModel):
    topic: str = Field(description="Requested topic or question")
    learner_level: str = Field(description="Who the notes are for")
    key_concepts: list[str] = Field(
        default_factory=list,
        description="Short list of core concepts needed for the lesson",
    )
    definitions: list[GroundedDefinition] = Field(
        default_factory=list,
        description="Concise grounded definitions of important terms",
    )
    examples: list[GroundedExample] = Field(
        default_factory=list,
        description="Short grounded examples worth teaching from",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Important caveats, assumptions, or constraints from the source",
    )
    source_facts: list[SourceFact] = Field(
        default_factory=list,
        description="Atomic facts that later stages can safely rely on",
    )
    source_references: list[SourceReference] = Field(
        default_factory=list,
        description="Traceable references back to the retrieved evidence",
    )
    notes_summary: str = Field(
        description="Compact summary of the grounded notes for downstream planning"
    )

    @field_validator("key_concepts")
    @classmethod
    def _limit_key_concepts(cls, value: list[str]) -> list[str]:
        if len(value) > 8:
            raise ValueError("Grounded notes may include at most 8 key concepts.")
        return value

    @field_validator("definitions")
    @classmethod
    def _limit_definitions(cls, value: list[GroundedDefinition]) -> list[GroundedDefinition]:
        if len(value) > 8:
            raise ValueError("Grounded notes may include at most 8 definitions.")
        return value

    @field_validator("examples")
    @classmethod
    def _limit_examples(cls, value: list[GroundedExample]) -> list[GroundedExample]:
        if len(value) > 5:
            raise ValueError("Grounded notes may include at most 5 examples.")
        return value

    @field_validator("constraints")
    @classmethod
    def _limit_constraints(cls, value: list[str]) -> list[str]:
        if len(value) > 8:
            raise ValueError("Grounded notes may include at most 8 constraints.")
        return value

    @field_validator("source_facts")
    @classmethod
    def _limit_source_facts(cls, value: list[SourceFact]) -> list[SourceFact]:
        if len(value) > 12:
            raise ValueError("Grounded notes may include at most 12 source facts.")
        return value

    @field_validator("notes_summary")
    @classmethod
    def _limit_summary_words(cls, value: str) -> str:
        if count_words(value) > 120:
            raise ValueError("Grounded notes summary must stay within 120 words.")
        return value
