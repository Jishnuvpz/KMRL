"""
Simple test FastAPI server to debug shutdown issue
"""
from fastapi import FastAPI

app = FastAPI(title="Test Server")


@app.get("/")
def root():
    return {"message": "Test server is working", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)
