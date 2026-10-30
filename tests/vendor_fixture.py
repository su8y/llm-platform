"""Deterministic HTTP provider for integration tests; never performs inference."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock


REQUESTS = {"embeddings": [], "chats": []}
REQUEST_LOCK = Lock()


def vector(text: str) -> list[float]:
    values = [0.0] * 1024
    values[1 if "CD456" in text else 0] = 1.0
    return values


class VendorHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass

    def send_json(self, status: int, value: object) -> None:
        body = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_json(200, {"ready": True})
        elif self.path == "/stats":
            with REQUEST_LOCK:
                self.send_json(200, REQUESTS)
        else:
            self.send_json(404, {})

    def do_POST(self) -> None:
        payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")
        if self.path == "/reset":
            with REQUEST_LOCK:
                REQUESTS["embeddings"].clear()
                REQUESTS["chats"].clear()
            self.send_json(200, {})
        elif self.path == "/embeddings":
            text = payload["texts"]
            with REQUEST_LOCK:
                REQUESTS["embeddings"].append(text)
            self.send_json(200, [vector(item) for item in text] if isinstance(text, list) else vector(text))
        elif self.path == "/v1/chat/completions":
            context = json.loads(payload["messages"][-1]["content"])
            with REQUEST_LOCK:
                REQUESTS["chats"].append(context)
            answer = "invalid JSON" if context["question"] == "INVALID_DECISION" else json.dumps({"query": "CD456"})
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            # Split the decision across provider chunks to exercise NDJSON assembly.
            for text in (answer[:len(answer) // 2], answer[len(answer) // 2:]):
                chunk = {
                    "id": "fixture", "object": "chat.completion.chunk", "created": 0,
                    "model": "fixture", "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}],
                }
                self.wfile.write(b"data: " + json.dumps(chunk).encode() + b"\n\n")
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        else:
            self.send_json(404, {})


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), VendorHandler).serve_forever()
