export enum Enums {
  // Kafka Event Types
  FILE_EMBEDDING_CREATE = 'FILE_EMBEDDING_CREATE',
  USER_PROMPT_CREATE = 'USER_PROMPT_CREATE',

  // Kafka Topics
  TOPIC_EMBEDDING_CREATE = 'embedding.create',
  TOPIC_USER_PROMPT = 'document.query',
  TOPIC_LLM_RESPONSE = 'llm.response',
  // Services
  PYTHON_AI_SERVICE = 'python-ai-service',
  NODE_API_SERVICE = 'node-api-service',
}
