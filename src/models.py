"""Data models for the Text-to-SPARQL system."""

from typing import List, Optional
from pydantic import BaseModel, Field


class Entity(BaseModel):
    """An entity linked from natural language to DBLP URI."""

    mention: str = Field(..., description="Original text mention")
    uri: str = Field(..., description="DBLP URI")
    label: str = Field(..., description="Human-readable label")
    entity_type: str = Field(..., description="Entity type (Person, Conference, etc.)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class SchemaClass(BaseModel):
    """A class from the DBLP schema."""

    iri: str
    label: str
    description: str


class SchemaProperty(BaseModel):
    """A property from the DBLP schema."""

    iri: str
    label: str
    description: str
    domain: Optional[str] = None
    range: Optional[str] = None


class SchemaContext(BaseModel):
    """Schema context for LLM prompting."""

    classes: List[SchemaClass] = Field(default_factory=list)
    properties: List[SchemaProperty] = Field(default_factory=list)


class Example(BaseModel):
    """A few-shot example for LLM prompting."""

    id: int
    question: str
    sparql: str
    query_type: str
    similarity: float = 0.0


class QueryRequest(BaseModel):
    """API request for natural language to SPARQL conversion."""

    question: str = Field(..., min_length=1, description="Natural language question")
    execute: bool = Field(default=False, description="Execute query against DBLP")
    max_retries: int = Field(default=2, ge=0, le=5, description="Max repair attempts")


class Triple(BaseModel):
    """An extracted SPARQL triple pattern."""

    subject: str
    predicate: str
    object: str


class ValidationResult(BaseModel):
    """Result of SPARQL validation."""

    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    triples: List[Triple] = Field(default_factory=list)


class QueryResponse(BaseModel):
    """API response with generated SPARQL."""

    question: str
    sparql: str
    confidence: float
    validation: ValidationResult
    entities: List[Entity] = Field(default_factory=list)
    results: Optional[List[dict]] = None
    attempts: int = 1
    repair_history: List[dict] = Field(default_factory=list)
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    schema_loaded: bool = False
    examples_count: int = 0
