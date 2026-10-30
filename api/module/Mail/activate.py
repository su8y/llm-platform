from module.Mail.agent import *
from module.Mail.run import *
from module.Mail.dto import *
from module.Mail.prompt import *
from module.Language.detector import FastTextDetector
from domain.email import *
from utils.error import *



class RunLLMEmail:
    """
    # RunLLMEmail do\n
    ---\n
    1. LLM-Proxy로 언어 판별 요청\n
    2. mainDB에서 요청에 맞는 시스템 프롬프트 쿼리\n
    3. mainDB에서 메일 쓰레드 파악해 쓰레드 내용 가져옴(like 대화이력)
    4. vectorDB에서 사용자 질문 의미와 가장 가까운 데이터 검색 -> mysql, s3 등에서 원천 데이터 가져옴\n
    5. 위 모든 I/O를 순차적으로 진행. 추후 속도개선 필요하면 병렬처리로 변경
    6. llm-proxy api 요청 | client.groxy.LLMProxyClient.stream 코드 참고\n
    7. 답변 객체 or 텍스트를 제네레이터로 RunLLM 호출한 객체에 전달(streaming message)\n
    8. 답변 완료 후, module.LLM.run.callback에서 크레딧, 답변 기록 등 후처리 진행\n
    """
    def __init__(self, args:CreateEmailContentDomain, thread:bool=None, stream:bool=None):
        self.args:CreateEmailContentDomain = args
        self.thread = thread if thread is not None else True
        self.stream = stream if stream is not None else True


    async def activate(self):
        try:
            self._get_llmMailArgs()
            self._get_model()
            await self._get_reference()
            await self._get_question_by_last_content()
            await self._get_language_message()
            await self._get_retrieval_data()
            await self._get_email_rag_data()
            await self._get_prompt()
            async for chunk in self._run():
                yield chunk

        except DBError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy.activate] 🔴 DBError: {e}")
            async for chunk in make_error_message():
                yield chunk
        except MemoryDBError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy.activate] 🔴 MemoryDBError: {e}")
            async for chunk in make_error_message():
                yield chunk
        except VectorDBError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy.activate] 🔴 VectorDBError: {e}")
            async for chunk in make_error_message():
                yield chunk
        except AWSError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy.activate] 🔴 AWSError: {e}")
            async for chunk in make_error_message():
                yield chunk
        except LLMStreamingError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy.activate] 🔴 LLMStreamingError: {e}")
            async for chunk in make_error_message():
                yield chunk
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy.activate] 🔴 Exception: {e}")
            async for chunk in make_error_message():
                yield chunk


    async def _run(self):
        try:
            async for chunk in run_email_llm(self.llmMailArgs):
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


    def _get_llmMailArgs(self):
        try:
            if not self.args or not isinstance(self.args, CreateEmailContentDomain):
                raise ValueError("params is required and must be CreateEmailContentDomain")
            self.llmMailArgs:LLMEmailArgs = make_llmEmailArgs(self.args)
        except ValueError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_llmArgs] 🔴 ValueError: {e}")
            raise e
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_llmArgs] 🔴 Exception: {e}")
            raise e


    def _get_model(self):
        if not self.llmMailArgs.chat_info:
            self.llmMailArgs.chat_info = {}
            self.llmMailArgs.chat_info["model"] = self.llmMailArgs.model
        else:
            self.llmMailArgs.chat_info["model"] = self.llmMailArgs.model


    async def _get_reference(self):
        try:
            self.llmMailArgs.reference = await get_reference(self.llmMailArgs)
        except DBError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_reference] 🔴 DBError: {e}")
            raise DBError(e)
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_reference] 🔴 Exception: {e}")
            raise e


    async def _get_question_by_last_content(self):
        try:
            self.llmMailArgs.question = await get_question_by_last_content(self.llmMailArgs)
        except DBError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_question_by_last_content] 🔴 DBError: {e}")
            raise DBError(e)
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_question_by_last_content] 🔴 Exception: {e}")
            raise e


    async def _get_language_message(self):
        try:
            self.llmMailArgs.language_message = await agent_judge_language(
                self.llmMailArgs
            )
        except LLMProxyError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_language_message] 🔴 LLMProxyError: {e}")
            raise LLMProxyError(e)
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_language_message] 🔴 Exception: {e}")
            raise e


    # async def _get_language_message(self):
    #     try:
    #         await FastTextDetector.detect(self.llmMailArgs)
    #         if self.llmMailArgs.lang == KOREAN:
    #             self.llmMailArgs.language_message = KOREAN_MESSAGE
    #         elif self.llmMailArgs.lang == JAPANESE:
    #             self.llmMailArgs.language_message = JAPANESE_MESSAGE
    #         else:
    #             self.llmMailArgs.language_message = ENGLISH_MESSAGE
    #     except LLMProxyError as e:
    #         logging.info(f"[llm.proxy._get_language_message] 🔴 LLMProxyError: {e}")
    #         raise LLMProxyError(e)
    #     except Exception as e:
    #         logging.info(f"[llm.proxy._get_language_message] 🔴 Exception: {e}")
    #         raise e


    async def _get_retrieval_data(self):
        try:
            match_docs = await query_vector(self.llmMailArgs)
            self.llmMailArgs.retrieval_data = await get_retrieval_data(self.llmMailArgs, match_docs)

        except LLMProxyError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_retrieval_data] 🔴 LLMProxyError: {e}")
            raise LLMProxyError(e)
        except VectorDBError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_retrieval_data] 🔴 VectorDBError: {e}")
            raise VectorDBError(e)
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_retrieval_data] 🔴 Exception: {e}")
            raise e


    async def _get_email_rag_data(self):
        try:
            match_docs = await query_vector_for_email_rag(self.llmMailArgs)
            self.llmMailArgs.email_rag_data = await get_retrieval_data_for_email_rag(self.llmMailArgs, match_docs)

        except LLMProxyError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_email_rag_data] 🔴 LLMProxyError: {e}")
            raise LLMProxyError(e)
        except VectorDBError as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_email_rag_data] 🔴 VectorDBError: {e}")
            raise VectorDBError(e)
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_email_rag_data] 🔴 Exception: {e}")
            raise e


    async def _get_prompt(self):
        try:
            query = """SELECT prompt FROM llm_platform.mail_prompt_history WHERE company_key = %s ORDER BY reg_date DESC"""
            param = (self.llmMailArgs.company_key, )
            row = await self.llmMailArgs.main_db_client.fetch_one(query, param)
            if row:
                logging.info(f"session_key: {self.args.session_key} | [module.Mail.activate._get_prompt] USE CUSTOMIZED PROMPT")
                self.llmMailArgs.system_message = row[0] + "\n\n\n" + DEFAULT_SYSTEM_MSG
            else:
                logging.info(f"session_key: {self.args.session_key} | [module.Mail.activate._get_prompt] USE BASIC PROMPT")
                self.llmMailArgs.system_message = SYSTEM_MESSAGE + "\n\n\n" + DEFAULT_SYSTEM_MSG
        except Exception as e:
            logging.error(f"session_key: {self.args.session_key} | [llm.proxy._get_prompt] 🔴 Exception: {e}")
            raise e
