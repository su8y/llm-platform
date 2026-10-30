import tiktoken

from utils.constants import *



def get_token_length(text:str, model_name:str=None):
    try:
        model_name = model_name or BASE_MODEL
        model_name = model_name if model_name in TIKTOKEN_MODEL_LIST else "gpt-4o"
        encoding = tiktoken.encoding_for_model(model_name)
        return len(encoding.encode(text))
    except Exception as e:
        raise e


def chunking_text(text: str, model_name: str, max_tokens: int, overlap_tokens: int = 100):
    model_name = model_name if model_name in TIKTOKEN_MODEL_LIST else "gpt-4o"
    encoding = tiktoken.encoding_for_model(model_name)
    tokens = encoding.encode(text)
    
    chunks = []
    start_idx = 0
    
    while start_idx < len(tokens):
        end_idx = min(start_idx + max_tokens, len(tokens))
        chunks.append(tokens[start_idx:end_idx])
        start_idx = end_idx - overlap_tokens if end_idx < len(tokens) else len(tokens)
    
    return [encoding.decode(chunk) for chunk in chunks] if len(chunks) > 0 else [""]