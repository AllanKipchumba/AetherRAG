from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print("FastAPI app has started!")

@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}
