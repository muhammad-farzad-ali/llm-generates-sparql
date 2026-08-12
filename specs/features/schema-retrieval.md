# Feature: Schema Retrieval

## Purpose

Given a natural language question and linked entities, retrieve the relevant DBLP schema triples (classes, predicates, domain/range) needed to generate correct SPARQL.

## User Story

As the LLM generating SPARQL,
I want to receive only the relevant schema information for the current question,
So that I use the correct predicates and avoid hallucinating invalid ones.

## Input/Output

**Input**:
```python
{
    "question": "Which papers did Michael Stonebraker publish at SIGMOD?",
    "entities": [
        {"uri": "...", "type": "Person"},
        {"uri": "...", "type": "Conference"}
    ]
}
```

**Output**:
```python
{
    "classes": [
        {"iri": "dblp:Person", "description": "An actual person (author/creator)"},
        {"iri": "dblp:Publication", "description": "A publication"},
        {"iri": "dblp:Inproceedings", "description": "A conference paper"},
        {"iri": "dblp:Conference", "description": "A conference series"}
    ],
    "predicates": [
        {
            "iri": "dblp:authoredBy",
            "domain": "dblp:Publication",
            "range": "dblp:Creator",
            "description": "The publication is authored by the creator"
        },
        {
            "iri": "dblp:publishedInStream",
            "domain": "dblp:Publication",
            "range": "dblp:Stream",
            "description": "The publication is published in a stream"
        },
        {
            "iri": "dblp:title",
            "domain": "dblp:Publication",
            "range": "xsd:string",
            "description": "The title of the publication"
        }
    ]
}
```

## Implementation Steps

### Step 1: Parse DBLP Schema

```python
# src/schema_retriever.py

from rdflib import Graph, RDF, RDFS, OWL
from typing import List, Dict
import json

class SchemaRetriever:
    def __init__(self, schema_path: str):
        self.graph = Graph()
        self.graph.parse(schema_path, format="turtle")
        self.classes = self._extract_classes()
        self.predicates = self._extract_predicates()
    
    def _extract_classes(self) -> List[Dict]:
        """Extract all classes from schema."""
        classes = []
        for s in self.graph.subjects(RDF.type, OWL.Class):
            label = self.graph.value(s, RDFS.label)
            comment = self.graph.value(s, RDFS.comment)
            classes.append({
                "iri": str(s),
                "label": str(label) if label else "",
                "description": str(comment) if comment else ""
            })
        return classes
    
    def _extract_predicates(self) -> List[Dict]:
        """Extract all properties with domain/range."""
        predicates = []
        for s in self.graph.subjects(RDF.type, OWL.ObjectProperty):
            label = self.graph.value(s, RDFS.label)
            comment = self.graph.value(s, RDFS.comment)
            domain = self.graph.value(s, RDFS.domain)
            range_ = self.graph.value(s, RDFS.range)
            predicates.append({
                "iri": str(s),
                "label": str(label) if label else "",
                "description": str(comment) if comment else "",
                "domain": str(domain) if domain else None,
                "range": str(range_) if range_ else None
            })
        return predicates
```

### Step 2: Build Semantic Index

```python
# Index schema elements for semantic search
# Use sentence-transformers to embed descriptions
# Store in ChromaDB for retrieval
```

### Step 3: Implement Relevance Scoring

```python
async def retrieve_relevant_schema(
    self, 
    question: str, 
    entity_types: List[str]
) -> Dict:
    """Retrieve schema elements relevant to the question."""
    
    # 1. Get predicates that connect the entity types
    relevant_predicates = []
    for pred in self.predicates:
        if pred["domain"] in entity_types or pred["range"] in entity_types:
            relevant_predicates.append(pred)
    
    # 2. Semantic search for additional relevant predicates
    # ... embed question, find similar predicate descriptions ...
    
    # 3. Return filtered schema
    return {
        "classes": [c for c in self.classes if c["iri"] in entity_types],
        "predicates": relevant_predicates
    }
```

### Step 4: Format for LLM Prompt

```python
def format_schema_for_prompt(self, schema: Dict) -> str:
    """Format schema as clean text for LLM prompt."""
    prompt = "DBLP SCHEMA:\n\n"
    
    prompt += "Classes:\n"
    for cls in schema["classes"]:
        prompt += f"- {cls['iri']}: {cls['description']}\n"
    
    prompt += "\nPredicates:\n"
    for pred in schema["predicates"]:
        prompt += f"- {pred['iri']}\n"
        prompt += f"  Domain: {pred['domain']}\n"
        prompt += f"  Range: {pred['range']}\n"
        prompt += f"  Description: {pred['description']}\n"
    
    return prompt
```

## Key DBLP Predicates to Include

| Predicate | Domain | Range | Use Case |
|-----------|--------|-------|----------|
| `dblp:authoredBy` | Publication | Creator | Author queries |
| `dblp:authorOf` | Creator | Publication | Author queries (inverse) |
| `dblp:title` | Publication | string | Title lookup |
| `dblp:yearOfPublication` | Publication | string | Year filtering |
| `dblp:publishedInStream` | Publication | Stream | Venue queries |
| `dblp:publishedInJournal` | Publication | Journal | Journal queries |
| `dblp:doi` | Publication | anyUri | DOI lookup |
| `dblp:creatorName` | Creator | string | Name matching |

## Edge Cases

1. **Predicate doesn't exist**: Don't include it, let validator catch
2. **Multiple predicates for same relation**: Include all, let LLM choose
3. **Inverse predicates**: Include both `authoredBy` and `authorOf`

## Acceptance Criteria

- [ ] Parses DBLP schema Turtle file correctly
- [ ] Returns relevant predicates for given entity types
- [ ] Formats schema cleanly for LLM prompt
- [ ] Includes domain/range information
- [ ] Handles missing schema elements gracefully
