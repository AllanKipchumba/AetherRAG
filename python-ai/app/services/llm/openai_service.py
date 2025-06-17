import openai
import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from chromadb import Collection
from dotenv import load_dotenv
load_dotenv()


logger = logging.getLogger(__name__)

@dataclass
class LLMResponse:
    """Response from LLM service"""
    content: str
    model: str
    usage: Dict[str, Any]
    finish_reason: str

@dataclass
class DocumentContext:
    """Document context for LLM prompts"""
    document_id: str
    content: str
    metadata: Dict[str, Any]
    similarity_score: float

class OpenAIService:
    """Service for interacting with OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize OpenAI service
        
        Args:
            api_key: OpenAI API key (if None, reads from OPENAI_API_KEY env var)
            model: OpenAI model to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        openai.api_key = self.api_key
        self.model = model
        self.client = openai.OpenAI(api_key=self.api_key)
        
    async def generate_response(
        self, 
        prompt: str, 
        context: Optional[List[DocumentContext]] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_message: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate response from OpenAI
        
        Args:
            prompt: User prompt
            context: Document context to include
            max_tokens: Maximum tokens in response
            temperature: Response creativity (0-1)
            system_message: System message to set behavior
            
        Returns:
            LLMResponse object
        """
        try:
            messages = []
            
            # Add system message if provided
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            # Prepare context if documents provided
            if context and len(context) > 0:
                context_text = self._prepare_context(context)
                enhanced_prompt = f"""Based on the following document context, please answer the user's question:

                    DOCUMENT CONTEXT:
                    {context_text}

                    USER QUESTION:
                    {prompt}

                    Please provide a comprehensive answer based on the document context. If the context doesn't contain enough information to fully answer the question, please mention what additional information might be needed."""
            else:
                enhanced_prompt = prompt
            
            messages.append({"role": "user", "content": enhanced_prompt})
            
            logger.info(f"Sending request to OpenAI model: {self.model}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage=response.usage.model_dump() if response.usage else {},
                finish_reason=response.choices[0].finish_reason
            )
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            raise Exception(f"Failed to generate LLM response: {e}")
    
    def _prepare_context(self, context: List[DocumentContext]) -> str:
        """
        Format document context for LLM prompt
        
        Args:
            context: List of document contexts
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, doc in enumerate(context, 1):
            context_part = f"""
                Document {i} (ID: {doc.document_id}, Similarity: {doc.similarity_score:.3f}):
                {doc.content}
                """
            if doc.metadata.get("filename"):
                context_part = f"""
                Document {i} - {doc.metadata['filename']} (ID: {doc.document_id}, Similarity: {doc.similarity_score:.3f}):
                {doc.content}
                """
            
            context_parts.append(context_part)
        
        return "\n" + "="*80 + "\n".join(context_parts) + "\n" + "="*80

class DocumentRetriever:
    """Service for retrieving documents from ChromaDB"""
    
    def __init__(self, collection: Collection, embedding_model):
        """
        Initialize document retriever
        
        Args:
            collection: ChromaDB collection
            embedding_model: SentenceTransformer model for embeddings
        """
        self.collection = collection
        self.embedding_model = embedding_model
    
    def get_document_by_id(self, document_id: str) -> Optional[DocumentContext]:
        """
        Retrieve a specific document by ID
        
        Args:
            document_id: Document ID to retrieve
            
        Returns:
            DocumentContext if found, None otherwise
        """
        try:
            result = self.collection.get(
                ids=[document_id],
                include=["documents", "metadatas"]
            )
            
            if not result["ids"] or len(result["ids"]) == 0:
                logger.warning(f"Document {document_id} not found in collection")
                return None
            
            return DocumentContext(
                document_id=document_id,
                content=result["documents"][0],
                metadata=result["metadatas"][0] if result["metadatas"] else {},
                similarity_score=1.0  # Exact match
            )
            
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {e}")
            return None
    
    def search_similar_documents(
        self, 
        query: str, 
        n_results: int = 3,
        similarity_threshold: float = 0.7
    ) -> List[DocumentContext]:
        """
        Search for similar documents using vector similarity
        
        Args:
            query: Search query
            n_results: Number of results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of similar documents
        """
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_model.encode(query)
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
                
            )
            
            documents = []
            
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    # Convert distance to similarity (assuming cosine distance)
                    distance = results["distances"][0][i] if results["distances"] else 0
                    similarity = 1 - distance  # Convert distance to similarity
                    
                    if similarity >= similarity_threshold:
                        documents.append(DocumentContext(
                            document_id=results["ids"][0][i],
                            content=results["documents"][0][i],
                            metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                            similarity_score=similarity
                        ))
            
            return documents
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {e}")
            return []