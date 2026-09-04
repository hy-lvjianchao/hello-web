import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

PORT = int(os.getenv("PORT", "80"))
S3_FILES_PATH = os.getenv("S3_FILES_PATH", "/mnt/s3files")

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(
            f"{datetime.now().isoformat()} "
            f"{self.client_address[0]} "
            f"{self.requestline} "
            f"{format % args}",
            flush=True
        )
    def send_json(self, status_code, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        # ========================================
        # 1. Web ALB HealthCheck
        # GET /health
        # ========================================
        if self.path == "/health":
            self.send_json(
                200,
                {
                    "status": "UP",
                    "service": "web",
                    "timestamp": datetime.now().isoformat()
                }
            )
            return
        # ========================================
        # 2. AP Service Connect HealthCheck
        # GET /actuator/health
        # ========================================
        if self.path == "/actuator/health":
            self.send_json(
                200,
                {
                    "status": "UP",
                    "service": "ap",
                    "timestamp": datetime.now().isoformat()
                }
            )
            return
        # ========================================
        # 3. S3 Files mount check
        # GET /s3-health
        # ========================================
        if self.path == "/s3-health":
            if not os.path.exists(S3_FILES_PATH):
                self.send_json(
                    500,
                    {
                        "status": "DOWN",
                        "message": "S3 Files mount directory does not exist",
                        "path": S3_FILES_PATH
                    }
                )
                return
            if not os.path.isdir(S3_FILES_PATH):
                self.send_json(
                    500,
                    {
                        "status": "DOWN",
                        "message": "S3 Files mount path is not a directory",
                        "path": S3_FILES_PATH
                    }
                )
                return
            try:
                files = os.listdir(S3_FILES_PATH)

                self.send_json(
                    200,
                    {
                        "status": "UP",
                        "path": S3_FILES_PATH,
                        "files": files
                    }
                )
            except Exception as e:
                self.send_json(
                    500,
                    {
                        "status": "DOWN",
                        "message": str(e),
                        "path": S3_FILES_PATH
                    }
                )
            return
        # ========================================
        # 4. S3 Files write/read test
        # GET /s3-test
        # ========================================
        if self.path == "/s3-test":
            test_file = os.path.join(
                S3_FILES_PATH,
                "ecs-test.txt"
            )
            test_content = (
                "Hello from ECS Fargate!\n"
                f"Time: {datetime.now().isoformat()}\n"
            )
            try:
                # Write
                with open(test_file, "w") as f:
                    f.write(test_content)
                # Read
                with open(test_file, "r") as f:
                    read_content = f.read()
                self.send_json(
                    200,
                    {
                        "status": "UP",
                        "message": "S3 Files read/write test succeeded",
                        "file": test_file,
                        "content": read_content
                    }
                )
            except Exception as e:
                self.send_json(
                    500,
                    {
                        "status": "DOWN",
                        "message": str(e),
                        "file": test_file
                    }
                )

            return
        # ========================================
        # 5. Default page
        # ========================================
        if self.path == "/":
            body = b"Hello World from ECS!"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()

            self.wfile.write(body)
            return
        # ========================================
        # 6. 404
        # ========================================
        self.send_json(
            404,
            {
                "status": "NOT_FOUND",
                "path": self.path
            }
        )

def main():
    server = HTTPServer(("0.0.0.0", PORT), Handler)

    print(f"Starting ECS test server on port {PORT}")
    print(f"S3 Files path: {S3_FILES_PATH}")

    server.serve_forever()


if __name__ == "__main__":
    main()
