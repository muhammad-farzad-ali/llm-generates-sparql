"""SPARQL validator: validates syntax, schema compliance, and triples."""

import re
from typing import List, Optional
from .models import ValidationResult, Triple, Entity, SchemaContext
from .config import DBLP_KEY_PREDICATES


class SPARQLValidator:
    """Validates SPARQL queries for correctness."""

    def validate(
        self,
        sparql: str,
        schema_context: Optional[SchemaContext] = None,
        entities: Optional[List[Entity]] = None,
    ) -> ValidationResult:
        """Run all validation checks."""
        errors = []
        warnings = []
        triples = []

        if not sparql or not sparql.strip():
            return ValidationResult(
                valid=False, errors=["Empty SPARQL query"], warnings=[], triples=[]
            )

        if "{" not in sparql or "}" not in sparql:
            errors.append("Missing WHERE clause braces")
            return ValidationResult(valid=False, errors=errors, triples=[])

        triples = self._extract_triples(sparql)

        prefix_errors = self._validate_prefixes(sparql)
        errors.extend(prefix_errors)

        pred_errors = self._validate_predicates(sparql, schema_context)
        errors.extend(pred_errors)

        entity_errors = self._validate_entities(sparql, entities or [])
        warnings.extend(entity_errors)

        structure_warnings = self._validate_structure(sparql)
        warnings.extend(structure_warnings)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            triples=triples,
        )

    def _extract_triples(self, sparql: str) -> List[Triple]:
        """Extract triple patterns from SPARQL."""
        triples = []
        pattern = r"(\??\w+)\s+(dblp:\w+)\s+(<?[^>\s]+>?|\??\w+)"
        matches = re.findall(pattern, sparql)

        for match in matches:
            triples.append(
                Triple(subject=match[0], predicate=match[1], object=match[2])
            )

        return triples

    def _validate_prefixes(self, sparql: str) -> List[str]:
        """Check required prefixes are declared."""
        errors = []

        if "dblp:" in sparql and "PREFIX dblp:" not in sparql:
            errors.append("Missing PREFIX declaration for dblp:")

        return errors

    def _validate_predicates(
        self, sparql: str, schema_context: Optional[SchemaContext]
    ) -> List[str]:
        """Check all predicates exist in schema."""
        errors = []
        pred_pattern = r"dblp:(\w+)"
        predicates_used = set(re.findall(pred_pattern, sparql))

        known_predicates = set(DBLP_KEY_PREDICATES)
        if schema_context:
            for p in schema_context.properties:
                known_predicates.add(p.label)

        for pred in predicates_used:
            if pred not in known_predicates:
                errors.append(f"Unknown predicate: dblp:{pred}")

        return errors

    def _validate_entities(self, sparql: str, entities: List[Entity]) -> List[str]:
        """Check entity URIs are valid."""
        warnings = []

        for entity in entities:
            if entity.uri and entity.uri not in sparql:
                warnings.append(f"Entity URI not used: {entity.mention}")

        return warnings

    def _validate_structure(self, sparql: str) -> List[str]:
        """Validate query structure."""
        warnings = []

        if sparql.count("{") != sparql.count("}"):
            warnings.append("Unbalanced braces in query")

        return warnings
