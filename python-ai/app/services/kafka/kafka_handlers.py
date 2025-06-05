from .kafka_client import EventMessage
from typing import Dict

def handle_embedding_create(topic: str, message: EventMessage, headers: Dict[str, bytes]) -> None:
    """Example message handler function"""
    print(f"Received message on topic {topic}:")
    print(f"  Event Type: {message.eventType}")
    print(f"  Source: {message.source}")
    print(f"  Payload: {message.payload}")
    print(f"  Headers: {headers}")
