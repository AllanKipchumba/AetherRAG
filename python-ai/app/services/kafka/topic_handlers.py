from .kafka_handlers import handle_embedding_create, handle_document_query
from .kafka_topics import KafkaTopics

TOPIC_HANDLERS = {
    KafkaTopics.EMBEDDING_CREATE.value: handle_embedding_create,
    KafkaTopics.DOCUMENT_QUERY.value: handle_document_query,
}
