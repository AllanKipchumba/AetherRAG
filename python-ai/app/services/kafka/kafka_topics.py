from enum import Enum

class KafkaTopics(Enum):
    """Kafka topic names"""
    EMBEDDING_CREATE = "embedding.create"
    DOCUMENT_QUERY = "document.query"
    DOCUMENT_RESPONSE = "document.response"
    
    EMBEDDING_COMPLETE = "embedding.complete"
    QUERY_COMPLETE = "query.complete"
    ERROR_NOTIFICATION = "error.notification"