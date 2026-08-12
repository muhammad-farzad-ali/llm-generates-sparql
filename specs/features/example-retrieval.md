# Feature: Example Retrieval

## Purpose

Dynamically retrieve relevant few-shot examples (question → SPARQL pairs) to include in the LLM prompt, improving generation accuracy.

## User Story

As the LLM generating SPARQL,
I want to see 3-5 similar questions with their correct SPARQL queries,
So that I can follow the same patterns for the current question.

## Input/Output

**Input**:
```python
{
    "question": "Which papers did Michael Stonebraker publish at SIGMOD?",
    "k": 3  # number of examples to retrieve
}
```

**Output**:
```python
{
    "examples": [
        {
            "question": "Which papers did John Doe publish at VLDB?",
            "sparql": "SELECT ?pub ?title WHERE { ?pub dblp:authoredBy <https://dblp.org/pid/j/JohnDoe> . ?pub dblp:publishedInStream <https://dblp.org/conf/vldb> . ?pub dblp:title ?title . }",
            "similarity": 0.92
        },
        {
            "question": "What are the publications of Jane Smith at SIGMOD?",
            "sparql": "SELECT ?pub ?title WHERE { ?pub dblp:authoredBy <https://dblp.org/pid/j/JaneSmith> . ?pub dblp:publishedInStream <https://dblp.org/conf/sigmod> . ?pub dblp:title ?title . }",
            "similarity": 0.89
        }
    ]
}
```

## Implementation Steps

### Step 1: Create Example Corpus

```json
// data/examples.json
[
    {
        "id": 1,
        "question": "Which papers did Michael Stonebraker author?",
        "entities": ["Michael Stonebraker"],
        "query_type": "author_publications",
        "sparql": "SELECT ?pub ?title WHERE { ?pub dblp:authoredBy <https://dblp.org/pid/s/MichaelStonebraker> . ?pub dblp:title ?title . }"
    },
    {
        "id": 2,
        "question": "How many publications does Geoffrey Hinton have?",
        "entities": ["Geoffrey Hinton"],
        "query_type": "count_publications",
        "sparql": "SELECT (COUNT(?pub) AS ?count) WHERE { ?pub dblp:authoredBy <https://dblp.org/pid/h/GeoffreyHinton> . }"
    }
]
```

### Step 2: Set Up Vector Store

```python
# src/example_retriever.py

import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import json

class ExampleRetriever:
    def __init__(self, examples_path: str):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = chromadb.Client()
        self.collection = self.client.create_collection("examples")
        self._load_examples(examples_path)
    
    def _load_examples(self, path: str):
        """Load examples into vector store."""
        with open(path) as f:
            examples = json.load(f)
        
        questions = [ex["question"] for ex in examples]
        embeddings = self.model.encode(questions).tolist()
        
        self.collection.add(
            documents=questions,
            embeddings=embeddings,
            ids=[str(ex["id"]) for ex in examples],
            metadatas=[{"sparql": ex["sparql"], "query_type": ex["query_type"]} 
                      for ex in examples]
        )
    
    def retrieve(self, question: str, k: int = 3) -> List[Dict]:
        """Retrieve k most similar examples."""
        embedding = self.model.encode(question).tolist()
        
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=k
        )
        
        examples = []
        for i in range(len(results["ids"][0])):
            examples.append({
                "question": results["documents"][0][i],
                "sparql": results["metadatas"][0][i]["sparql"],
                "similarity": 1 - results["distances"][0][i]
            })
        
        return examples
```

### Step 3: Implement Query Type Classification

```python
# Classify questions into types for better retrieval
QUERY_TYPES = {
    "author_publications": ["papers by", "publications of", "authored by"],
    "count_publications": ["how many", "number of", "count"],
    "venue_publications": ["papers at", "published in", "appeared in"],
    "co_authors": ["co-authors", "collaborated with"],
    "year_filter": ["after", "before", "since", "in year"]
}
```

### Step 4: Format Examples for Prompt

```python
def format_examples_for_prompt(self, examples: List[Dict]) -> str:
    """Format examples as clean text for LLM prompt."""
    prompt = "EXAMPLES:\n\n"
    
    for i, ex in enumerate(examples, 1):
        prompt += f"Example {i}:\n"
        prompt += f"Question: {ex['question']}\n"
        prompt += f"SPARQL:\n{ex['sparql']}\n\n"
    
    return prompt
```

## Example Categories to Include

| Category | Count | Example Question |
|----------|-------|------------------|
| Author publications | 10 | "Papers by X" |
| Count publications | 5 | "How many papers did X publish?" |
| Venue publications | 10 | "Papers at SIGMOD" |
| Year filtering | 10 | "Papers after 2020" |
| Co-authors | 5 | "Who collaborated with X?" |
| Title search | 5 | "Papers about machine learning" |
| Multi-hop | 5 | "Co-authors of X who also published at Y" |

## Edge Cases

1. **No similar examples**: Return empty list, system still works
2. **Low similarity**: Include examples with similarity > 0.7 only
3. **Too many examples**: Cap at 5 to save prompt space

## Acceptance Criteria

- [ ] Loads 50+ examples into vector store
- [ ] Retrieves semantically similar examples
- [ ] Returns examples sorted by similarity
- [ ] Formats examples cleanly for prompt
- [ ] Retrieval latency < 100ms
