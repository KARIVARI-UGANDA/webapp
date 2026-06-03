import os

import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("UVICORN_RELOAD", "0") == "1",
        reload_dirs=["app"] if os.getenv("UVICORN_RELOAD", "0") == "1" else None,
    )