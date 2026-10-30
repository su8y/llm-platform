import logging
import time
from datetime import timedelta

from module.LLM.dto import LLMArgs
from module.Mail.dto import LLMEmailArgs
from module.MCP.dto import MCPArgs



def get_elapsed(llmArgs:LLMArgs|LLMEmailArgs|MCPArgs, key:str):
    try:
        end_time = time.time()
        elapsed = timedelta(seconds=float(end_time - llmArgs.start_time)).total_seconds()
        llmArgs.time_info[key] = elapsed
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_elapsed] Exception: {e}")
        raise e