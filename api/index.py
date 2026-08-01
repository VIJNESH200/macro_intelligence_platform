import os
import sys

# Ensure project root is on sys.path for serverless environment
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from web.server import app  # noqa: F401, E402

handler = app
