import json
import threading
import time
from http.client import HTTPConnection
from http.server import HTTPServer

import app


def start_test_server():
    server = HTTPServer(("127.0.0.1", 0), app.Handler)

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True
    )
    thread.start()

    return server


def request(server, path):
    host, port = server.server_address

    conn = HTTPConnection(host, port)
    conn.request("GET", path)

    response = conn.getresponse()
    body = response.read().decode("utf-8")

    conn.close()

    return response.status, json.loads(body)


def test_health():
    server = start_test_server()

    try:
        status, body = request(server, "/health")

        assert status == 200
        assert body["status"] == "UP"
        assert body["service"] == "web"
        assert "timestamp" in body

    finally:
        server.shutdown()


def test_actuator_health():
    server = start_test_server()

    try:
        status, body = request(server, "/actuator/health")

        assert status == 200
        assert body["status"] == "UP"
        assert body["service"] == "ap"
        assert "timestamp" in body

    finally:
        server.shutdown()


def test_not_found():
    server = start_test_server()

    try:
        status, body = request(server, "/test")

        assert status == 404
        assert body["status"] == "NOT_FOUND"

    finally:
        server.shutdown()