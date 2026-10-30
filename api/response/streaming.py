import time
import asyncio
import uuid
from datetime import timedelta

from fastapi.responses import StreamingResponse

from utils.error import *



class ResponseQueue:
    def __init__(self, request_id: str):
        self.event = asyncio.Event()
        self.queue = asyncio.Queue()
        self.request_id = request_id or uuid.uuid4()


def get_response_queue():
    return ResponseQueue(request_id=str(uuid.uuid4()))


async def streaming_response(
        response: ResponseQueue,
        generator,
        answer_id:str=None,
        is_error:bool=None,
        start_time=None,
        session_key:str=None
):
    try:
        asyncio.create_task(make_response_with_queue(
            response=response,
            generator=generator
        ))
        await response.event.wait()
        if start_time:
            time_first_chunk_in_queue = time.time()
            elapsed = timedelta(seconds=int(time_first_chunk_in_queue - start_time))
            logging.info(f"session_key: {session_key} | [TIMETEST] ⏱️ TIME from queue: {elapsed}")
        return StreamingResponse(
            stream_from_queue(response),
            headers={
                "Content-Type": "text/event-stream; charset=utf-8",
                "Cache-Control": "no-cache",
                "Transfer-Encoding": "chunked",
                "id": answer_id if answer_id else "",
                "askCode": "200" if not is_error else "599",
                "Request-Id": response.request_id
            },
            media_type="text/event-stream"
        )

    except DBError as e:
        logging.info(f"[helper.question.streaming_response] 🔴 DBError: {e}")
        raise LLMStreamingError
    except LLMStreamingError as e:
        logging.info(f"[helper.question.streaming_response] 🔴 LLMStreamingError: {e}")
        raise LLMStreamingError
    except MemoryDBError as e:
        logging.info(f"[helper.question.streaming_response] 🔴 MemoryDBError: {e}")
        raise LLMStreamingError
    except VectorDBError as e:
        logging.info(f"[helper.question.streaming_response] 🔴 VectorDBError: {e}")
        raise LLMStreamingError
    except AWSError as e:
        logging.info(f"[helper.question.streaming_response] 🔴 AWSError: {e}")
        raise LLMStreamingError
    except Exception as e:
        logging.info(f"[helper.question.streaming_response] 🔴 error: {e}")
        raise LLMStreamingError


async def make_response_with_queue(response: ResponseQueue, generator):
    try:
        # 대답이 들어오면 대답을 비동기 큐에 넣어준다.
        async for chunk in generator:
            await response.queue.put((response.request_id, chunk))
            if not response.event.is_set():
                response.event.set()
    except DBError as e:
        logging.info(f"[helper.question.streaming_response] 🔴 DBError: {e}")
        raise LLMStreamingError
    except LLMStreamingError as e:
        logging.info(f"[helper.question.streaming_response] 🔴 LLMStreamingError: {e}")
        raise LLMStreamingError
    except MemoryDBError as e:
        logging.info(f"[helper.question.streaming_response] 🔴 MemoryDBError: {e}")
        raise LLMStreamingError
    except VectorDBError as e:
        logging.info(f"[helper.question.streaming_response] 🔴 VectorDBError: {e}")
        raise LLMStreamingError
    except AWSError as e:
        logging.info(f"[helper.question.streaming_response] 🔴 AWSError: {e}")
        raise LLMStreamingError
    except Exception as e:
        logging.info(f"[helper.question.streaming_response] 🔴 error: {e}")
        raise LLMStreamingError
    finally:
        await response.queue.put((response.request_id, None))


async def stream_from_queue(response: ResponseQueue):
    while True:
        request_id, chunk = await response.queue.get()

        if request_id != response.request_id:
            continue

        if chunk is None:
            response.queue.task_done()
            break

        yield chunk
