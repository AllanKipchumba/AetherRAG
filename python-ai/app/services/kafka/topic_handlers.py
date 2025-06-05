from .kafka_handlers import handle_embedding_create
from .kafka_topics import KafkaTopics

TOPIC_HANDLERS = {
    KafkaTopics.EMBEDDING_CREATE.value: handle_embedding_create,
}
