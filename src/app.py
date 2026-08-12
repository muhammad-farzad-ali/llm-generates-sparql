"""FastAPI application for Text-to-SPARQL conversion."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import QueryRequest, QueryResponse, HealthResponse
from .pipeline import Pipeline

app = FastAPI(
    title="DBLP Text-to-SPARQL API",
    description="Convert natural language questions about DBLP to SPARQL queries",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline: Pipeline = None


def get_pipeline() -> Pipeline:
    global pipeline
    if pipeline is None:
        pipeline = Pipeline()
    return pipeline


@app.on_event("shutdown")
def shutdown_event():
    global pipeline
    if pipeline:
        pipeline.close()


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    p = get_pipeline()
    return HealthResponse(
        status="ok",
        schema_loaded=len(p.schema_retriever.classes) > 0,
        examples_count=len(p.example_retriever.examples),
    )


@app.post("/api/v1/query", response_model=QueryResponse)
def convert_to_sparql(request: QueryRequest):
    """Convert natural language question to SPARQL query."""
    try:
        p = get_pipeline()
        response = p.convert(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/schema")
def get_schema():
    """Get the DBLP schema context."""
    p = get_pipeline()
    context = p.schema_retriever.get_relevant_schema()
    return {
        "classes": [c.model_dump() for c in context.classes],
        "properties": [p.model_dump() for p in context.properties],
    }


@app.get("/api/v1/examples")
def get_examples():
    """Get available few-shot examples."""
    p = get_pipeline()
    return {
        "count": len(p.example_retriever.examples),
        "examples": [e.model_dump() for e in p.example_retriever.examples],
    }
