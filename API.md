# DBLP Text-to-SPARQL API Documentation

## Overview

This service converts natural language questions about computer science publications into SPARQL queries for the [DBLP Computer Science Bibliography](https://dblp.org/).

**Base URL**: `http://localhost:8000`  
**Version**: 1.0  
**Format**: JSON

---

## Authentication

No authentication required. This is an internal service.

---

## CORS

Cross-Origin Resource Sharing (CORS) is enabled for all origins:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

You can call this API from any web application, regardless of the domain.

---

## Endpoints

### 1. Health Check

Check if the service is running and healthy.

```
GET /health
```

**Response**:
```json
{
  "status": "ok",
  "schema_loaded": true,
  "examples_count": 12
}
```

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Service status (`ok` or `error`) |
| `schema_loaded` | boolean | Whether DBLP schema is loaded |
| `examples_count` | integer | Number of few-shot examples available |

---

### 2. Convert Natural Language to SPARQL

Convert a natural language question into a SPARQL query.

```
POST /api/v1/query
```

**Request Body**:
```json
{
  "question": "Which papers did Michael Stonebraker author?",
  "execute": false,
  "max_retries": 2
}
```

**Fields**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `question` | string | Yes | - | Natural language question about DBLP |
| `execute` | boolean | No | `false` | Whether to execute the query against DBLP |
| `max_retries` | integer | No | `2` | Max repair attempts if query fails (0-5) |

**Response**:
```json
{
  "question": "Which papers did Michael Stonebraker author?",
  "sparql": "PREFIX dblp: <https://dblp.org/rdf/schema#> SELECT ?pub ?title WHERE { ?pub dblp:authoredBy <https://dblp.org/pid/s/MichaelStonebraker> . ?pub dblp:title ?title . }",
  "confidence": 1.0,
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": [],
    "triples": [
      {
        "subject": "?pub",
        "predicate": "dblp:authoredBy",
        "object": "<https://dblp.org/pid/s/MichaelStonebraker>"
      }
    ]
  },
  "entities": [
    {
      "mention": "Michael Stonebraker",
      "uri": "https://dblp.org/pid/s/MichaelStonebraker",
      "label": "Michael Stonebraker",
      "entity_type": "Person",
      "confidence": 1.0
    }
  ],
  "results": null,
  "attempts": 1,
  "repair_history": [],
  "error": null
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `question` | string | Original question |
| `sparql` | string | Generated SPARQL query |
| `confidence` | float | Confidence score (0.0 - 1.0) |
| `validation` | object | Validation results |
| `validation.valid` | boolean | Whether query is valid |
| `validation.errors` | array | Validation errors |
| `validation.warnings` | array | Validation warnings |
| `validation.triples` | array | Extracted triple patterns |
| `entities` | array | Linked entities |
| `results` | array/null | Query results (if `execute=true`) |
| `attempts` | integer | Number of attempts |
| `repair_history` | array | Repair attempts history |
| `error` | string/null | Error message if failed |

---

### 3. Get DBLP Schema

Retrieve the DBLP schema context used for SPARQL generation.

```
GET /api/v1/schema
```

**Response**:
```json
{
  "classes": [
    {
      "iri": "https://dblp.org/rdf/schema#Person",
      "label": "Person",
      "description": "An actual person, who is a creator of a publication"
    }
  ],
  "properties": [
    {
      "iri": "https://dblp.org/rdf/schema#authoredBy",
      "label": "authoredBy",
      "description": "The publication is authored by the creator",
      "domain": "https://dblp.org/rdf/schema#Publication",
      "range": "https://dblp.org/rdf/schema#Creator"
    }
  ]
}
```

---

### 4. Get Examples

Retrieve available few-shot examples for SPARQL generation.

```
GET /api/v1/examples
```

**Response**:
```json
{
  "count": 12,
  "examples": [
    {
      "id": 1,
      "question": "Which papers did Michael Stonebraker author?",
      "sparql": "SELECT ?pub ?title WHERE { ... }",
      "query_type": "author_publications",
      "similarity": 0.0
    }
  ]
}
```

---

## Example Usage

### cURL

```bash
# Health check
curl http://localhost:8000/health

# Convert question to SPARQL
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Which papers did Michael Stonebraker author?"}'

# Execute query against DBLP
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many papers were published at SIGMOD 2023?", "execute": true}'

# Get schema
curl http://localhost:8000/api/v1/schema

# Get examples
curl http://localhost:8000/api/v1/examples
```

### JavaScript (Fetch)

```javascript
// Convert question to SPARQL
const response = await fetch('http://localhost:8000/api/v1/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: "Which papers did Michael Stonebraker author?",
    execute: true
  })
});

const data = await response.json();
console.log(data.sparql);
console.log(data.results);
```

### Python (requests)

```python
import requests

# Convert question to SPARQL
response = requests.post(
    'http://localhost:8000/api/v1/query',
    json={
        'question': 'Which papers did Michael Stonebraker author?',
        'execute': True
    }
)

data = response.json()
print(data['sparql'])
print(data['results'])
```

### React / Frontend

```javascript
import { useState } from 'react';

function App() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const response = await fetch('http://localhost:8000/api/v1/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: query, execute: true })
    });
    const data = await response.json();
    setResult(data);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask about DBLP..."
      />
      <button type="submit">Search</button>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </form>
  );
}
```

---

## Supported Query Types

| Query Type | Example |
|------------|---------|
| Author publications | "Papers by Michael Stonebraker" |
| Venue publications | "Papers at SIGMOD 2023" |
| Co-authors | "Who are the co-authors of Yann LeCun?" |
| Publication count | "How many papers does Geoffrey Hinton have?" |
| Venue count | "How many papers at SIGMOD 2023?" |
| Keyword search | "Papers about machine learning" |
| DOI lookup | "DOI of paper titled 'Attention Is All You Need'" |
| List venues | "List all journals in DBLP" |
| Top publications | "Top 5 publications at SIGIR" |

---

## DBLP Entity Types

### Persons

| Name | URI |
|------|-----|
| Michael Stonebraker | `https://dblp.org/pid/s/MichaelStonebraker` |
| Donald E. Knuth | `https://dblp.org/pid/k/DonaldEKnuth` |
| Geoffrey Hinton | `https://dblp.org/pid/10/3248` |
| Yann LeCun | `https://dblp.org/pid/l/YannLeCun` |
| Christos Faloutsos | `https://dblp.org/pid/f/CFaloutsos` |
| Jiawei Han | `https://dblp.org/pid/h/JiaweiHan` |
| Jennifer Widom | `https://dblp.org/pid/w/JenniferWidom` |
| Hector Garcia-Molina | `https://dblp.org/pid/g/HGarciaMolina` |

### Venues

| Name | URI |
|------|-----|
| SIGMOD | `https://dblp.org/streams/conf/sigmod` |
| VLDB | `https://dblp.org/streams/conf/vldb` |
| SIGIR | `https://dblp.org/streams/conf/sigir` |
| KDD | `https://dblp.org/streams/conf/kdd` |
| ICDE | `https://dblp.org/streams/conf/icde` |
| PODS | `https://dblp.org/streams/conf/pods` |
| EDBT | `https://dblp.org/streams/conf/edbt` |
| CIDR | `https://dblp.org/streams/conf/cidr` |
| TODS | `https://dblp.org/streams/journals/tods` |
| TKDE | `https://dblp.org/streams/journals/tkde` |
| PVLDB | `https://dblp.org/streams/journals/pvldb` |

---

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad request (invalid input) |
| 404 | Not found |
| 500 | Internal server error |

### Error Response

```json
{
  "detail": "Error message here"
}
```

---

## Rate Limits

No rate limits are currently enforced. However, please be mindful of:
- DBLP endpoint rate limits (when `execute=true`)
- OpenAI API rate limits (for LLM generation)

---

## Data Sources

- **DBLP RDF Schema**: https://dblp.org/rdf/docu/
- **DBLP SPARQL Endpoint**: https://sparql.dblp.org/sparql
- **DBLP Search API**: https://dblp.org/search/publ/api

---

## Support

For issues or questions, contact the development team or create an issue on GitHub:
https://github.com/muhammad-farzad-ali/llm-generates-sparql/issues
