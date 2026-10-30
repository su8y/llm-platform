import asyncio
import json
from copy import deepcopy
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, Mock, patch

from support import VectorDBError, load_milvus


milvus = load_milvus()


class FilterTests(TestCase):
    def test_configured_dimension_is_used_when_creating_a_collection(self) -> None:
        sdk = Mock()
        with patch.dict("os.environ", {"VECTOR_DIMENSION": "1536"}):
            milvus.MilvusClient("knowledge")._create_collection(sdk)
        vector_field = next(call for call in sdk.create_schema.return_value.add_field.call_args_list if call.args[0] == "vector")
        self.assertEqual(vector_field.kwargs["dim"], 1536)

    def test_invalid_dimension_is_rejected_before_creating_a_collection(self) -> None:
        for value in ("", "invalid", "0", "-1", "1.5"):
            sdk = Mock()
            with self.subTest(value=value), patch.dict("os.environ", {"VECTOR_DIMENSION": value}):
                with self.assertRaises(VectorDBError):
                    milvus.MilvusClient("knowledge")._create_collection(sdk)
            sdk.create_schema.assert_not_called()

    def test_tenant_file_and_active_constraints(self) -> None:
        expression = milvus.MilvusClient._make_search_filter({
            'company_key': 'a', 'upload_file_id': 12, 'is_on': True,
            'data_type': {'$in': ['post', 'parser']},
        })
        self.assertIn('metadata["company_key"] == "a"', expression)
        self.assertIn('metadata["upload_file_id"] == 12', expression)
        self.assertIn('is_on == true', expression)
        self.assertIn('data_type in ["post", "parser"]', expression)

    def test_filter_value_is_escaped(self) -> None:
        value = 'a" or is_on == true or "'
        expression = milvus.MilvusClient._make_search_filter({'company_key': value})
        self.assertEqual(json.loads(expression.split(' == ', 1)[1]), value)

    def test_invalid_filters_fail_closed(self) -> None:
        for filters in ({'unknown': True}, {'company_key': {'$ne': 'a'}},
                        {'is_on': 'true'}, {'company_key': None},
                        {'id': float('nan')}, {'data_type': {'$in': []}}):
            with self.subTest(filters=filters), self.assertRaises(VectorDBError):
                milvus.MilvusClient._make_search_filter(filters)


class MilvusTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.client = milvus.MilvusClient('knowledge')
        self.sdk = Mock()
        self.sdk.search.return_value = [[]]
        self.connection = patch.object(self.client, 'check_connection', AsyncMock(return_value=self.sdk))
        self.connection.start()
        self.addCleanup(self.connection.stop)

    async def test_dense_and_bm25_receive_identical_scope(self) -> None:
        self.client._hybrid = True
        filters = {'company_key': 'a', 'is_on': True}
        await self.client.find([0.1], filter=filters)
        await self.client.find_lexical('AB123', filter=filters)
        dense, lexical = self.sdk.search.call_args_list
        self.assertEqual(dense.kwargs['filter'], lexical.kwargs['filter'])
        self.assertEqual(dense.kwargs['anns_field'], 'vector')
        self.assertEqual(lexical.kwargs['anns_field'], 'sparse')
        self.assertEqual(lexical.kwargs['data'], ['AB123'])
        self.assertEqual(lexical.kwargs['timeout'], 10.0)

    async def test_reindex_scan_keeps_company_scope_and_closes_iterator(self) -> None:
        self.sdk.query_iterator.return_value.next.side_effect = [[{'id': '1'}], []]
        with patch.object(self.client, 'exists', AsyncMock(return_value=True)):
            batches = [batch async for batch in self.client.iterate('a')]
        self.assertEqual(batches, [[{'id': '1'}]])
        self.assertEqual(self.sdk.query_iterator.call_args.kwargs['filter'], 'metadata["company_key"] == "a"')
        self.sdk.query_iterator.return_value.close.assert_called_once()

    async def test_missing_source_never_creates_a_collection(self) -> None:
        with patch.object(self.client, 'exists', AsyncMock(return_value=False)):
            with self.assertRaises(VectorDBError):
                _ = [batch async for batch in self.client.iterate('a')]
        self.sdk.query_iterator.assert_not_called()

    async def test_scan_failure_closes_iterator(self) -> None:
        self.sdk.query_iterator.return_value.next.side_effect = RuntimeError('unavailable')
        with patch.object(self.client, 'exists', AsyncMock(return_value=True)):
            with self.assertRaises(VectorDBError):
                _ = [batch async for batch in self.client.iterate('a')]
        self.sdk.query_iterator.return_value.close.assert_called_once()

    async def test_legacy_collection_keeps_dense_search(self) -> None:
        self.assertEqual(await self.client.find_lexical('AB123'), [])
        self.sdk.search.assert_not_called()

    async def test_upsert_keeps_chunk_and_active_flag_together(self) -> None:
        await self.client.insert_many(['1'], [[0.1]], [{
            'content': 'AB123', 'company_key': 'a', 'is_on': False,
        }])
        record = self.sdk.upsert.call_args.kwargs['data'][0]
        self.assertEqual(record['text'], 'AB123')
        self.assertIs(record['is_on'], False)
        self.assertEqual(record['metadata']['content'], 'AB123')

    async def test_metadata_update_preserves_original_content(self) -> None:
        self.sdk.get.return_value = [{
            'id': '1', 'vector': [0.1],
            'metadata': {'id': 9, 'company_key': 'a', 'content': 'AB123', 'is_on': True},
        }]
        await self.client.update(['1'], [{'is_on': False}])
        record = self.sdk.upsert.call_args.kwargs['data'][0]
        self.assertEqual(record['text'], 'AB123')
        self.assertEqual(record['metadata']['id'], 9)
        self.assertIs(record['is_on'], False)

    async def test_mismatched_batch_is_rejected_before_io(self) -> None:
        with self.assertRaises(VectorDBError):
            await self.client.insert_many(['1', '2'], [[0.1]], [{}])
        self.sdk.upsert.assert_not_called()

    async def test_delete_escapes_ids_and_never_deletes_on_empty_input(self) -> None:
        self.assertFalse(await self.client.remove(id=[]))
        self.sdk.delete.assert_not_called()
        await self.client.remove(id=['a" or true'])
        expression = self.sdk.delete.call_args.kwargs['filter']
        self.assertEqual(json.loads(expression.removeprefix('id in ')), ['a" or true'])

    async def test_schema_has_bm25_function_and_sparse_index(self) -> None:
        self.client._create_collection(self.sdk)
        schema = self.sdk.create_schema.return_value
        self.assertIn('text', [call.args[0] for call in schema.add_field.call_args_list])
        function = schema.add_function.call_args.args[0]
        self.assertEqual(function.input_field_names, ['text'])
        self.assertEqual(function.output_field_names, ['sparse'])
        index_calls = self.sdk.prepare_index_params.return_value.add_index.call_args_list
        self.assertIn('BM25', [call.kwargs['metric_type'] for call in index_calls])

    async def test_repeated_id_replaces_content(self) -> None:
        records = {}

        def upsert(**kwargs: object) -> None:
            for record in kwargs['data']:
                records[record['id']] = deepcopy(record)

        self.sdk.upsert.side_effect = upsert
        await self.client.insert_many(['1'], [[0.1]], [{'content': 'old'}])
        await self.client.insert_many(['1'], [[0.2]], [{'content': 'new'}])
        self.assertEqual(len(records), 1)
        self.assertEqual(records['1']['text'], 'new')
