from .kafka_client import EventMessage
from typing import Dict
from ..embedding.embedding_service import download_document, extract_text_from_pdf, embedding_model, collection
import asyncio

def handle_embedding_create(topic: str, message: EventMessage, headers: Dict[str, bytes]) -> None:
    print(f"Received message on topic {topic}:")
    print(f"  Event Type: {message.eventType}")
    print(f"  Source: {message.source}")
    print(f"  Payload: {message.payload}")
    print(f"  Headers: {headers}")

    payload = message.payload
    document_url = payload.get("url")
    object_name = payload.get("objectName")

    asyncio.create_task(process_embedding(document_url, object_name))

async def process_embedding(url: str, doc_id: str):
    try:
        file_path = await download_document(url)
        text = extract_text_from_pdf(file_path)
        embedding = embedding_model.encode(text)

        # Store in ChromaDB
        collection.add(
            documents=[text],
            embeddings=[embedding.tolist()],
            ids=[doc_id],
            metadatas=[{"source": "kafka", "filename": doc_id}]
        )

        print(f"[+]Embedding for {doc_id} stored successfully.")

    except Exception as e:
        print(f"[-]Error processing embedding: {e}")
