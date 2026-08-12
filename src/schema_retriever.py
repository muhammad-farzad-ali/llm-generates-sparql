"""Schema retriever: extracts and provides DBLP schema context."""

from pathlib import Path
from typing import List, Optional
from rdflib import Graph, RDF, RDFS, OWL
from .models import SchemaClass, SchemaProperty, SchemaContext
from .config import SCHEMA_PATH


class SchemaRetriever:
    """Parses DBLP schema and provides relevant context for LLM."""

    def __init__(self, schema_path: Optional[Path] = None):
        self.schema_path = schema_path or SCHEMA_PATH
        self.graph = Graph()
        self.classes: List[SchemaClass] = []
        self.properties: List[SchemaProperty] = []
        self._load_schema()

    def _load_schema(self):
        """Load and parse the DBLP schema."""
        if not self.schema_path.exists():
            print(f"Warning: Schema file not found at {self.schema_path}")
            return

        self.graph.parse(str(self.schema_path), format="turtle")
        self._extract_classes()
        self._extract_properties()

    def _extract_classes(self):
        """Extract all classes from schema."""
        for s in self.graph.subjects(RDF.type, OWL.Class):
            label = self.graph.value(s, RDFS.label)
            comment = self.graph.value(s, RDFS.comment)
            iri = str(s)
            if "dblp.org/rdf/schema#" in iri:
                self.classes.append(
                    SchemaClass(
                        iri=iri,
                        label=str(label) if label else iri.split("#")[-1],
                        description=str(comment).split(".")[0] if comment else "",
                    )
                )

    def _extract_properties(self):
        """Extract all properties with domain/range."""
        for s in self.graph.subjects(RDF.type, RDF.Property):
            label = self.graph.value(s, RDFS.label)
            comment = self.graph.value(s, RDFS.comment)
            domain = self.graph.value(s, RDFS.domain)
            range_ = self.graph.value(s, RDFS.range)
            iri = str(s)
            if "dblp.org/rdf/schema#" in iri:
                self.properties.append(
                    SchemaProperty(
                        iri=iri,
                        label=str(label) if label else iri.split("#")[-1],
                        description=str(comment).split(".")[0] if comment else "",
                        domain=str(domain) if domain else None,
                        range=str(range_) if range_ else None,
                    )
                )

    def get_relevant_schema(
        self, entity_types: Optional[List[str]] = None
    ) -> SchemaContext:
        """Get schema context - returns ALL classes and properties from DBLP schema."""
        return SchemaContext(classes=self.classes, properties=self.properties)

    def format_for_prompt(self, context: SchemaContext) -> str:
        """Format schema context for LLM prompt."""
        lines = ["DBLP SCHEMA:", ""]

        lines.append("Classes:")
        for cls in context.classes:
            lines.append(f"  dblp:{cls.label} - {cls.description}")

        lines.append("")
        lines.append("Properties:")
        for prop in context.properties:
            domain = prop.domain.split("#")[-1] if prop.domain else "?"
            range_ = prop.range.split("#")[-1] if prop.range else "?"
            lines.append(f"  dblp:{prop.label}")
            lines.append(f"    Domain: {domain}")
            lines.append(f"    Range: {range_}")
            lines.append(f"    Description: {prop.description}")

        return "\n".join(lines)

    def get_property_by_name(self, name: str) -> Optional[SchemaProperty]:
        """Get a property by its short name."""
        for prop in self.properties:
            if prop.label == name:
                return prop
        return None
