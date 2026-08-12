"""Executor: executes SPARQL queries against DBLP endpoint."""

import time
from typing import Dict, List, Optional
from SPARQLWrapper import SPARQLWrapper, JSON
from .config import DBLP_SPARQL_ENDPOINT


class SPARQLExecutor:
    """Executes SPARQL queries against the DBLP endpoint."""

    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or DBLP_SPARQL_ENDPOINT
        self.sparql = SPARQLWrapper(self.endpoint)
        self.sparql.setReturnFormat(JSON)

    def execute(self, query: str) -> Dict:
        """Execute a SPARQL query and return results."""
        try:
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()

            parsed = self._parse_results(results)

            return {
                "success": True,
                "results": parsed,
                "count": len(parsed),
                "error": None,
            }
        except Exception as e:
            return {
                "success": False,
                "results": [],
                "count": 0,
                "error": str(e),
            }

    def _parse_results(self, results: Dict) -> List[Dict]:
        """Parse SPARQL JSON results into list of dicts."""
        parsed = []

        if "results" in results:
            for binding in results["results"]["bindings"]:
                row = {}
                for var, value in binding.items():
                    row[var] = value.get("value", "")
                parsed.append(row)

        return parsed

    def verify_results(self, results: List[Dict], question: str) -> Dict:
        """Verify results are reasonable."""
        issues = []

        if len(results) == 0:
            issues.append("Query returned no results")
        elif len(results) > 1000:
            issues.append(f"Query returned {len(results)} results - may be too broad")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
        }
