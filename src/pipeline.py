"""Main pipeline: orchestrates the Text-to-SPARQL conversion."""

from typing import List, Dict, Optional
from .models import (
    Entity,
    Example,
    SchemaContext,
    QueryRequest,
    QueryResponse,
    ValidationResult,
)
from .entity_linker import EntityLinker
from .schema_retriever import SchemaRetriever
from .example_retriever import ExampleRetriever
from .llm_generator import LLMGenerator
from .validator import SPARQLValidator
from .executor import SPARQLExecutor
from .config import MAX_RETRIES, DBLP_PREFIXES


class Pipeline:
    """Main pipeline for natural language to SPARQL conversion."""

    def __init__(self):
        self.entity_linker = EntityLinker()
        self.schema_retriever = SchemaRetriever()
        self.example_retriever = ExampleRetriever()
        self.llm_generator = LLMGenerator()
        self.validator = SPARQLValidator()
        self.executor = SPARQLExecutor()

    def convert(self, request: QueryRequest) -> QueryResponse:
        """Convert natural language question to SPARQL query."""
        entities = self._extract_entities(request.question)

        schema_context = self.schema_retriever.get_relevant_schema()

        examples = self.example_retriever.retrieve(request.question, k=3)

        llm_result = self.llm_generator.generate(
            question=request.question,
            entities=entities,
            schema_context=schema_context,
            examples=examples,
            schema_formatter=self.schema_retriever.format_for_prompt,
            example_formatter=self.example_retriever.format_for_prompt,
        )

        sparql = llm_result.get("sparql", "")
        confidence = llm_result.get("confidence", 0.0)

        if not sparql:
            return QueryResponse(
                question=request.question,
                sparql="",
                confidence=0.0,
                validation=ValidationResult(
                    valid=False, errors=["LLM failed to generate SPARQL"]
                ),
                entities=entities,
                error=llm_result.get("error", "Generation failed"),
            )

        sparql_with_prefixes = self._add_prefixes(sparql)

        validation = self.validator.validate(
            sparql_with_prefixes, schema_context, entities
        )

        results = None
        attempts = 1
        repair_history = []

        if request.execute and validation.valid:
            exec_result = self.executor.execute(sparql_with_prefixes)
            if exec_result["success"]:
                results = exec_result["results"]
            elif request.max_retries > 0:
                repaired = self._repair_loop(
                    sparql_with_prefixes,
                    exec_result["error"],
                    request.question,
                    entities,
                    schema_context,
                    request.max_retries,
                )
                if repaired:
                    sparql_with_prefixes = repaired
                    validation = self.validator.validate(
                        sparql_with_prefixes, schema_context, entities
                    )
                    exec_result = self.executor.execute(sparql_with_prefixes)
                    if exec_result["success"]:
                        results = exec_result["results"]
                    attempts = request.max_retries + 1

        return QueryResponse(
            question=request.question,
            sparql=sparql_with_prefixes,
            confidence=confidence,
            validation=validation,
            entities=entities,
            results=results,
            attempts=attempts,
            repair_history=repair_history,
        )

    def _extract_entities(self, question: str) -> List[Entity]:
        """Extract entities from the question."""
        import re

        patterns = [
            r"(?:by|authored by|written by|published by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(?:at|in|from)\s+([A-Z][A-Z0-9]+(?:\s+[A-Z][a-z]+)*)",
            r'"([^"]+)"',
        ]

        mentions = []
        for pattern in patterns:
            matches = re.findall(pattern, question)
            for match in matches:
                mentions.append({"text": match.strip()})

        if not mentions:
            words = question.split()
            for i, word in enumerate(words):
                if word[0:1].isupper() and len(word) > 2:
                    next_word = words[i + 1] if i + 1 < len(words) else ""
                    if next_word and next_word[0:1].isupper():
                        mentions.append({"text": f"{word} {next_word}"})

        return self.entity_linker.link_batch(mentions)

    def _add_prefixes(self, sparql: str) -> str:
        """Add PREFIX declarations if missing."""
        if "PREFIX" in sparql:
            return sparql
        return DBLP_PREFIXES + "\n" + sparql

    def _repair_loop(
        self,
        sparql: str,
        error: str,
        question: str,
        entities: List[Entity],
        schema_context: SchemaContext,
        max_retries: int,
    ) -> Optional[str]:
        """Attempt to repair a failed query."""
        current = sparql

        for i in range(max_retries):
            repaired = self.llm_generator.repair(
                sparql=current,
                error=error,
                question=question,
                entities=entities,
                schema_context=schema_context,
                schema_formatter=self.schema_retriever.format_for_prompt,
            )

            if repaired and repaired != current:
                validation = self.validator.validate(repaired, schema_context, entities)
                if validation.valid:
                    exec_result = self.executor.execute(repaired)
                    if exec_result["success"]:
                        return self._add_prefixes(repaired)
                    error = exec_result["error"]
                current = self._add_prefixes(repaired)

        return None

    def close(self):
        """Cleanup resources."""
        self.entity_linker.close()
