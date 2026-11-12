"""Start the Vesper web app on http://127.0.0.1:8216 (local only).

    pip install -r requirements-web.txt
    python run_web.py [--port 8216]
"""
import argparse

import uvicorn

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8216)
    a = ap.parse_args()
    print(f"Vesper web app: http://127.0.0.1:{a.port}")
    uvicorn.run("vesper.web.app:app", host="127.0.0.1", port=a.port)
