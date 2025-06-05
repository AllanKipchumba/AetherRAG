from enum import Enum

class KafkaTopics(str, Enum):
    EMBEDDING_CREATE = "embedding.create"
