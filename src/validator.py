"""SPARQL validator: validates syntax, schema compliance, and triples."""

import re
from typing import List, Optional
from .models import ValidationResult, Triple, Entity, SchemaContext
from .config import DBLP_KEY_PREDICATES, DBLP_KEY_CLASSES


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

        pred_errors = self._validate_predicates_and_classes(sparql, schema_context)
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
        """Extract triple patterns from SPARQL, handling 'a' as rdf:type."""
        triples = []
        where_clause = self._extract_where_clause(sparql)
        if not where_clause:
            return triples

        pattern = r"(\??\w+)\s+(a|dblp:\w+)\s+(<?[^>\s]+>?|\??\w+)\s*[.\s]"
        matches = re.findall(pattern, where_clause)

        for match in matches:
            predicate = match[1]
            if predicate == "a":
                predicate = "rdf:type"

            triples.append(
                Triple(subject=match[0], predicate=predicate, object=match[2])
            )

        return triples

    def _extract_where_clause(self, sparql: str) -> str:
        """Extract the WHERE clause from SPARQL."""
        match = re.search(r"WHERE\s*\{(.+?)\}", sparql, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1)
        return ""

    def _validate_prefixes(self, sparql: str) -> List[str]:
        """Check required prefixes are declared."""
        errors = []

        if "dblp:" in sparql and "PREFIX dblp:" not in sparql:
            errors.append("Missing PREFIX declaration for dblp:")

        return errors

    def _validate_predicates_and_classes(
        self, sparql: str, schema_context: Optional[SchemaContext]
    ) -> List[str]:
        """Check predicates and classes are valid, handling rdf:type."""
        errors = []
        where_clause = self._extract_where_clause(sparql)
        if not where_clause:
            return errors

        known_predicates = set(DBLP_KEY_PREDICATES)
        known_classes = set(DBLP_KEY_CLASSES)

        if schema_context:
            for p in schema_context.properties:
                known_predicates.add(p.label)
            for c in schema_context.classes:
                known_classes.add(c.label)

        type_pattern = r"(\??\w+)\s+a\s+(dblp:\w+)"
        type_matches = re.findall(type_pattern, where_clause)
        for match in type_matches:
            class_name = match[1].replace("dblp:", "")
            if class_name not in known_classes:
                errors.append(f"Unknown class: dblp:{class_name}")

        pred_pattern = r"(\??\w+)\s+(dblp:\w+)\s+(<?[^>\s]+>?|\??\w+)"
        pred_matches = re.findall(pred_pattern, where_clause)
        for match in pred_matches:
            predicate = match[1].replace("dblp:", "")
            if predicate not in known_predicates:
                subject = match[0]
                if subject != "a":
                    errors.append(f"Unknown predicate: dblp:{predicate}")

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
