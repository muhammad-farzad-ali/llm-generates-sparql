# Option 3: RAG for Semantic Search

## Goal

Implement proper Retrieval-Augmented Generation (RAG) with vector embeddings for:
1. **Example retrieval** - semantically similar question/SPARQL pairs
2. **Schema retrieval** - relevant classes/predicates for the question
3. **Entity discovery** - semantically similar entities from DBLP

## Current Problem

Example retrieval uses simple keyword overlap:

```python
# src/example_retriever.py lines 126-129
question_words = set(question_lower.split())
ex_words = set(ex_lower.split())
overlap = len(question_words & ex_words)
score = overlap / max(len(question_words), 1)
```

This fails for semantically similar but lexically different questions:
- "Who wrote X?" vs "Papers authored by X"
- "Conference papers" vs "Inproceedings"

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    RAG Pipeline                          │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Example  │  │ Schema   │  │ Entity   │             │
│  │ Index    │  │ Index    │  │ Index    │             │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│       │              │              │                   │
│       ▼              ▼              ▼                   │
│  ┌──────────────────────────────────────┐              │
│  │         ChromaDB Vector Store        │              │
│  └──────────────────┬───────────────────┘              │
│                     │                                   │
│                     ▼                                   │
│  ┌──────────────────────────────────────┐              │
│  │     Semantic Search (cosine sim)     │              │
│  └──────────────────┬───────────────────┘              │
│                     │                                   │
│                     ▼                                   │
│  ┌──────────────────────────────────────┐              │
│  │            LLM Generator             │              │
│  └──────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

## What Changes

### New File: `src/rag_index.py`

```python
"""RAG index with vector embeddings for semantic search."""

import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict

class RAGIndex:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = chromadb.Client()
        
        # Create collections
        self.examples = self.client.create_collection("examples")
        self.schema = self.client.create_collection("schema")
        self.entities = self.client.create_collection("entities")
    
    def index_examples(self, examples: List[Dict]):
        """Embed and index example questions + SPARQL."""
        texts = [ex["question"] for ex in examples]
        embeddings = self.model.encode(texts).tolist()
        
        self.examples.add(
            documents=texts,
            embeddings=embeddings,
            ids=[str(ex["id"]) for ex in examples],
            metadatas=[{"sparql": ex["sparql"], "query_type": ex["query_type"]} 
                      for ex in examples]
        )
    
    def index_schema(self, classes, properties):
        """Embed and index schema elements."""
        texts = []
        for cls in classes:
            texts.append(f"class {cls.label}: {cls.description}")
        for prop in properties:
            texts.append(f"property {prop.label}: {prop.description}")
        
        embeddings = self.model.encode(texts).tolist()
        
        self.schema.add(
            documents=texts,
            embeddings=embeddings,
            ids=[f"schema_{i}" for i in range(len(texts))],
            metadatas=[{"type": "class" if i < len(classes) else "property"} 
                      for i in range(len(texts))]
        )
    
    def index_entities(self, entities: List[Dict]):
        """Embed and index DBLP entities."""
        texts = [f"{e['name']} ({e['type']})" for e in entities]
        embeddings = self.model.encode(texts).tolist()
        
        self.entities.add(
            documents=texts,
            embeddings=embeddings,
            ids=[e["uri"] for e in entities],
            metadatas=[{"uri": e["uri"], "type": e["type"]} for e in entities]
        )
    
    def search_examples(self, query: str, k: int = 3):
        """Retrieve semantically similar examples."""
        embedding = self.model.encode([query]).tolist()
        results = self.examples.query(query_embeddings=embedding, n_results=k)
        return results
    
    def search_schema(self, query: str, k: int = 10):
        """Retrieve relevant schema elements."""
        embedding = self.model.encode([query]).tolist()
        results = self.schema.query(query_embeddings=embedding, n_results=k)
        return results
    
    def search_entities(self, query: str, k: int = 5):
        """Retrieve similar entities."""
        embedding = self.model.encode([query]).tolist()
        results = self.entities.query(query_embeddings=embedding, n_results=k)
        return results
```

### Modified File: `src/example_retriever.py`

```python
class ExampleRetriever:
    def __init__(self):
        self.rag_index = RAGIndex()
        self._load_and_index_examples()
    
    def retrieve(self, question: str, k: int = 3):
        """Semantic search instead of keyword overlap."""
        results = self.rag_index.search_examples(question, k)
        return self._format_results(results)
```

### Modified File: `src/schema_retriever.py`

```python
class SchemaRetriever:
    def __init__(self):
        self.rag_index = RAGIndex()
        self._load_and_index_schema()
    
    def get_relevant_schema(self, question: str, entity_types=None):
        """Semantic search for relevant schema elements."""
        results = self.rag_index.search_schema(question, k=20)
        return self._format_schema_context(results)
```

### Modified File: `src/pipeline.py`

```python
class Pipeline:
    def convert(self, request):
        # 1. Extract entities
        entities = self._extract_entities(request.question)
        
        # 2. RAG: Retrieve relevant schema
        schema_context = self.schema_retriever.get_relevant_schema(
            question=request.question  # Pass question for semantic search
        )
        
        # 3. RAG: Retrieve similar examples
        examples = self.example_retriever.retrieve(
            question=request.question, k=3
        )
        
        # 4. Generate SPARQL
        ...
```

### New Dependencies: `requirements.txt`

```
chromadb>=0.4.0
sentence-transformers>=2.2.0
```

## New File: `data/dblp_entities.json`

```json
[
  {"name": "Michael Stonebraker", "uri": "https://dblp.org/pid/s/MichaelStonebraker", "type": "Person"},
  {"name": "Geoffrey Hinton", "uri": "https://dblp.org/pid/10/3248", "type": "Person"},
  ...
]
```

This file is indexed at startup for entity semantic search.

## What Stays the Same

- `KNOWN_PERSON_URIS` and `KNOWN_VENUE_URIS` can stay or be removed
- `DBLP_KEY_CLASSES` and `DBLP_KEY_PREDICATES` can stay or be removed
- Entity linker can use RAG or remain unchanged
- LLM generator unchanged

## Benefits

| Benefit | Description |
|---------|-------------|
| Better accuracy | Semantic similarity > keyword overlap |
| Handles synonyms | "authored by" matches "written by" |
| Ambiguity resolution | Better entity matching |
| Scalable | Can index 1000s of examples |

## Risks

| Risk | Mitigation |
|------|------------|
| Slower cold start | Index once, cache in memory |
| Larger memory footprint | Use `all-MiniLM-L6-v2` (small model) |
| New dependency | Pin versions in requirements.txt |
| Embedding quality | Use proven model (MiniLM) |

## Implementation Steps

1. Add `chromadb` and `sentence-transformers` to `requirements.txt`
2. Create `src/rag_index.py` with RAGIndex class
3. Modify `src/example_retriever.py` to use RAGIndex
4. Modify `src/schema_retriever.py` to use RAGIndex
5. Modify `src/pipeline.py` to pass question for semantic search
6. Create `data/dblp_entities.json` with known entities
7. Test retrieval accuracy
8. Commit and push

## Testing

```bash
# Install new dependencies
pip install chromadb sentence-transformers

# Start server
python main.py

# Test semantic search
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Who authored the paper about neural networks?"}'

# Should retrieve semantically similar examples
# Should retrieve relevant schema elements
```

## Success Criteria

- [ ] ChromaDB indexes examples at startup
- [ ] Semantic search returns relevant examples
- [ ] Schema retrieval returns relevant predicates
- [ ] Latency < 500ms for retrieval
- [ ] Existing queries still work
