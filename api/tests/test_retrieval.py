import asyncio
import unittest

from module.Retrieval.core import (
    SearchHit, SearchScope, reciprocal_rank_fusion, retrieve,
)


class RankingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scope = SearchScope("company-a", 7)
        self.exact = SearchHit("exact", "company-a", "invoice AB123", 7)
        self.other = SearchHit("other", "company-a", "shipping status", 7)
        self.private = SearchHit("private", "company-b", "invoice AB123", 7)
        self.deleted = SearchHit("deleted", "company-a", "invoice AB123", 7, False)
        self.file = SearchHit("file", "company-a", "invoice AB123", 8)

    def test_rrf_scope_duplicate_and_shared_evidence(self) -> None:
        rankings = [[self.private, self.exact, self.exact, self.other], [self.other]]
        hits = reciprocal_rank_fusion(rankings, self.scope)
        self.assertEqual([hit.id for hit in hits], ["other", "exact"])
        self.assertAlmostEqual(hits[1].score, 1 / 61)
        self.assertEqual(reciprocal_rank_fusion(rankings, self.scope, 0), [])


class AgentTests(unittest.IsolatedAsyncioTestCase):
    async def test_refine_once_preserves_original_and_scope(self) -> None:
        scope = SearchScope("company-a")
        calls = []

        async def search(query, received_scope, limit):
            calls.append((query, received_scope, limit))
            return [SearchHit(query, "company-a", query)]

        async def refine(question, results):
            self.assertEqual(question, "original")
            self.assertEqual(results[0].id, "original")
            return "refined"

        hits = await retrieve("original", scope, search, search, refine, lambda hits: False)
        self.assertEqual({hit.id for hit in hits}, {"original", "refined"})
        self.assertEqual(len(calls), 4)
        self.assertTrue(all(call[1] == scope for call in calls))

    async def test_sufficient_results_skip_llm(self) -> None:
        async def search(query, scope, limit):
            return [SearchHit("a", scope.company_key, "answer")]

        async def refine(question, results):
            self.fail("unnecessary LLM call")

        hits = await retrieve("question", SearchScope("a"), search, search, refine)
        self.assertEqual(len(hits), 1)

    async def test_duplicate_rewrite_stops(self) -> None:
        calls = []

        async def search(query, scope, limit):
            calls.append(query)
            return []

        async def refine(question, results):
            return " QUESTION "

        self.assertEqual(await retrieve("question", SearchScope("a"), search, search, refine), [])
        self.assertEqual(len(calls), 2)

    async def test_total_timeout_cancels_backends(self) -> None:
        cancelled = []

        async def search(query, scope, limit):
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.append(True)

        with self.assertRaises(TimeoutError):
            await retrieve("question", SearchScope("a"), search, search, timeout=0.01)
        self.assertEqual(len(cancelled), 2)

    async def test_backend_failure_cancels_sibling(self) -> None:
        cancelled = asyncio.Event()

        async def dense(query, scope, limit):
            await asyncio.sleep(0)
            raise ConnectionError("backend unavailable")

        async def lexical(query, scope, limit):
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        with self.assertRaises(ConnectionError):
            await retrieve("question", SearchScope("a"), dense, lexical)
        self.assertTrue(cancelled.is_set())

    async def test_empty_scope_does_not_call_backends(self) -> None:
        async def search(query, scope, limit):
            self.fail("unscoped retrieval")

        self.assertEqual(await retrieve("question", SearchScope(""), search, search), [])


if __name__ == "__main__":
    unittest.main()
