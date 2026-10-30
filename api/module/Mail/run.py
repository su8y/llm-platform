import time
from datetime import timedelta

from module.Mail.helper import *
from utils.error import *



async def run_email_llm(llmEmailArgs:LLMEmailArgs):
    try:
        # time test
        end_time = time.time()
        elapsed = timedelta(seconds=int(end_time - llmEmailArgs.start_time))
        logging.info(f"session_key: {llmEmailArgs.session_key} | [TIMETEST] ⏱️ TIME to proxy: {elapsed}")

        human_message = make_email_message(
            question=llmEmailArgs.question,
            language_message=llmEmailArgs.language_message,
            email_rag_data=llmEmailArgs.email_rag_data,
            retrieval_data=llmEmailArgs.retrieval_data,
            reference=llmEmailArgs.reference
        )

        # write_log_for_debug_message(
        #     system_message=llmEmailArgs.system_message,
        #     conversation_history=llmEmailArgs.conversation_history,
        #     human_message=human_message
        # )

        is_first_chunk = True
        async for chunk in llmEmailArgs.llm_proxy_client.stream(
            service=llmEmailArgs.service,
            vendor=llmEmailArgs.vendor,
            model=llmEmailArgs.model,
            system_message=llmEmailArgs.system_message,
            human_message=human_message,
            conversation_history=llmEmailArgs.conversation_history if llmEmailArgs.redis_save else [],
            callback=callback,
            callback_args=llmEmailArgs,
            time=float(llmEmailArgs.start_time)
        ):
            if chunk:
                if is_first_chunk:
                    if llmEmailArgs.credit_available and llmEmailArgs.credit_available > 0:
                        await llmEmailArgs.main_db_client.execute(
                            query="""
                                UPDATE company_info
                                SET credit_available = credit_available - 1
                                WHERE company_key = %s
                                    AND credit_available > 0
                            """,
                            params=(llmEmailArgs.company_key)
                        )
                    is_first_chunk = False
                    time_from_proxy = time.time()
                    elapsed = timedelta(seconds=int(time_from_proxy - llmEmailArgs.start_time))
                    logging.info(f"session_key: {llmEmailArgs.session_key} | [TIMETEST] ⏱️ TIME from proxy: {elapsed}")
                if chunk.get("text"):
                    yield chunk["text"]

    except DBError as e:
        logging.info(f"session_key: {llmEmailArgs.session_key} | [llm.proxy.run_llm] 🔴 DBError: {e}")
        raise DBError(e)
    except MemoryDBError as e:
        logging.info(f"session_key: {llmEmailArgs.session_key} | [llm.proxy.run_llm] 🔴 MemoryDBError: {e}")
        raise MemoryDBError(e)
    except VectorDBError as e:
        logging.info(f"session_key: {llmEmailArgs.session_key} | [llm.proxy.run_llm] 🔴 VectorDBError: {e}")
        raise VectorDBError(e)
    except AWSError as e:
        logging.info(f"session_key: {llmEmailArgs.session_key} | [llm.proxy.run_llm] 🔴 AWSError: {e}")
        raise AWSError(e)
    except LLMStreamingError as e:
        logging.info(f"session_key: {llmEmailArgs.session_key} | [llm.proxy.run_llm] 🔴 LLMStreamingError: {e}")
        raise LLMStreamingError(e)
    except Exception as e:
        logging.info(f"session_key: {llmEmailArgs.session_key} | [llm.proxy.run_llm] 🔴 Exception: {e}")
        raise e


async def callback(args:LLMEmailArgs):
    try:
        # elapsed check
        end_time = time.time()
        elapsed = timedelta(seconds=int(end_time - args.start_time))
        logging.info(f"session_key: {args.session_key} | [TIMETEST] ⏱️ TIME to callback: {elapsed}")

        # default db io jobs
        query = """
            UPDATE cx_email
            SET
                status = 'answering'
            WHERE id = %s
        """
        params=(args.id,)
        query_temp = """
            UPDATE cx_email_temp
            SET
                answering_content = %s,
                is_create = %s
            WHERE cx_email_id = %s
        """
        params_temp = (args.message, True, args.id)
        query_record = """
            INSERT INTO cx_email_history (
                company_key,
                cx_email_id,
                user_id,
                action_code,
                reg_date
            ) VALUES (
                %s, %s, %s, %s, %s
            )
        """
        params_record = (args.company_key, args.id, args.user_id, args.action_code, args.current_time)
        tasks = [
            args.main_db_client.execute(query=query, params=params),
            args.main_db_client.execute(query=query_record, params=params_record),
            args.main_db_client.execute(query=query_temp, params=params_temp)
        ]

        # update if manager is not in row
        query_get_manager = """
            SELECT
                CASE
                    WHEN manager IS NULL THEN FALSE
                    ELSE TRUE
                END AS has_manager
            FROM cx_email
            WHERE id = %s
        """
        params_get_manager = (args.id,)
        row = await args.main_db_client.fetch_one(query=query_get_manager, params=params_get_manager)
        if not row[0]:
            query_update_manager = """UPDATE cx_email SET manager = %s WHERE id = %s"""
            params_update_manager = (args.user_id, args.id)
            tasks.append(args.main_db_client.execute(query=query_update_manager, params=params_update_manager))

        await asyncio.gather(*tasks)

    except DBError as e:
        logging.info(f"session_key: {args.session_key} | [module.LLM.run.callback] 🔴 DBError: {e}")
    except MemoryDBError as e:
        logging.info(f"session_key: {args.session_key} | [module.LLM.run.callback] 🔴 MemoryDBError: {e}")
    except AWSError as e:
        logging.info(f"session_key: {args.session_key} | [module.LLM.run.callback] 🔴 AWSError: {e}")
    except Exception as e:
        logging.info(f"session_key: {args.session_key} | [module.LLM.run.callback] 🔴 Exception: {e}")
