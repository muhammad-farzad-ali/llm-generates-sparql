# Feature: SPARQL Validator

## Purpose

Validate generated SPARQL queries for syntax correctness, schema compliance, and type compatibility before execution.

## User Story

As the pipeline,
I want to catch invalid SPARQL before executing it,
So that I can repair it or fail fast without wasting API calls.

## Input/Output

**Input**:
```python
{
    "sparql": "SELECT ?pub WHERE { ?pub dblp:authoredBy <https://dblp.org/pid/s/MichaelStonebraker> }",
    "schema": {
        "predicates": [
            {"iri": "dblp:authoredBy", "domain": "Publication", "range": "Creator"}
        ]
    },
    "entities": [
        {"uri": "https://dblp.org/pid/s/MichaelStonebraker", "type": "Person"}
    ]
}
```

**Output**:
```python
{
    "valid": True,
    "errors": [],
    "warnings": [],
    "triples_extracted": [
        {"subject": "?pub", "predicate": "dblp:authoredBy", "object": "<https://dblp.org/pid/s/MichaelStonebraker>"}
    ]
}
```

## Validation Checks

### 1. Syntax Validation
```python
# Check if SPARQL is syntactically valid
# Use SPARQLWrapper or rdflib parser
```

### 2. Prefix Validation
```python
# Check all required prefixes are declared
REQUIRED_PREFIXES = {
    "dblp": "https://dblp.org/rdf/schema#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
}
```

### 3. Predicate Validation
```python
# Check all predicates exist in schema
def validate_predicates(sparql: str, schema_predicates: List[str]) -> List[str]:
    errors = []
    extracted_predicates = extract_predicates(sparql)
    for pred in extracted_predicates:
        if pred not in schema_predicates:
            errors.append(f"Unknown predicate: {pred}")
    return errors
```

### 4. Type Compatibility
```python
# Check domain/range compatibility
# e.g., authoredBy expects Publication → Person
# Error if used as: Person → authoredBy → Publication
```

### 5. Entity URI Validation
```python
# Check all provided entity URIs are used
# Check no hallucinated URIs are present
```

## Implementation Steps

### Step 1: Syntax Validator

```python
# src/validator.py

from SPARQLWrapper import SPARQLWrapper
from rdflib import Graph
import re
from typing import List, Dict

class SPARQLValidator:
    def validate_syntax(self, sparql: str) -> List[str]:
        """Validate SPARQL syntax."""
        errors = []
        
        try:
            # Try to parse with rdflib
            g = Graph()
            g.query(sparql)
        except Exception as e:
            errors.append(f"Syntax error: {str(e)}")
        
        return errors
```

### Step 2: Extract Triples

```python
def extract_triples(self, sparql: str) -> List[Dict]:
    """Extract triple patterns from SPARQL."""
    triples = []
    
    # Simple regex-based extraction
    # For production, use a proper SPARQL parser
    pattern = r'(\??\w+)\s+(dblp:\w+)\s+(<?[^>]+>?|\??\w+)'
    matches = re.findall(pattern, sparql)
    
    for match in matches:
        triples.append({
            "subject": match[0],
            "predicate": match[1],
            "object": match[2]
        })
    
    return triples
```

### Step 3: Predicate Validator

```python
def validate_predicates(
    self,
    triples: List[Dict],
    schema_predicates: List[str]
) -> List[str]:
    """Check all predicates exist in schema."""
    errors = []
    
    for triple in triples:
        predicate = triple["predicate"]
        # Normalize predicate format
        if not predicate.startswith("dblp:"):
            predicate = f"dblp:{predicate}"
        
        if predicate not in schema_predicates:
            errors.append(f"Unknown predicate: {predicate}")
    
    return errors
```

### Step 4: Type Compatibility Validator

```python
def validate_type_compatibility(
    self,
    triples: List[Dict],
    schema: Dict,
    entities: List[Dict]
) -> List[str]:
    """Check domain/range compatibility."""
    errors = []
    
    for triple in triples:
        pred_info = self.get_predicate_info(triple["predicate"], schema)
        if not pred_info:
            continue
        
        # Check domain
        subject_type = self.get_subject_type(triple["subject"], triples, entities)
        if subject_type and pred_info["domain"]:
            if not self.is_compatible(subject_type, pred_info["domain"]):
                errors.append(
                    f"Domain mismatch: {triple['predicate']} expects "
                    f"{pred_info['domain']}, got {subject_type}"
                )
        
        # Check range
        object_type = self.get_object_type(triple["object"], triples, entities)
        if object_type and pred_info["range"]:
            if not self.is_compatible(object_type, pred_info["range"]):
                errors.append(
                    f"Range mismatch: {triple['predicate']} expects "
                    f"{pred_info['range']}, got {object_type}"
                )
    
    return errors
```

### Step 5: Complete Validator

```python
async def validate(
    self,
    sparql: str,
    schema: Dict,
    entities: List[Dict]
) -> Dict:
    """Run all validation checks."""
    errors = []
    warnings = []
    
    # 1. Syntax check
    syntax_errors = self.validate_syntax(sparql)
    errors.extend(syntax_errors)
    
    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings}
    
    # 2. Extract triples
    triples = self.extract_triples(sparql)
    
    # 3. Prefix check
    prefix_errors = self.validate_prefixes(sparql)
    errors.extend(prefix_errors)
    
    # 4. Predicate check
    pred_names = [p["iri"] for p in schema.get("predicates", [])]
    pred_errors = self.validate_predicates(triples, pred_names)
    errors.extend(pred_errors)
    
    # 5. Type compatibility check
    type_errors = self.validate_type_compatibility(triples, schema, entities)
    errors.extend(type_errors)
    
    # 6. Entity URI check
    entity_errors = self.validate_entities(sparql, entities)
    warnings.extend(entity_errors)
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "triples_extracted": triples
    }
```

## Error Types

| Error | Severity | Example |
|-------|----------|---------|
| Syntax error | Error | Missing closing brace |
| Unknown predicate | Error | `dblp:nonExistent` |
| Domain mismatch | Error | Person used where Publication expected |
| Range mismatch | Error | String used where Person expected |
| Missing prefix | Warning | `PREFIX dblp:` not declared |
| Unused entity | Warning | Entity provided but not used |

## Edge Cases

1. **Empty SPARQL**: Return error immediately
2. **Multiple query forms**: Handle SELECT, CONSTRUCT, ASK
3. **Nested queries**: Validate subqueries recursively
4. **Optional patterns**: Don't validate OPTIONAL blocks strictly

## Acceptance Criteria

- [ ] Catches syntax errors
- [ ] Validates predicates against schema
- [ ] Checks domain/range compatibility
- [ ] Extracts triples correctly
- [ ] Returns clear error messages
- [ ] Handles all common SPARQL patterns
