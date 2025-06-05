from fastapi import FastAPI
from contextlib import asynccontextmanager
from .services.kafka.kafka_client import kafka_message_queue
from .services.kafka.topic_handlers import TOPIC_HANDLERS
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("FastAPI app has started!")

    # Connect Kafka producer
    kafka_message_queue.connect()

    # Subscribe to Kafka topics with handlers
    for topic, handler in TOPIC_HANDLERS.items():
        if topic in [".", ".."] or not topic.strip():
            continue
        asyncio.get_event_loop().run_in_executor(
            None,
            kafka_message_queue.subscribe,
            [topic],
            "python-ai-consumer-group",
            handler
        )

    yield  # App is running

    # Cleanup on shutdown
    kafka_message_queue.disconnect()
    print("FastAPI app has shut down!")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}
