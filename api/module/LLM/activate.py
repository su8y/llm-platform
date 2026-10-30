from module.LLM.run import *
# from module.LLM.agent import *
from module.Language.detector import FastTextDetector
from module.LLM.dto import *
from utils.error import *



class RunLLM:
    """
    # RunLLM do\n
    ---\n
    1. mainDB에서 요청에 맞는 시스템 프롬프트 쿼리\n
    2. vectorDB에서 사용자 질문 의미와 가장 가까운 데이터 검색 -> mysql, s3 등에서 원천 데이터 가져옴\n
    3. memoryDB에 저장된 대화이력 조회\n
    4. FastTextDetector(DL) 활용해 사용자 질문 언어 판별 | 일본어 답변을 제대로 못해 조치\n
    5. [1, 2, 3, 4] I/O를 비동기로 동시 진행(병렬 처리)\n
    6. llm-proxy api 요청 | client.groxy.LLMProxyClient.stream 코드 참고\n
    7. 답변 객체 or 텍스트를 제네레이터로 RunLLM 호출한 객체에 전달(streaming message)\n
    8. 답변 완료 후, module.LLM.run.callback에서 크레딧, 답변 기록 등 후처리 진행\n
    """

    def __init__(self, args:chatDomain|chatbotDomain, thread:bool=None, stream:bool=None):
        self.args:chatDomain = args
        self.thread = thread if thread is not None else True
        self.stream = stream if stream is not None else True

    async def activate(self):
        try:
            tasks = []
            self._get_llmArgs()
            self._get_model()
            tasks.append(self._get_language_message())
            tasks.append(self._get_context())
            tasks.append(self._get_prompt())
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
            async for chunk in run_llm(self.llmArgs):
                yield chunk

        except DBError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._run] 🔴 DBError: {e}")
            raise DBError(e)
        except MemoryDBError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._run] 🔴 MemoryDBError: {e}")
            raise MemoryDBError(e)
        except VectorDBError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._run] 🔴 VectorDBError: {e}")
            raise VectorDBError(e)
        except AWSError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._run] 🔴 AWSError: {e}")
            raise AWSError(e)
        except LLMStreamingError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._run] 🔴 LLMStreamingError: {e}")
            raise LLMStreamingError(e)
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._run] 🔴 Exception: {e}")
            raise e


    def _get_llmArgs(self):
        try:
            if not self.args or not isinstance(self.args, (chatDomain, chatbotDomain)):
                raise ValueError("params is required and must be chatDomain")
            self.llmArgs:LLMArgs = make_llmArgs(self.args)
        except ValueError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_llmArgs] 🔴 ValueError: {e}")
            raise e
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_llmArgs] 🔴 Exception: {e}")
            raise e


    def _get_model(self):
        if not self.llmArgs.chat_info:
            self.llmArgs.chat_info = {}
            self.llmArgs.chat_info["model"] = self.llmArgs.model
        else:
            self.llmArgs.chat_info["model"] = self.llmArgs.model


    async def _get_language_message(self):
        try:
            await FastTextDetector.detect(self.llmArgs)
            if self.llmArgs.lang_detected == JAPANESE:
                self.llmArgs.language_message = JAPANESE_MESSAGE
            else:
                self.llmArgs.language_message = OTHER_MESSAGE
        except LLMProxyError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_language_message] 🔴 LLMProxyError: {e}")
            raise LLMProxyError(e)
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_language_message] 🔴 Exception: {e}")
            raise e


    async def _get_context(self) -> None:
        await self._get_conversation_history()
        await self._get_retrieval_data()


    async def _get_retrieval_data(self):
        try:
            # io: to vectorDB
            match_docs = await query_vector(self.llmArgs) # llm_proxy_client, vector_db_client, question, service

            # io: to mysql, to s3
            refer_ids, parser_ids, sitemap_ids, email_ids, self.llmArgs.retrieval_data = await get_retrieval_data(match_docs, self.llmArgs) # main_db_client, s3_client

            # set chat_info for insert history
            self.llmArgs.chat_info["refer_id"] = str(refer_ids) if refer_ids else None
            self.llmArgs.chat_info["parser_id"] = str(parser_ids) if parser_ids else None

            self.llmArgs.chat_info["sitemap_id"] = str(sitemap_ids) if sitemap_ids else None
            self.llmArgs.chat_info["email_id"] = str(email_ids) if email_ids else None
            if self.llmArgs.info:
                self.llmArgs.chat_info = {**self.llmArgs.chat_info, **self.llmArgs.info}

        except VectorDBError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_retrieval_data] 🔴 VectorDBError: {e}")
            raise VectorDBError(e)
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_retrieval_data] 🔴 Exception: {e}")
            raise e


    async def _get_conversation_history(self):
        try:
            self.llmArgs.conversation_history = await get_conversation_history(self.llmArgs) # memory_db_client, session_key
        except MemoryDBError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_conversation_history] 🔴 MemoryDBError: {e}")
            raise MemoryDBError(e)
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_conversation_history] 🔴 Exception: {e}")
            raise e


    async def _get_prompt(self):
        try:
            if self.llmArgs.store_name:
                self.llmArgs.system_message, self.llmArgs.chat_info["prompt_id"] = await get_system_prompt(self.llmArgs) # main_db_client, company_key
                # self.llmArgs.system_message = prompt + '\n\n' + CONVERSATION_HISTORY  + '\n\n' + IMAGE_PROMPT + '\n\n' + URL_LINK_PROMPT
            else:
                prompt, self.llmArgs.chat_info["prompt_id"] = await get_system_prompt(self.llmArgs) # main_db_client, company_key
                self.llmArgs.system_message = prompt
                if self.llmArgs.on_llm_platform_system:
                    self.llmArgs.system_message += '\n\n' + RAG_PROMPT + '\n\n' + CONVERSATION_HISTORY + '\n\n' + IMAGE_PROMPT + '\n\n' + URL_LINK_PROMPT
                    if self.llmArgs.info.get("init_date"):
                        self.llmArgs.system_message += f"\n\n{TIME_PROMPT}"

        except DBError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_prompt] 🔴 DBError: {e}")
            raise DBError(e)
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_prompt] 🔴 Exception: {e}")
            raise e

    @staticmethod
    async def get_retrieval_data(s3_client:S3Client, main_db_client:MySQLClient, refer_ids:list, parser_ids:list, email_ids:list, sitemap_ids:list):
        try:
            return await get_retrieval_data_for_client(
                s3_client=s3_client,
                main_db_client=main_db_client,
                refer_id=refer_ids,
                parser_id=parser_ids,
                email_id=email_ids,
                sitemap_id=sitemap_ids
            )
        except DBError as e:
            logging.error(f"[llm.proxy.get_retrieval_data] 🔴 DBError: {e}")
            raise DBError(e)
        except AWSError as e:
            logging.error(f"[llm.proxy.get_retrieval_data] 🔴 AWSError: {e}")
            raise AWSError(e)
        except Exception as e:
            logging.error(f"[llm.proxy.get_retrieval_data] 🔴 Exception: {e}")
            raise e


    @staticmethod
    async def get_conversation_history(memory_db_client:RedisClient, session_key:str):
        """
        ROLE:
        ---
        1. get history data from redis and input to llmArgs
        2. return conversation history data
        \n\n
        ARGS:
        ---
        {
            "memory_db": RedisClient,
            "session_key": str
        }
        """
        try:
            return await get_conversation_history_for_client(
                memory_db_client=memory_db_client,
                session_key=session_key
            )
        except MemoryDBError as e:
            logging.error(f"[llm.proxy.get_conversation_history] 🔴 MemoryDBError: {e}")
            raise MemoryDBError(e)
        except Exception as e:
            logging.error(f"[llm.proxy.get_conversation_history] 🔴 Exception: {e}")
            raise e
