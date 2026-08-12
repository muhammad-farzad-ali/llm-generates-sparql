# Architecture Decision Record: LLM Provider

## Status

**Accepted**  
**Date**: 2025-01-15

## Context

We need to select an LLM provider for generating SPARQL queries from natural language questions about the DBLP knowledge graph.

## Decision

Use **OpenAI GPT-5.4-nano** as the primary LLM.

## Rationale

| Factor | GPT-5.4-nano | Alternatives |
|--------|--------------|--------------|
| Cost | $0.10/1M input, $0.625/1M output | GPT-5.4: $1.25/$7.50 |
| Latency | Fast (nano tier) | Slower for larger models |
| Context | Short context | Adequate for our prompts |
| SPARQL capability | Sufficient | Larger models overkill |

## Cost Analysis

For a typical query (500 input tokens, 200 output tokens):
- Input: 500 tokens × $0.10/1M = $0.00005
- Output: 200 tokens × $0.625/1M = $0.000125
- **Total per query: ~$0.000175** (~$0.18 per 1000 queries)

## Alternatives Considered

1. **GPT-5.4**: 12x more expensive, similar capability
2. **GPT-5.4-mini**: 3.75x more expensive, marginal improvement
3. **GPT-5.5**: 25x more expensive, overkill for this task
4. **Anthropic Claude**: Not selected per user preference

## Consequences

### Positive
- Very low cost per query
- Fast response times
- Adequate for structured SPARQL generation

### Negative
- Short context window may limit examples
- May need more retries than larger models
- Less capable for complex reasoning

## Mitigation

- Keep prompts concise (schema + 3-5 examples max)
- Implement repair loop for quality issues
- Monitor accuracy metrics closely
- Consider upgrading model if accuracy < 70%
