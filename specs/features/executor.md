# Feature: Executor & Repair

## Purpose

Execute validated SPARQL queries against the DBLP endpoint and automatically repair failed queries using LLM feedback.

## User Story

As a user asking a question,
I want the system to execute my query and return results,
And if the query fails, I want it to automatically try to fix it.

## Input/Output

**Input**:
```python
{
    "sparql": "SELECT ?pub ?title WHERE { ?pub dblp:authoredBy <https://dblp.org/pid/s/MichaelStonebraker> . ?pub dblp:title ?title . }",
    "max_retries": 3
}
```

**Output (success)**:
```python
{
    "success": True,
    "results": [
        {"pub": "https://dblp.org/rec/...", "title": "The Design of PostgreSQL"},
        {"pub": "https://dblp.org/rec/...", "title": "Ingres"}
    ],
    "attempts": 1,
    "final_sparql": "SELECT ?pub ?title WHERE { ?pub dblp:authoredBy <https://dblp.org/pid/s/MichaelStonebraker> . ?pub dblp:title ?title . }"
}
```

**Output (failure with repair)**:
```python
{
    "success": True,
    "results": [...],
    "attempts": 2,
    "final_sparql": "...",  # Repaired query
    "repair_history": [
        {"attempt": 1, "error": "Unknown predicate dblp:author", "fixed": "Changed to dblp:authoredBy"}
    ]
}
```

## Implementation Steps

### Step 1: SPARQL Executor

```python
# src/executor.py

from SPARQLWrapper import SPARQLWrapper, JSON
from typing import Dict, List, Optional
import time

class SPARQLExecutor:
    def __init__(self, endpoint: str = "https://sparql.dblp.org/sparql"):
        self.endpoint = endpoint
        self.sparql = SPARQLWrapper(endpoint)
        self.sparql.setReturnFormat(JSON)
    
    async def execute(self, sparql: str) -> Dict:
        """Execute SPARQL query against endpoint."""
        try:
            self.sparql.setQuery(sparql)
            results = self.sparql.query().convert()
            
            return {
                "success": True,
                "results": self._parse_results(results),
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "results": [],
                "error": str(e)
            }
    
    def _parse_results(self, results: Dict) -> List[Dict]:
        """Parse SPARQL JSON results into list of dicts."""
        parsed = []
        
        if "results" in results:
            for binding in results["results"]["bindings"]:
                row = {}
                for var, value in binding.items():
                    row[var] = value["value"]
                parsed.append(row)
        
        return parsed
```

### Step 2: Result Verifier

```python
class ResultVerifier:
    def verify_results(
        self,
        results: List[Dict],
        question: str,
        expected_type: str = None
    ) -> Dict:
        """Verify results are reasonable."""
        issues = []
        
        # Check for empty results
        if len(results) == 0:
            issues.append("Query returned no results")
        
        # Check for suspiciously large results
        if len(results) > 1000:
            issues.append(f"Query returned {len(results)} results, may be too broad")
        
        # Check for expected type patterns
        if expected_type == "count":
            if len(results) != 1 or "count" not in results[0]:
                issues.append("Count query should return single numeric result")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
```

### Step 3: Repair Module

```python
class QueryRepairer:
    def __init__(self, llm_generator):
        self.llm = llm_generator
    
    async def repair(
        self,
        original_sparql: str,
        error: str,
        question: str,
        entities: List[Dict],
        schema: Dict
    ) -> str:
        """Attempt to repair failed SPARQL query."""
        
        prompt = f"""The following SPARQL query failed:

{original_sparql}

Error: {error}

Original question: {question}

Fix the query. Return ONLY the corrected SPARQL, no explanation.
Use the same entities and schema as before.
"""
        
        response = await self.llm.generate(
            question=prompt,
            entities=entities,
            schema=schema,
            examples=[]
        )
        
        return response["sparql"]
```

### Step 4: Complete Pipeline with Retry

```python
class ExecutorWithRepair:
    def __init__(self, executor, verifier, repairer, max_retries: int = 3):
        self.executor = executor
        self.verifier = verifier
        self.repairer = repairer
        self.max_retries = max_retries
    
    async def execute_and_repair(
        self,
        sparql: str,
        question: str,
        entities: List[Dict],
        schema: Dict
    ) -> Dict:
        """Execute query with automatic repair on failure."""
        
        current_sparql = sparql
        repair_history = []
        
        for attempt in range(1, self.max_retries + 1):
            # Execute
            result = await self.executor.execute(current_sparql)
            
            if result["success"]:
                # Verify results
                verification = self.verifier.verify_results(
                    result["results"], question
                )
                
                if verification["valid"]:
                    return {
                        "success": True,
                        "results": result["results"],
                        "attempts": attempt,
                        "final_sparql": current_sparql,
                        "repair_history": repair_history
                    }
                else:
                    error = "; ".join(verification["issues"])
            else:
                error = result["error"]
            
            # Attempt repair
            if attempt < self.max_retries:
                repaired = await self.repairer.repair(
                    current_sparql, error, question, entities, schema
                )
                
                repair_history.append({
                    "attempt": attempt,
                    "error": error,
                    "original": current_sparql,
                    "repaired": repaired
                })
                
                current_sparql = repaired
        
        # All retries exhausted
        return {
            "success": False,
            "results": [],
            "attempts": self.max_retries,
            "final_sparql": current_sparql,
            "repair_history": repair_history,
            "error": "Max retries exhausted"
        }
```

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Unknown predicate` | Typo or wrong predicate | Use correct DBLP predicate |
| `Timeout` | Query too complex | Simplify or add LIMIT |
| `Malformed query` | Syntax error | Fix syntax |
| `Empty results` | Wrong entity URI | Verify entity linking |
| `Too many results` | Missing filters | Add FILTER conditions |

## DBLP Endpoint Quirks

```python
# DBLP endpoint has some limitations:
# 1. Rate limiting: ~1 request per second
# 2. Timeout: Complex queries may timeout
# 3. Result limit: Max 10000 results

# Add delays between requests
await asyncio.sleep(1)
```

## Edge Cases

1. **Endpoint down**: Return error, don't retry indefinitely
2. **Rate limited**: Wait and retry
3. **Timeout**: Simplify query or add LIMIT
4. **Invalid repair**: Track repair attempts, stop if not improving

## Acceptance Criteria

- [ ] Executes SPARQL against DBLP endpoint
- [ ] Parses JSON results correctly
- [ ] Catches and reports execution errors
- [ ] Attempts repair on failure
- [ ] Limits retry attempts
- [ ] Returns complete execution history
- [ ] Handles rate limiting gracefully
