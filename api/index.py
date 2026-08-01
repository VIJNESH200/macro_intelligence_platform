import os
import sys

# Ensure project root is on sys.path for serverless environment
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from web.server import app
    handler = app
except Exception as exc:
    from fastapi import FastAPI
    app = FastAPI()
    err_msg = str(exc)
    err_type = type(exc).__name__

    @app.get("/api/{path:path}")
    def catch_all(path: str):
        return {"error": err_msg, "type": err_type}

    handler = app
