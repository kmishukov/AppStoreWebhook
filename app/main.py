from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/webhook/appstore")
async def appstore_webhook(request: Request):
    payload = await request.json()
    return {"received": True}