# Feature: LLM SPARQL Generator

## Purpose

Generate correct SPARQL queries from natural language questions using OpenAI GPT-5.4-nano, grounded in DBLP schema and examples.

## User Story

As a user asking a question about DBLP,
I want the system to generate a correct SPARQL query,
So that I get accurate results from the DBLP Knowledge Graph.

## Input/Output

**Input**:
```python
{
    "question": "Which papers did Michael Stonebraker publish at SIGMOD after 2015?",
    "entities": [
        {"mention": "Michael Stonebraker", "uri": "https://dblp.org/pid/s/MichaelStonebraker", "type": "Person"},
        {"mention": "SIGMOD", "uri": "https://dblp.org/conf/sigmod", "type": "Conference"}
    ],
    "schema": {
        "classes": [...],
        "predicates": [...]
    },
    "examples": [...]
}
```

**Output**:
```python
{
    "sparql": "SELECT ?pub ?title ?year WHERE { ?pub dblp:authoredBy <https://dblp.org/pid/s/MichaelStonebraker> . ?pub dblp:publishedInStream <https://dblp.org/conf/sigmod> . ?pub dblp:title ?title . ?pub dblp:yearOfPublication ?year . FILTER(?year > \"2015\") }",
    "confidence": 0.85,
    "reasoning": "Used authoredBy for author, publishedInStream for venue, yearOfPublication for year filter"
}
```

## Implementation Steps

### Step 1: Design System Prompt

```python
# src/llm_generator.py

SYSTEM_PROMPT = """You are a SPARQL expert for the DBLP Computer Science Bibliography.

Your task: Convert natural language questions into correct SPARQL queries.

RULES:
1. Use ONLY predicates from the provided schema
2. Use the exact entity URIs provided
3. Use correct namespaces (PREFIX declarations)
4. Return ONLY the SPARQL query, no explanation
5. Use SELECT for queries that return results
6. Use FILTER for date/string filtering
7. Use COUNT/GROUP BY for aggregation queries

DBLP NAMESPACES:
PREFIX dblp: <https://dblp.org/rdf/schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""
```

### Step 2: Build User Prompt Template

```python
def build_prompt(
    self,
    question: str,
    entities: List[Dict],
    schema: Dict,
    examples: List[Dict]
) -> str:
    """Build complete prompt with all context."""
    
    prompt = SYSTEM_PROMPT + "\n\n"
    
    # Add schema
    prompt += "RELEVANT SCHEMA:\n"
    prompt += self.format_schema(schema) + "\n\n"
    
    # Add entities
    prompt += "ENTITIES:\n"
    for entity in entities:
        prompt += f"- {entity['mention']}: <{entity['uri']}> ({entity['type']})\n"
    prompt += "\n"
    
    # Add examples
    prompt += "EXAMPLES:\n"
    for i, ex in enumerate(examples, 1):
        prompt += f"Example {i}:\n"
        prompt += f"Question: {ex['question']}\n"
        prompt += f"SPARQL:\n{ex['sparql']}\n\n"
    
    # Add question
    prompt += f"QUESTION:\n{question}\n\n"
    prompt += "SPARQL:"
    
    return prompt
```

### Step 3: Implement LLM Client

```python
import openai
from typing import Dict, Optional
import re

class LLMGenerator:
    def __init__(self, api_key: str, model: str = "gpt-5.4-nano"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    async def generate(
        self,
        question: str,
        entities: List[Dict],
        schema: Dict,
        examples: List[Dict]
    ) -> Dict:
        """Generate SPARQL query from question and context."""
        
        prompt = self.build_prompt(question, entities, schema, examples)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,  # Deterministic for consistency
            max_tokens=500
        )
        
        sparql = response.choices[0].message.content
        sparql = self._clean_sparql(sparql)
        
        return {
            "sparql": sparql,
            "confidence": self._estimate_confidence(sparql, entities),
            "reasoning": self._extract_reasoning(response)
        }
    
    def _clean_sparql(self, sparql: str) -> str:
        """Clean and format SPARQL output."""
        # Remove markdown code blocks if present
        sparql = re.sub(r'```sparql\n?', '', sparql)
        sparql = re.sub(r'```\n?', '', sparql)
        
        # Remove extra whitespace
        sparql = ' '.join(sparql.split())
        
        return sparql.strip()
```

### Step 4: Implement Confidence Estimation

```python
def _estimate_confidence(self, sparql: str, entities: List[Dict]) -> float:
    """Estimate confidence in generated SPARQL."""
    confidence = 1.0
    
    # Check if all entity URIs are used
    for entity in entities:
        if entity["uri"] not in sparql:
            confidence -= 0.2
    
    # Check for common patterns
    if "SELECT" not in sparql:
        confidence -= 0.3
    
    # Check for balanced braces
    if sparql.count("{") != sparql.count("}"):
        confidence -= 0.5
    
    return max(0.0, min(1.0, confidence))
```

## Query Patterns to Support

| Pattern | Example | SPARQL Template |
|---------|---------|-----------------|
| Author publications | "Papers by X" | `?pub dblp:authoredBy <X>` |
| Venue publications | "Papers at Y" | `?pub dblp:publishedInStream <Y>` |
| Year filter | "Papers after 2020" | `?pub dblp:yearOfPublication ?year . FILTER(?year > "2020")` |
| Count | "How many papers" | `SELECT (COUNT(?pub) AS ?count)` |
| Co-authors | "Who collaborated with X" | `?pub dblp:authoredBy <X> . ?pub dblp:authoredBy ?coauthor` |

## Edge Cases

1. **Ambiguous question**: Generate best guess, let validator catch issues
2. **Missing entity**: Return error message, don't hallucinate URI
3. **Complex query**: Break into simpler patterns if possible
4. **LLM returns explanation**: Extract only the SPARQL part

## Testing

```python
# tests/test_llm_generator.py

async def test_simple_author_query():
    generator = LLMGenerator(api_key="test")
    result = await generator.generate(
        question="Which papers did Michael Stonebraker author?",
        entities=[{"mention": "Michael Stonebraker", "uri": "https://dblp.org/pid/s/MichaelStonebraker", "type": "Person"}],
        schema={...},
        examples=[...]
    )
    assert "dblp:authoredBy" in result["sparql"]
    assert "MichaelStonebraker" in result["sparql"]
```

## Acceptance Criteria

- [ ] Generates syntactically valid SPARQL
- [ ] Uses correct DBLP predicates from schema
- [ ] Uses exact entity URIs provided
- [ ] Includes proper PREFIX declarations
- [ ] Handles common query patterns (author, venue, year, count)
- [ ] Returns confidence score
- [ ] Temperature set to 0.0 for consistency
