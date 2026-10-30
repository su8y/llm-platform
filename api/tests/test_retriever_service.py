import json
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from module.Retrieval.core import SearchScope
from support import DataError, load_module


Retriever = load_module('module/Retrieval/service.py').Retriever


def match(key: str, text: str, company: str = 'a', active: bool = True, kind: str = 'post') -> SimpleNamespace:
    return SimpleNamespace(id=key, metadata={
        'company_key': company, 'content': text, 'is_on': active,
        'upload_file_id': 7, 'data_type': kind, 'id': 42,
    })


class RetrieverTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.decision = {'query': None}
        self.contexts = []
        self.closed = False

        async def stream(**kwargs: object):
            self.contexts.append(kwargs)
            try:
                yield {'text': json.dumps(self.decision)}
            finally:
                self.closed = True

        self.proxy = SimpleNamespace(embeddings=AsyncMock(return_value=[0.1]), stream=stream)
        self.vectors = SimpleNamespace(
            find=AsyncMock(return_value=[match('dense', 'general policy')]),
            find_lexical=AsyncMock(return_value=[match('lexical', 'AB123 refund')]),
        )
        self.retriever = Retriever(self.vectors, self.proxy, 'service', 'vendor', 'model', 'session')
        self.scope = SearchScope('a', 7, ('post',))

    async def test_hybrid_search_preserves_question_scope_and_history(self) -> None:
        hits = await self.retriever.find('AB123', self.scope, history=[{'message': 'refund'}])
        self.assertEqual({hit.id for hit in hits}, {'dense', 'lexical'})
        self.proxy.embeddings.assert_awaited_once_with(text='AB123', service='service')
        dense_filter = self.vectors.find.await_args.kwargs['filter']
        self.assertEqual(dense_filter, self.vectors.find_lexical.await_args.kwargs['filter'])
        self.assertEqual(dense_filter, {
            'company_key': 'a', 'is_on': True, 'upload_file_id': 7,
            'data_type': {'$in': ['post']},
        })
        context = json.loads(self.contexts[0]['human_message'])
        self.assertEqual(context['question'], 'AB123')
        self.assertIn('refund', context['history'])
        self.assertTrue(self.closed)
        self.assertEqual(hits[0].metadata['id'], 42)

    async def test_refinement_is_bounded_and_keeps_original_evidence(self) -> None:
        self.decision = {'query': 'AB123 refund'}
        self.vectors.find.side_effect = [[match('original', 'policy')], [match('refined', 'refund')]]
        hits = await self.retriever.find('AB123', self.scope)
        self.assertEqual(self.proxy.embeddings.await_count, 2)
        self.assertEqual(len(self.contexts), 1)
        self.assertTrue({'original', 'refined'} <= {hit.id for hit in hits})
        for call in self.vectors.find.await_args_list:
            self.assertEqual(call.kwargs['filter']['company_key'], 'a')

    async def test_unauthorized_evidence_never_reaches_llm(self) -> None:
        self.vectors.find.return_value = [
            match('private', 'secret', company='b'), match('deleted', 'secret', active=False),
            match('email', 'secret', kind='email'), match('safe', 'allowed'),
        ]
        self.vectors.find_lexical.return_value = []
        hits = await self.retriever.find('question', self.scope)
        self.assertEqual([hit.id for hit in hits], ['safe'])
        self.assertNotIn('secret', self.contexts[0]['human_message'])

    async def test_invalid_json_preserves_original_results(self) -> None:
        async def stream(**kwargs: object):
            yield {'text': 'not json'}

        self.proxy.stream = stream
        hits = await self.retriever.find('AB123', self.scope)
        self.assertEqual(len(hits), 2)
        self.assertEqual(self.proxy.embeddings.await_count, 1)

    async def test_excessive_output_closes_generator(self) -> None:
        self.decision = {'query': 'x' * 2000}
        hits = await self.retriever.find('AB123', self.scope)
        self.assertEqual(len(hits), 2)
        self.assertTrue(self.closed)
        self.assertEqual(self.proxy.embeddings.await_count, 1)

    async def test_legacy_snippets_skip_llm(self) -> None:
        self.vectors.find.return_value = [match('legacy', '')]
        self.vectors.find_lexical.return_value = []
        hits = await self.retriever.find('question', self.scope)
        self.assertEqual(len(hits), 1)
        self.assertEqual(self.contexts, [])

    async def test_empty_scope_prevents_io(self) -> None:
        with self.assertRaises(DataError):
            await self.retriever.find('question', SearchScope(''))
        self.proxy.embeddings.assert_not_awaited()
        self.vectors.find_lexical.assert_not_awaited()

    async def test_io_failure_propagates(self) -> None:
        self.vectors.find.side_effect = ConnectionError('unavailable')
        with self.assertRaises(ConnectionError):
            await self.retriever.find('question', self.scope)
