"""Load real modules with external dependencies mocked for offline unit tests."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


API_ROOT = Path(__file__).resolve().parents[1]


class AppError(Exception):
    pass


class DataError(AppError):
    pass


class VectorDBError(AppError):
    pass


class Model:
    def __init__(self, **values: object) -> None:
        self.__dict__.update(values)


def module(name: str, **values: object) -> ModuleType:
    result = ModuleType(name)
    result.__dict__.update(values)
    return result


def load_module(path: str, **dependencies: ModuleType) -> ModuleType:
    name = path.removesuffix('.py').replace('/', '.')
    spec = importlib.util.spec_from_file_location(name, API_ROOT / path)
    result = importlib.util.module_from_spec(spec)
    errors = module('utils.error', AppError=AppError, DataError=DataError, VectorDBError=VectorDBError)
    with patch.dict(sys.modules, {'utils.error': errors, **dependencies}):
        spec.loader.exec_module(result)
    return result


def load_milvus() -> ModuleType:
    return load_module('client/milvus.py', **{
        'pydantic': module('pydantic', BaseModel=Model),
        'pymilvus': module('pymilvus', MilvusClient=Model, Function=Model,
            FunctionType=SimpleNamespace(BM25='BM25'),
            DataType=SimpleNamespace(VARCHAR='str', FLOAT_VECTOR='vector', JSON='json',
                                     BOOL='bool', SPARSE_FLOAT_VECTOR='sparse')),
    })
