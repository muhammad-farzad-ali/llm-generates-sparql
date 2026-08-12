"""LLM generator: generates SPARQL queries using OpenAI GPT."""

import re
import openai
from typing import List, Optional, Dict
from .models import Entity, SchemaContext, Example
from .config import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS

SYSTEM_PROMPT = """You are a SPARQL expert for the DBLP Computer Science Bibliography.

Your task: Convert natural language questions into correct SPARQL queries.

MANDATORY PREFIXES (always include these at the top):
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

RULES:
1. Use ONLY predicates from the provided schema
2. Use the exact entity URIs provided (enclose in angle brackets)
3. Use the EXACT PREFIX declarations shown above
4. Return ONLY the SPARQL query, no explanation
5. Use SELECT for queries that return results
6. Use FILTER for date/string filtering
7. Use COUNT/GROUP BY for aggregation queries
8. Always enclose URIs in angle brackets: <https://dblp.org/...>
9. Use string literals with quotes: "2023"
10. For year comparisons, use the format: "2023"^^xsd:gYear

IMPORTANT:
- The DBLP namespace is: https://dblp.org/rdf/schema#
- Venue URIs use format: https://dblp.org/streams/conf/sigmod (NOT /conf/sigmod)
- Person URIs use format: https://dblp.org/pid/s/MichaelStonebraker
- Do NOT hallucinate URIs - use only the provided entity URIs
- Do NOT invent predicates - use only the provided schema predicates
- Return clean, executable SPARQL only"""


class LLMGenerator:
    """Generates SPARQL queries using OpenAI GPT."""

    def __init__(self):
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.model = LLM_MODEL

    def generate(
        self,
        question: str,
        entities: List[Entity],
        schema_context: SchemaContext,
        examples: List[Example],
        schema_formatter,
        example_formatter,
    ) -> Dict:
        """Generate SPARQL query from question and context."""
        prompt = self._build_prompt(
            question,
            entities,
            schema_context,
            examples,
            schema_formatter,
            example_formatter,
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=LLM_TEMPERATURE,
                max_completion_tokens=LLM_MAX_TOKENS,
            )

            raw_sparql = response.choices[0].message.content or ""
            sparql = self._clean_sparql(raw_sparql)
            confidence = self._estimate_confidence(sparql, entities)

            return {
                "sparql": sparql,
                "confidence": confidence,
                "raw_response": raw_sparql,
            }
        except Exception as e:
            return {
                "sparql": "",
                "confidence": 0.0,
                "error": str(e),
            }

    def _build_prompt(
        self,
        question: str,
        entities: List[Entity],
        schema_context: SchemaContext,
        examples: List[Example],
        schema_formatter,
        example_formatter,
    ) -> str:
        """Build complete prompt with all context."""
        parts = []

        parts.append(schema_formatter(schema_context))

        parts.append("\nENTITIES:")
        for entity in entities:
            parts.append(f"- {entity.mention}: <{entity.uri}> ({entity.entity_type})")

        if examples:
            parts.append("\n" + example_formatter(examples))

        parts.append(f"\nQUESTION:\n{question}")
        parts.append("\nGenerate SPARQL:")

        return "\n".join(parts)

    def _clean_sparql(self, sparql: str) -> str:
        """Clean and format SPARQL output."""
        sparql = re.sub(r"```sparql\n?", "", sparql)
        sparql = re.sub(r"```\n?", "", sparql)
        sparql = re.sub(r"^SPARQL:\s*", "", sparql, flags=re.IGNORECASE)
        sparql = " ".join(sparql.split())
        return sparql.strip()

    def _estimate_confidence(self, sparql: str, entities: List[Entity]) -> float:
        """Estimate confidence in generated SPARQL."""
        if not sparql:
            return 0.0

        confidence = 1.0

        for entity in entities:
            if entity.uri not in sparql:
                confidence -= 0.15

        if "SELECT" not in sparql.upper():
            confidence -= 0.2

        if sparql.count("{") != sparql.count("}"):
            confidence -= 0.3

        if "PREFIX" not in sparql.upper() and "dblp:" in sparql:
            confidence -= 0.1

        return max(0.0, min(1.0, confidence))

    def repair(
        self,
        sparql: str,
        error: str,
        question: str,
        entities: List[Entity],
        schema_context: SchemaContext,
        schema_formatter,
    ) -> str:
        """Attempt to repair a failed SPARQL query."""
        repair_prompt = f"""The following SPARQL query failed:

{sparql}

Error: {error}

Original question: {question}

Available entities:
{chr(10).join(f"- {e.mention}: <{e.uri}>" for e in entities)}

Fix the query. Return ONLY the corrected SPARQL, no explanation."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": repair_prompt},
                ],
                temperature=0.0,
                max_completion_tokens=LLM_MAX_TOKENS,
            )
            return self._clean_sparql(response.choices[0].message.content or "")
        except Exception:
            return sparql
