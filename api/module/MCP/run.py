from datetime import timezone

from module.MCP.helper import *
from utils.error import *
from utils.vector import get_token_length



async def run_mcp(mcpArgs:MCPArgs):
    try:
        # calculate token size
        human_message = make_human_message(question=mcpArgs.question, language_message=mcpArgs.language_message) # for sent & for cal token
        str_for_token_length = mcpArgs.system_message + str(mcpArgs.conversation_history) + human_message
        token = get_token_length(str_for_token_length, mcpArgs.model)

        # save question to Database and Memory
        data = make_chat_history_data(mcpArgs.chat_info, role="human", message=mcpArgs.question, token=token)
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        insert_query = f"""INSERT INTO chat_history ({columns}) VALUES ({placeholders})"""
        await mcpArgs.main_db_client.execute(query=insert_query, params=tuple(data.values()))
        mcpArgs.chat_info["question_id"] = mcpArgs.chat_info["id"]

        # time test
        end_time = time.time()
        elapsed = timedelta(seconds=float(end_time - mcpArgs.start_time))
        logging.info(f"session_key: {mcpArgs.session_key} | [TIMETEST] ⏱️ TIME to proxy: {elapsed}")
        mcpArgs.time_info["ElapsedToProxy"] = elapsed.total_seconds()

        # log for debug message
        # write_log_for_debug_message(
        #     system_message=mcpArgs.system_message,
        #     conversation_history=mcpArgs.conversation_history,
        #     human_message=human_message
        # )

        llm_proxy_calling = mcpArgs.llm_proxy_client.stream if not mcpArgs.is_mcp else mcpArgs.llm_proxy_client.stream_with_mcp
        is_first_chunk = True
        async for chunk in llm_proxy_calling(
            mcp_server=mcpArgs.mcp_server,
            mcp_token=mcpArgs.mcp_token,
            mcp_allowed_tools=mcpArgs.mcp_allowed_tools,
            service=mcpArgs.service,
            vendor=mcpArgs.vendor,
            model=mcpArgs.model,
            system_message=mcpArgs.system_message,
            system_message_placeholder=mcpArgs.system_message_placeholder,
            human_message=human_message,
            conversation_history=mcpArgs.conversation_history,
            callback=callback,
            callback_args=mcpArgs,
            time=float(mcpArgs.start_time),
            store_name=mcpArgs.store_name
        ):
            if chunk: # mcp일 경우엔 dict를 str로 serialize해서 보냄. client에서 json.loads로 dict 변환 중.
                if is_first_chunk:
                    tasks = list()

                    # 대화이력 저장
                    data_redis = redis_format(role="human", message=mcpArgs.question)
                    tasks.append(mcpArgs.memory_db_client.rpush(mcpArgs.session_key, data_redis))
                    tasks.append(mcpArgs.memory_db_client.expire(mcpArgs.session_key, 1800))

                    # 크레딧 차감
                    if mcpArgs.credit_available and mcpArgs.credit_available > 0:
                        tasks.append(mcpArgs.main_db_client.execute(
                            query="UPDATE company_info SET credit_available = credit_available - 1 WHERE company_key = %s AND credit_available > 0",
                            params=(mcpArgs.company_key)
                        ))

                    # io 비동기로 동시 진행
                    await asyncio.gather(*tasks)

                    # 첫번째 답변 떨어졌을 때 시간 체크 및 기타 상태값 변경
                    is_first_chunk = False
                    time_from_proxy = time.time()
                    elapsed = timedelta(seconds=float(time_from_proxy - mcpArgs.start_time))
                    logging.info(f"session_key: {mcpArgs.session_key} | [TIMETEST] ⏱️ TIME from proxy: {elapsed}")
                    mcpArgs.time_info["ElapsedFromProxy"] = elapsed.total_seconds()

                # 현재는 텍스트만 보냄
                if chunk.get("text"):
                    yield chunk["text"]

    except DBError as e:
        logging.error(f"session_key: {mcpArgs.session_key} | [llm.proxy.run_llm] 🔴 DBError: {e}")
        raise DBError(e)
    except MemoryDBError as e:
        logging.error(f"session_key: {mcpArgs.session_key} | [llm.proxy.run_llm] 🔴 MemoryDBError: {e}")
        raise MemoryDBError(e)
    except VectorDBError as e:
        logging.error(f"session_key: {mcpArgs.session_key} | [llm.proxy.run_llm] 🔴 VectorDBError: {e}")
        raise VectorDBError(e)
    except AWSError as e:
        logging.error(f"session_key: {mcpArgs.session_key} | [llm.proxy.run_llm] 🔴 AWSError: {e}")
        raise AWSError(e)
    except LLMStreamingError as e:
        logging.error(f"session_key: {mcpArgs.session_key} | [llm.proxy.run_llm] 🔴 LLMStreamingError: {e}")
        raise LLMStreamingError(e)
    except Exception as e:
        logging.error(f"session_key: {mcpArgs.session_key} | [llm.proxy.run_llm] 🔴 Exception: {e}")
        raise e


async def callback(args:MCPArgs):
    try:
        end_time = time.time()
        elapsed = timedelta(seconds=float(end_time - args.start_time))
        logging.info(f"session_key: {args.session_key} | [TIMETEST] ⏱️ TIME to callback: {elapsed}")
        args.time_info["ElapsedAtCallback"] = elapsed.total_seconds()

        session_key = args.session_key
        answer_id = args.answer_id
        message = args.message # message는 proxy client에서 미리 받아둠
        credit_available = args.credit_available
        company_key = args.company_key
        elapsed_info = str(args.time_info)
        memory_db_client:RedisClient = args.memory_db_client
        main_db_client:MySQLClient = args.main_db_client
        reg_date = datetime.now(timezone('UTC'))
        tasks = list()

        data_redis = redis_format(role="ai", message=message, id=answer_id)
        tasks.append(memory_db_client.rpush(session_key, data_redis))
        tasks.append(memory_db_client.expire(session_key, 1800))

        data = make_chat_history_data(args.chat_info, role="ai", message=message, token=get_token_length(message), reg_date=reg_date, id=answer_id, elapsed_info=elapsed_info)
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        insert_query = f"""INSERT INTO chat_history ({columns}) VALUES ({placeholders})"""
        tasks.append(main_db_client.execute(query=insert_query, params=tuple(data.values())))

        chat_title_row = await main_db_client.fetch_one(query="SELECT EXISTS(SELECT 1 FROM chat_title WHERE session_key = %s)", params=(session_key))
        if chat_title_row[0]:
            update_query = "UPDATE chat_title SET update_date = %s WHERE session_key = %s"
            params = (reg_date, session_key)
            tasks.append(main_db_client.execute(query=update_query, params=params))
        if credit_available and credit_available > 0:
            tasks.append(record_credit_history(main_db_client, company_key, credit_available, reg_date))

        await asyncio.gather(*tasks)
        logging.info(f"[answer_id: {answer_id}, session_key: {session_key}] ⏱️ WHOLE PROCESS ELAPSED INFO: {elapsed_info}")

    except DBError as e:
        logging.error(f"session_key: {args.session_key} | [module.LLM.run.callback] 🔴 DBError: {e}")
    except MemoryDBError as e:
        logging.error(f"session_key: {args.session_key} | [module.LLM.run.callback] 🔴 MemoryDBError: {e}")
    except AWSError as e:
        logging.error(f"session_key: {args.session_key} | [module.LLM.run.callback] 🔴 AWSError: {e}")
    except Exception as e:
        logging.error(f"session_key: {args.session_key} | [module.LLM.run.callback] 🔴 Exception: {e}")
