from .kafka_client import EventMessage
from typing import Dict
from ..embedding.embedding_service import download_document, embedding_model, collection
from ..llm.openai_service import OpenAIService, DocumentRetriever, DocumentContext
from ..utils.extract_text import extract_text_from_pdf
from typing import Dict, Optional
import logging
from  .kafka_client import kafka_message_queue

# Set up logging
logger = logging.getLogger(__name__)

async def handle_embedding_create(topic: str, message: EventMessage, headers: Dict[str, bytes]) -> None:
    """Async handler for embedding creation events"""
    logger.info(f"Received message on topic {topic}:")
    logger.info(f"  Event Type: {message.eventType}")
    logger.info(f"  Source: {message.source}")
    logger.info(f"  Payload: {message.payload}")
    logger.info(f"  Headers: {headers}")

    payload = message.payload
    document_url = payload.get("url")
    object_name = payload.get("objectName")

    if not document_url or not object_name:
        logger.error("Missing required fields: url or objectName")
        return

    # Now you can directly await since this function is async
    await process_embedding(document_url, object_name)

async def process_embedding(url: str, doc_id: str):
    """Process document embedding asynchronously"""
    try:
        logger.info(f"Starting embedding processing for {doc_id}")
        
        # Download document
        file_path = await download_document(url)
        logger.info(f"Document downloaded: {file_path}")
        
        # Extract text from PDF
        text = extract_text_from_pdf(file_path)
        logger.info(f"Text extracted, length: {len(text)} characters")
        
        # Create embedding
        embedding = embedding_model.encode(text)
        logger.info(f"Embedding created, shape: {embedding.shape}")

        # Store in ChromaDB
        collection.add(
            documents=[text],
            embeddings=[embedding.tolist()],
            ids=[doc_id],
            metadatas=[{"source": "kafka", "filename": doc_id}]
        )

        logger.info(f"[+] Embedding for {doc_id} stored successfully.")

    except Exception as e:
        logger.error(f"[-] Error processing embedding for {doc_id}: {e}")
       

# Initialize services
openai_service = OpenAIService()
document_retriever = DocumentRetriever(collection, embedding_model)

async def handle_document_query(topic: str, message: EventMessage, headers: Dict[str, bytes]) -> None:
    """
    Handle document query requests
    
    Expected payload structure:
    {
        "document_id": "optional_specific_document_id",
        "user_prompt": "user's question or prompt",
        "query_type": "specific_document" | "semantic_search",
        "search_params": {
            "n_results": 3,
            "similarity_threshold": 0.7
        },
        "llm_params": {
            "max_tokens": 1000,
            "temperature": 0.7,
            "system_message": "optional system message"
        }
    }
    """
    logger.info(f"Received document query on topic {topic}:")
    logger.info(f"  Event Type: {message.eventType}")
    logger.info(f"  Source: {message.source}")
    logger.info(f"  Message ID: {message.messageId}")
    
    try:
        payload = message.payload
        
        # Extract required fields
        user_prompt = payload.get("user_prompt")
        if not user_prompt:
            logger.error("Missing required field: user_prompt")
            return
        
        # Extract optional fields
        document_id = payload.get("document_id")
        query_type = payload.get("query_type", "semantic_search")
        search_params = payload.get("search_params", {})
        llm_params = payload.get("llm_params", {})
        
        logger.info(f"Processing query: '{user_prompt[:100]}...' (type: {query_type})")
        
        # Process the query
        await process_document_query(
            user_prompt=user_prompt,
            document_id=document_id,
            query_type=query_type,
            search_params=search_params,
            llm_params=llm_params,
            correlation_id=message.metadata.get("correlationId")
        )
        
    except Exception as e:
        logger.error(f"Error handling document query: {e}")
        # TODO: Send error response back or to dead letter queue
        raise

async def process_document_query(
    user_prompt: str,
    document_id: Optional[str] = None,
    query_type: str = "semantic_search",
    search_params: Dict = None,
    llm_params: Dict = None,
    correlation_id: Optional[str] = None
) -> None:
    """
    Process document query and generate LLM response
    
    Args:
        user_prompt: User's question or prompt
        document_id: Specific document ID (if query_type is "specific_document")
        query_type: Type of query ("specific_document" or "semantic_search")
        search_params: Parameters for semantic search
        llm_params: Parameters for LLM generation
        correlation_id: Correlation ID for tracking
    """
    try:
        # Set default parameters
        search_params = search_params or {}
        llm_params = llm_params or {}
        
        # Retrieve document context
        context_documents = []
        
        if query_type == "specific_document" and document_id:
            # Retrieve specific document
            logger.info(f"Retrieving specific document: {document_id}")
            doc = document_retriever.get_document_by_id(document_id)
            if doc:
                context_documents.append(doc)
                logger.info(f"Retrieved document {document_id} ({len(doc.content)} characters)")
            else:
                logger.warning(f"Document {document_id} not found")
                
        elif query_type == "semantic_search":
            # Perform semantic search
            logger.info(f"Performing semantic search for: '{user_prompt[:50]}...'")
            n_results = search_params.get("n_results", 3)
            similarity_threshold = search_params.get("similarity_threshold", 0.7)
            
            context_documents = document_retriever.search_similar_documents(
                query=user_prompt,
                n_results=n_results,
                similarity_threshold=similarity_threshold,
            )
            
            logger.info(f"Found {len(context_documents)} relevant documents")
            for doc in context_documents:
                logger.info(f"  - {doc.document_id} (similarity: {doc.similarity_score:.3f})")
        
        else:
            logger.warning(f"Unknown query_type: {query_type}")
        
        # Generate LLM response
        logger.info("Generating LLM response...")
        
        # Prepare LLM parameters
        max_tokens = llm_params.get("max_tokens", 1000)
        temperature = llm_params.get("temperature", 0.7)
        system_message = llm_params.get("system_message")
        
        # Default system message for document queries
        if not system_message:
            system_message = """You are a helpful assistant that answers questions based on provided document context. 
                Be accurate and cite specific information from the documents when possible. 
                If the provided context doesn't contain enough information to answer the question completely, 
                clearly state what information is missing."""
        
        response = await openai_service.generate_response(
            prompt=user_prompt,
            context=context_documents,
            max_tokens=max_tokens,
            temperature=temperature,
            system_message=system_message
        )
        
        logger.info(f"LLM response generated ({len(response.content)} characters)")
        logger.info(f"Token usage: {response.usage}")
        
        # TODO: Send response back via Kafka or store in database
        logger.info("=== LLM RESPONSE ===")
        logger.info(f"Prompt: {user_prompt}")
        logger.info(f"Response: {response.content}")
        logger.info(f"Model: {response.model}")
        logger.info(f"Finish reason: {response.finish_reason}")
        logger.info("==================")
        
        # publish the response to another Kafka topic
        llm_event = kafka_message_queue.create_message(
            event_type="llm.response",
            payload={
                "prompt": user_prompt,
                "response": response.content,
                "model": response.model,
                "finish_reason": response.finish_reason,
            }
        )

        # Publish to Kafka topic "llm.response"
        kafka_message_queue.publish_event("llm.response", llm_event)

        
    except Exception as e:
        logger.error(f"Error processing document query: {e}")
        # TODO: Handle errors appropriately (retry, dead letter queue, etc.)
        raise
