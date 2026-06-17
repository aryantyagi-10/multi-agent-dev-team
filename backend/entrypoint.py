import threading
import uvicorn

from backend.worker import run_worker


def start_worker():
    run_worker()


if __name__ == "__main__":
    # Worker in a daemon thread; API in the main thread.
    t = threading.Thread(target=start_worker, daemon=True)
    t.start()
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, workers=1)
