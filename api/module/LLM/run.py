from datetime import timezone

from module.LLM.helper import *
from utils.error import *
from utils.vector import get_token_length


async def run_llm(llmArgs:LLMArgs):
    try:
        # calculate token size
        human_message = llmArgs.question if llmArgs.store_name else make_human_message(
            question=llmArgs.question,
            retrieval_data=llmArgs.retrieval_data,
            language_message=llmArgs.language_message
        )
        str_for_token_length = llmArgs.system_message + str(llmArgs.conversation_history) + human_message
        token = get_token_length(str_for_token_length, llmArgs.model)

        # save question to Database and Memory
        data = make_chat_history_data(llmArgs.chat_info, role="human", message=llmArgs.question, token=token)
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        insert_query = f"""INSERT INTO chat_history ({columns}) VALUES ({placeholders})"""
        await llmArgs.main_db_client.execute(query=insert_query, params=tuple(data.values()))
        llmArgs.chat_info["question_id"] = llmArgs.chat_info["id"]

        # time test
        end_time = time.time()
        elapsed = timedelta(seconds=float(end_time - llmArgs.start_time))
        llmArgs.time_info["ElapsedToProxy"] = elapsed.total_seconds()

        # mcp or not
        llm_proxy_calling = llmArgs.llm_proxy_client.stream if not llmArgs.is_mcp else llmArgs.llm_proxy_client.stream_with_mcp

        # write log for debug message
        # write_log_for_debug_message(
        #     system_message=llmArgs.system_message,
        #     conversation_history=llmArgs.conversation_history,
        #     human_message=human_message
        # )

        # request to llm proxy api
        is_first_chunk = True
        async for chunk in llm_proxy_calling(
            service=llmArgs.service,
            vendor=llmArgs.vendor,
            model=llmArgs.model,
            system_message=llmArgs.system_message,
            human_message=human_message,
            conversation_history=llmArgs.conversation_history,
            callback=callback,
            callback_args=llmArgs,
            time=float(llmArgs.start_time),
            store_name=llmArgs.store_name,
            session_key=llmArgs.session_key
        ):
            if chunk:
                # logging.info(f"chunk: {chunk}")
                if is_first_chunk:
                    tasks = list()
                    # 대화이력 저장
                    data_redis = redis_format(role="human", message=llmArgs.question)
                    tasks.append(llmArgs.memory_db_client.rpush(llmArgs.session_key, data_redis))
                    tasks.append(llmArgs.memory_db_client.expire(llmArgs.session_key, 1800))

                    # 크레딧 차감
                    if llmArgs.credit_available and llmArgs.credit_available > 0:
                        tasks.append(llmArgs.main_db_client.execute(
                            query="UPDATE company_info SET credit_available = credit_available - 1 WHERE company_key = %s AND credit_available > 0",
                            params=(llmArgs.company_key)
                        ))
                    # io니까 비동기로 동시에
                    await asyncio.gather(*tasks)

                    # 첫번째 답변 떨어졌을 때 시간 체크 및 기타 상태값 변경
                    is_first_chunk = False
                    time_from_proxy = time.time()
                    elapsed = timedelta(seconds=float(time_from_proxy - llmArgs.start_time))
                    logging.info(f"session_key: {llmArgs.session_key} | [TIMETEST] ⏱️ TIME from proxy: {elapsed}")
                    llmArgs.time_info["ElapsedFromProxy"] = elapsed.total_seconds()

                # 현재는 텍스트만 보냄
                if chunk.get("text"):
                    yield chunk["text"]

    except DBError as e:
        logging.info(f"session_key: {llmArgs.session_key} | [llm.proxy.run_llm] 🔴 DBError: {e}")
        raise DBError(e)
    except MemoryDBError as e:
        logging.info(f"session_key: {llmArgs.session_key} | [llm.proxy.run_llm] 🔴 MemoryDBError: {e}")
        raise MemoryDBError(e)
    except VectorDBError as e:
        logging.info(f"session_key: {llmArgs.session_key} | [llm.proxy.run_llm] 🔴 VectorDBError: {e}")
        raise VectorDBError(e)
    except AWSError as e:
        logging.info(f"session_key: {llmArgs.session_key} | [llm.proxy.run_llm] 🔴 AWSError: {e}")
        raise AWSError(e)
    except LLMStreamingError as e:
        logging.info(f"session_key: {llmArgs.session_key} | [llm.proxy.run_llm] 🔴 LLMStreamingError: {e}")
        raise LLMStreamingError(e)
    except Exception as e:
        logging.info(f"session_key: {llmArgs.session_key} | [llm.proxy.run_llm] 🔴 Exception: {e}")
        raise e


async def callback(args:LLMArgs):
    try:
        end_time = time.time()
        elapsed = timedelta(seconds=float(end_time - args.start_time))
        logging.info(f"session_key: {args.session_key} | [TIMETEST] ⏱️ TIME to callback: {elapsed}")
        args.time_info["ElapsedAtCallback"] = elapsed.total_seconds()

        reg_date = datetime.now(timezone('UTC'))

        data_redis = redis_format(role="ai", message=args.message, id=args.answer_id)
        await args.memory_db_client.rpush(args.session_key, data_redis)
        await args.memory_db_client.expire(args.session_key, 1800)

        data = make_chat_history_data(
            args.chat_info, role="ai",
            message=args.message,
            token=get_token_length(args.message),
            reg_date=reg_date,
            id=args.answer_id,
            elapsed_info=str(args.time_info)
        )
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        insert_query = f"""INSERT INTO chat_history ({columns}) VALUES ({placeholders})"""
        task = [args.main_db_client.execute(query=insert_query, params=tuple(data.values()))]

        chat_title_row = await args.main_db_client.fetch_one(
            query="SELECT EXISTS(SELECT 1 FROM chat_title WHERE session_key = %s)",
            params=(args.session_key)
        )
        if chat_title_row[0]:
            update_query = "UPDATE chat_title SET update_date = %s WHERE session_key = %s"
            params = (reg_date, args.session_key)
            task.append(args.main_db_client.execute(query=update_query, params=params))
        if args.credit_available and args.credit_available > 0:
            task.append(record_credit_history(args.main_db_client, args.company_key, args.credit_available, reg_date))
        await asyncio.gather(*task)

        logging.info(f"[answer_id: {args.answer_id}, session_key: {args.session_key}] ⏱️ WHOLE PROCESS ELAPSED INFO: {str(args.time_info)}")

    except DBError as e:
        logging.info(f"session_key: {args.session_key} | [module.LLM.run.callback] 🔴 DBError: {e}")
    except MemoryDBError as e:
        logging.info(f"session_key: {args.session_key} | [module.LLM.run.callback] 🔴 MemoryDBError: {e}")
    except AWSError as e:
        logging.info(f"session_key: {args.session_key} | [module.LLM.run.callback] 🔴 AWSError: {e}")
    except Exception as e:
        logging.info(f"session_key: {args.session_key} | [module.LLM.run.callback] 🔴 Exception: {e}")
