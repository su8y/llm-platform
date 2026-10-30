"""Dependency-free ranking and bounded retrieval; IO is supplied by adapters."""

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class SearchScope:
    company_key: str
    file_id: int | None = None
    data_types: tuple[str, ...] = ()


@dataclass(frozen=True)
class SearchHit:
    # Stable chunk ID, shared by lexical and dense indexes.
    id: str
    company_key: str
    text: str
    file_id: int | None = None
    is_on: bool = True
    score: float = 0.0
    metadata: dict = field(default_factory=dict, compare=False)


def in_scope(hit: SearchHit, scope: SearchScope) -> bool:
    return bool(scope.company_key) and (
        hit.company_key == scope.company_key
        and hit.is_on
        and (scope.file_id is None or hit.file_id == scope.file_id)
        and (not scope.data_types or hit.metadata.get("data_type") in scope.data_types)
    )


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[SearchHit]],
    scope: SearchScope,
    limit: int = 10,
) -> list[SearchHit]:
    """Fuse ranks without comparing incompatible BM25/vector scores."""
    scores: dict[str, float] = {}
    hits: dict[str, SearchHit] = {}
    for ranking in rankings:
        seen = set()
        rank = 0
        for hit in ranking:
            if hit.id in seen or not in_scope(hit, scope):
                continue
            seen.add(hit.id)
            rank += 1
            hits.setdefault(hit.id, hit)
            scores[hit.id] = scores.get(hit.id, 0.0) + 1.0 / (60 + rank)
    result = []
    for key in sorted(scores, key=lambda key: (-scores[key], key))[:max(0, limit)]:
        hit = hits[key]
        result.append(replace(hit, score=scores[key]))
    return result


Search = Callable[[str, SearchScope, int], Awaitable[list[SearchHit]]]
Refine = Callable[[str, Sequence[SearchHit]], Awaitable[str | None]]
Enough = Callable[[Sequence[SearchHit]], bool]


async def retrieve(
    question: str,
    scope: SearchScope,
    dense_search: Search,
    lexical_search: Search,
    refine: Refine | None = None,
    enough: Enough | None = None,
    limit: int = 10,
    timeout: float = 15.0,
) -> list[SearchHit]:
    """Search original query first, optionally refine once, preserve both.

    Adapters MUST apply scope before searching (defense-in-depth filtering is
    also performed here). LLM refinement belongs in an llm-proxy adapter; this
    module does not import vendor SDKs. Errors/cancellation propagate; an IO
    outage must not silently become an empty knowledge base. The timeout
    covers both rounds and refinement together.
    """
    if not question.strip() or not scope.company_key or limit <= 0:
        return []
    async with asyncio.timeout(timeout):
        async def search(query: str) -> list[list[SearchHit]]:
            tasks = [asyncio.create_task(backend(query, scope, limit))
                     for backend in (dense_search, lexical_search)]
            try:
                return await asyncio.gather(*tasks)
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)

        rankings = await search(question)
        results = reciprocal_rank_fusion(rankings, scope, limit)
        sufficient = enough(results) if enough is not None else bool(results)
        if refine is None or sufficient:
            return results
        rewritten = await refine(question, results)
        if rewritten is None or not rewritten.strip():
            return results
        rewritten = rewritten.strip()
        if rewritten.casefold() == question.strip().casefold():
            return results
        rankings.extend(await search(rewritten))
        return reciprocal_rank_fusion(rankings, scope, limit)
