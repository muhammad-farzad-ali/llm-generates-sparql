# Coding Standards

## Python Style

- Follow PEP 8
- Use type hints for all function signatures
- Use docstrings for all public functions and classes
- Maximum line length: 100 characters

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Module | snake_case | `entity_linker.py` |
| Class | PascalCase | `EntityLinker` |
| Function | snake_case | `link_entity()` |
| Variable | snake_case | `entity_uri` |
| Constant | UPPER_SNAKE | `DBLP_ENDPOINT` |

## Type Hints

```python
from typing import List, Dict, Optional

def link_entity(mention: str, entity_type: Optional[str] = None) -> Dict[str, str]:
    """Link entity mention to DBLP URI."""
    pass
```

## Error Handling

```python
# Use specific exceptions
class EntityNotFoundError(Exception):
    pass

class InvalidSPARQLError(Exception):
    pass

# Always handle errors gracefully
try:
    result = await executor.execute(sparql)
except SPARQLWrapperException as e:
    logger.error(f"SPARQL execution failed: {e}")
    return {"success": False, "error": str(e)}
```

## Async/Await

- Use `async/await` for all I/O operations
- Use `asyncio.gather()` for parallel operations
- Use `asyncio.Semaphore()` for rate limiting

## Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Processing question: %s", question)
logger.error("Entity linking failed: %s", error)
```

## Testing

- Use `pytest` for all tests
- Use `pytest-asyncio` for async tests
- Aim for >80% coverage
- Test edge cases explicitly

```python
import pytest

@pytest.mark.asyncio
async def test_entity_linking_success():
    linker = EntityLinker()
    result = await linker.link("Michael Stonebraker")
    assert result["uri"] is not None

@pytest.mark.asyncio
async def test_entity_linking_not_found():
    linker = EntityLinker()
    with pytest.raises(EntityNotFoundError):
        await linker.link("NonexistentPerson12345")
```

## Documentation

- Every module must have a module docstring
- Every class must have a class docstring
- Every public function must have a function docstring
- Include usage examples in complex functions

## File Organization

```
src/
├── __init__.py
├── pipeline.py              # Main orchestrator
├── entity_linker.py         # Entity linking module
├── schema_retriever.py      # Schema retrieval module
├── example_retriever.py     # Example retrieval module
├── llm_generator.py         # LLM SPARQL generation
├── validator.py             # SPARQL validation
├── executor.py              # Query execution
├── models.py                # Pydantic data models
├── config.py                # Configuration management
└── utils.py                 # Shared utilities
```

## Dependencies

- Pin all dependency versions in `requirements.txt`
- Use virtual environments
- Document any system-level dependencies
