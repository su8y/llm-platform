from module.MCP.run import *
from module.MCP.agent import *
from module.MCP.dto import *
from module.Language.detector import FastTextDetector

from utils.error import *



class RunMCP:
    """
    # RunMCP do\n
    ---\n
    1. mainDB에서 요청에 맞는 시스템 프롬프트 쿼리\n
    2. memoryDB에 저장된 대화이력 조회\n
    3. FastTextDetector(DL) 활용해 사용자 질문 언어 판별 | 일본어 답변을 제대로 못해 조치\n
    5. [1, 2, 3] I/O를 비동기로 동시에 진행\n
    6. llm-proxy api 요청 | client.groxy.LLMProxyClient.stream_with_mcp 코드 참고\n
    7. 답변 객체 or 텍스트를 제네레이터로 RunLLM 호출한 객체에 전달(streaming message)\n
    8. 답변 완료 후, module.LLM.run.callback에서 크레딧, 답변 기록 등 후처리 진행\n
    """


    def __init__(self, args:chatDomain, thread:bool=None, stream:bool=None):
        self.args:chatDomain = args
        self.thread = thread if thread is not None else True
        self.stream = stream if stream is not None else True

    async def activate(self):
        try:
            tasks = []
            self._get_mcpArgs()
            self._get_model()
            tasks.append(self._get_language_message())
            tasks.append(self._get_conversation_history())
            tasks.append(self._get_prompt())
            tasks.append(self._get_mcp_url_and_tools())
            await asyncio.gather(*tasks)
            async for chunk in self._run():
                yield chunk

        except DBError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy.activate] 🔴 DBError: {e}")
            async for chunk in make_error_message_for_LLM():
                yield chunk
        except MemoryDBError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy.activate] 🔴 MemoryDBError: {e}")
            async for chunk in make_error_message_for_LLM():
                yield chunk
        except VectorDBError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy.activate] 🔴 VectorDBError: {e}")
            async for chunk in make_error_message_for_LLM():
                yield chunk
        except AWSError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy.activate] 🔴 AWSError: {e}")
            async for chunk in make_error_message_for_LLM():
                yield chunk
        except LLMStreamingError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy.activate] 🔴 LLMStreamingError: {e}")
            async for chunk in make_error_message_for_LLM():
                yield chunk
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy.activate] 🔴 Exception: {e}")
            async for chunk in make_error_message_for_LLM():
                yield chunk


    async def _run(self):
        try:
            async for chunk in run_mcp(self.mcpArgs):
                yield chunk
        except DBError as e:
            logging.error(f"session_key: {self.args.session_key} | [module.MCP.activate._run] 🔴 DBError: {e}")
            raise DBError(e)
        except MemoryDBError as e:
            logging.error(f"session_key: {self.args.session_key} | [module.MCP.activate._run] 🔴 MemoryDBError: {e}")
            raise MemoryDBError(e)
        except VectorDBError as e:
            logging.error(f"session_key: {self.args.session_key} | [module.MCP.activate._run] 🔴 VectorDBError: {e}")
            raise VectorDBError(e)
        except AWSError as e:
            logging.error(f"session_key: {self.args.session_key} | [module.MCP.activate._run] 🔴 AWSError: {e}")
            raise AWSError(e)
        except LLMStreamingError as e:
            logging.error(f"session_key: {self.args.session_key} | [module.MCP.activate._run] 🔴 LLMStreamingError: {e}")
            raise LLMStreamingError(e)
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [module.MCP.activate._run] 🔴 Exception: {e}")
            raise e


    def _get_mcpArgs(self):
        try:
            if not self.args or not isinstance(self.args, chatDomain):
                raise ValueError("params is required and must be chatDomain")
            self.mcpArgs:MCPArgs = make_mcpArgs(self.args)
        except ValueError as e:
            logging.error(f"session_key: {self.args.session_key} | [module.MCP.activate._get_llmArgs] 🔴 ValueError: {e}")
            raise e
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [module.MCP.activate._get_llmArgs] 🔴 Exception: {e}")
            raise e


    def _get_model(self):
        if not self.mcpArgs.chat_info:
            self.mcpArgs.chat_info = {}
            self.mcpArgs.chat_info["model"] = self.mcpArgs.model
        else:
            self.mcpArgs.chat_info["model"] = self.mcpArgs.model


    async def _get_language_message(self):
        try:
            await FastTextDetector.detect(self.mcpArgs)
            if self.mcpArgs.lang_detected == JAPANESE:
                self.mcpArgs.language_message = JAPANESE_MESSAGE
            else:
                self.mcpArgs.language_message = OTHER_MESSAGE
        except LLMProxyError as e:
            logging.error(f"session_key: {self.args.session_key} | [module.MCP.activate._get_language_message] 🔴 LLMProxyError: {e}")
            raise LLMProxyError(e)
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [module.MCP.activate._get_language_message] 🔴 Exception: {e}")
            raise e


    async def _get_conversation_history(self):
        try:
            self.mcpArgs.conversation_history = await get_conversation_history(self.mcpArgs) # memory_db_client, session_key
        except MemoryDBError as e:
            logging.error(f"session_key: {self.args.session_key} | [module.MCP.activate._get_conversation_history] 🔴 MemoryDBError: {e}")
            raise MemoryDBError(e)
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [module.MCP.activate._get_conversation_history] 🔴 Exception: {e}")
            raise e


    async def _get_prompt(self):
        try:
            prompt, self.mcpArgs.chat_info["prompt_id"] = await get_system_prompt(self.mcpArgs) # main_db_client, company_key
            # self.mcpArgs.system_message = prompt + '\n\n' + RAG_PROMPT + '\n\n' + CONVERSATION_HISTORY_MCP + '\n\n' + IMAGE_PROMPT + '\n\n' + URL_LINK_PROMPT + '\n\n' + self.mcpArgs.language_message
            self.mcpArgs.system_message = prompt + '\n\n' + RAG_PROMPT + '\n\n' + IMAGE_PROMPT + '\n\n' + URL_LINK_PROMPT + '\n\n' + self.mcpArgs.language_message
        except DBError as e:
            logging.error(f"session_key: {self.args.session_key} | [module.MCP.activate._get_prompt] 🔴 DBError: {e}")
            raise DBError(e)
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [module.MCP.activate._get_prompt] 🔴 Exception: {e}")
            raise e


    async def _get_mcp_url_and_tools(self):
        try:
            self.mcpArgs.mcp_server, self.mcpArgs.mcp_token, mcp_allowed_tools = await get_mcp_url_and_tools(
                self.mcpArgs
            )
            if isinstance(mcp_allowed_tools, str):
                try:
                    self.mcpArgs.mcp_allowed_tools = ast.literal_eval(mcp_allowed_tools)
                except Exception:
                    logging.warning(f"session_key: {self.args.session_key} | [module.MCP.activate._get_mcp_url_and_tools]: You need check mcp_allowed_tools columns! self.mcpArgs.mcp_allowed_tools: {mcp_allowed_tools}")
                    self.mcpArgs.mcp_allowed_tools = None
        except DBError as e:
            logging.error(f"session_key: {self.args.session_key} | [module.MCP.activate._get_mcp_url_and_tools] DBError: {e.message}")
            raise DBError(e.message)
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [module.MCP.activate._get_mcp_url_and_tools] Exception: {e}")
            raise e
