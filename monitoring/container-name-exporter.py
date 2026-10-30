#!/usr/bin/env python3
"""
Simple exporter that provides container ID to name mappings
"""
import docker
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()

            try:
                client = docker.from_env()
                containers = client.containers.list()

                metrics = []
                for container in containers:
                    container_id = container.id
                    container_name = container.name
                    container_short_id = container.short_id

                    # Create info metric with labels
                    metric = f'container_info{{id="/docker/{container_id}",name="{container_name}",short_id="{container_short_id}"}} 1'
                    metrics.append(metric)

                response = '\n'.join(metrics) + '\n'
                self.wfile.write(response.encode())
            except Exception as e:
                self.wfile.write(f'# Error: {str(e)}\n'.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress logs

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 9998), MetricsHandler)
    print('Container Name Exporter listening on :9998')
    server.serve_forever()