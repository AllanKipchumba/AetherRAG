import json
import uuid
import asyncio
import inspect
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, TypedDict, Union, Awaitable
from dataclasses import dataclass, asdict
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import logging
import os



# Configure logging
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
logger = logging.getLogger(__name__)

class Metadata(TypedDict):
    correlationId: str
    retryCount: int
    priority: str  # 'normal' | 'high' | 'low'

@dataclass
class EventMessage:
    messageId: str
    timestamp: str
    source: str
    destination: Optional[str]
    eventType: str
    version: str
    payload: Any
    metadata: Metadata

# Type alias for message handler (now supports both sync and async)
MessageHandler = Union[
    Callable[[str, EventMessage, Dict[str, bytes]], None],
    Callable[[str, EventMessage, Dict[str, bytes]], Awaitable[None]]
]

class KafkaMessageQueue:
    def __init__(self, config_dict=None):
        """
        Initialize Kafka client with configuration
        
        Args:
            config_dict: Optional config dictionary. If None, uses global kafka_config.
        """
        if config_dict is None:
            config_dict = {
                'service_name': os.getenv('KAFKA_SERVICE_NAME'),
                'brokers': os.getenv('KAFKA_BROKERS', 'localhost:9092').split(','),
                'client_id': os.getenv('KAFKA_CLIENT_ID', 'default-client'),
                'ca': os.getenv('KAFKA_SSL_CA'),
                'cert': os.getenv('KAFKA_SSL_CERT'),
                'key': os.getenv('KAFKA_SSL_KEY')
        }
            
        self.kafka_config = config_dict
        self.service_name = config_dict['service_name']
        
        # Producer configuration
        producer_config = {
            'bootstrap_servers': config_dict['brokers'],
            'client_id': config_dict['client_id'],
            'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
            'key_serializer': lambda k: k.encode('utf-8') if k else None,
            'acks': 'all',  # Equivalent to idempotent=true
            'retries': 8,
            'max_in_flight_requests_per_connection': 1,
            'enable_idempotence': True,
            'request_timeout_ms': 30000,
        }
        
        # Add SSL configuration if provided
        if config_dict['ca']:
            producer_config.update({
                'security_protocol': 'SSL',
                'ssl_check_hostname': True,
                'ssl_cafile': config_dict['ca'],
                'ssl_keyfile': config_dict['key'],
                'ssl_certfile': config_dict['cert'],
            })
        
        self.producer = None
        self.consumer = None
        self.producer_config = producer_config
        
    def connect(self) -> None:
        """Connect the Kafka producer"""
        try:
            self.producer = KafkaProducer(**self.producer_config)
            print("Kafka producer connected")
        except Exception as e:
            logger.error(f"Failed to connect producer: {e}")
            raise
    
    def disconnect(self) -> None:
        """Disconnect producer and consumer"""
        if self.producer:
            self.producer.close()
            print("Kafka producer disconnected")
            
        if self.consumer:
            self.consumer.close()
            print("Kafka consumer disconnected")
    
    def create_message(
        self, 
        event_type: str, 
        payload: Any, 
        destination: Optional[str] = None
    ) -> EventMessage:
        """Create a structured event message"""
        return EventMessage(
            messageId=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat() + 'Z',
            source=self.service_name,
            destination=destination,
            eventType=event_type,
            version='1.0',
            payload=payload,
            metadata=Metadata(
                correlationId=str(uuid.uuid4()),
                retryCount=0,
                priority='normal'
            )
        )
    
    def publish_event(
        self, 
        topic: str, 
        message: EventMessage, 
        key: Optional[str] = None
    ) -> Any:
        """Publish an event to a Kafka topic"""
        if not self.producer:
            raise RuntimeError("Producer not connected. Call connect() first.")
        
        try:
            # Convert dataclass to dict for serialization
            message_dict = asdict(message)
            
            # Prepare headers
            headers = [
                ('event-type', message.eventType.encode('utf-8')),
                ('source', message.source.encode('utf-8')),
                ('timestamp', message.timestamp.encode('utf-8')),
            ]
            
            # Send message
            future = self.producer.send(
                topic=topic,
                key=key or message.messageId,
                value=message_dict,
                headers=headers
            )
            
            # Wait for the message to be sent and get metadata
            record_metadata = future.get(timeout=30)
            
            result = {
                'topic': record_metadata.topic,
                'partition': record_metadata.partition,
                'offset': record_metadata.offset,
                'timestamp': record_metadata.timestamp
            }
            
            print(f"Message published to {topic}: {result}")
            return result
            
        except KafkaError as e:
            logger.error(f"Error publishing message: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error publishing message: {e}")
            raise
    
    async def _call_handler(
        self, 
        handler: MessageHandler, 
        topic: str, 
        event_message: EventMessage, 
        headers: Dict[str, bytes]
    ) -> None:
        """Call handler whether it's sync or async"""
        try:
            if inspect.iscoroutinefunction(handler):
                await handler(topic, event_message, headers)
            else:
                # Run sync handler in a thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, handler, topic, event_message, headers)
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
            raise

    async def subscribe_async(
        self, 
        topics: List[str], 
        group_id: str, 
        message_handler: MessageHandler
    ) -> None:
        """Subscribe to topics and process messages asynchronously"""
        consumer_config = {
            'bootstrap_servers': self.kafka_config['brokers'],
            'group_id': group_id,
            'client_id': self.kafka_config['client_id'],
            'value_deserializer': lambda m: json.loads(m.decode('utf-8')) if m else {},
            'key_deserializer': lambda k: k.decode('utf-8') if k else None,
            'session_timeout_ms': 30000,
            'heartbeat_interval_ms': 3000,
            'auto_offset_reset': 'earliest',
            'enable_auto_commit': True,
        }
        
        # Add SSL configuration if provided
        if self.kafka_config['ca']:
            consumer_config.update({
                'security_protocol': 'SSL',
                'ssl_check_hostname': True,
                'ssl_cafile': self.kafka_config['ca'],
                'ssl_keyfile': self.kafka_config['key'],
                'ssl_certfile': self.kafka_config['cert'],
            })
        
        try:
            self.consumer = KafkaConsumer(*topics, **consumer_config)
            print(f"Subscribed to topics: {topics}")
            
            # Process messages in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            
            def consume_messages():
                """Consume messages synchronously in a separate thread"""
                for message in self.consumer:
                    try:
                        # Parse message value into EventMessage
                        message_data = message.value
                        if not message_data:
                            continue
                        
                        # Convert dict back to EventMessage
                        event_message = EventMessage(**message_data)
                        
                        # Convert headers to dict
                        headers = {}
                        if message.headers:
                            for key, value in message.headers:
                                headers[key] = value
                        
                        # Schedule the handler to run in the event loop
                        asyncio.run_coroutine_threadsafe(
                            self._call_handler(message_handler, message.topic, event_message, headers),
                            loop
                        )
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing message JSON: {e}")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
            
            # Run the consumer in a thread pool
            await loop.run_in_executor(None, consume_messages)
                    
        except Exception as e:
            logger.error(f"Error in consumer: {e}")
            raise

    def subscribe(
        self, 
        topics: List[str], 
        group_id: str, 
        message_handler: MessageHandler
    ) -> None:
        """Subscribe to topics and process messages (synchronous version for backward compatibility)"""
        consumer_config = {
            'bootstrap_servers': self.kafka_config['brokers'],
            'group_id': group_id,
            'client_id': self.kafka_config['client_id'],
            'value_deserializer': lambda m: json.loads(m.decode('utf-8')) if m else {},
            'key_deserializer': lambda k: k.decode('utf-8') if k else None,
            'session_timeout_ms': 30000,
            'heartbeat_interval_ms': 3000,
            'auto_offset_reset': 'earliest',
            'enable_auto_commit': True,
        }
        
        # Add SSL configuration if provided
        if self.kafka_config['ca']:
            consumer_config.update({
                'security_protocol': 'SSL',
                'ssl_check_hostname': True,
                'ssl_cafile': self.kafka_config['ca'],
                'ssl_keyfile': self.kafka_config['key'],
                'ssl_certfile': self.kafka_config['cert'],
            })
        
        try:
            self.consumer = KafkaConsumer(*topics, **consumer_config)
            print(f"Subscribed to topics: {topics}")
            
            # Process messages
            for message in self.consumer:
                try:
                    # Parse message value into EventMessage
                    message_data = message.value
                    if not message_data:
                        continue
                    
                    # Convert dict back to EventMessage
                    event_message = EventMessage(**message_data)
                    
                    # Convert headers to dict
                    headers = {}
                    if message.headers:
                        for key, value in message.headers:
                            headers[key] = value
                    
                    # Call message handler - now handles both sync and async
                    if inspect.iscoroutinefunction(message_handler):
                        # For async handlers, run in new event loop
                        asyncio.run(message_handler(message.topic, event_message, headers))
                    else:
                        # For sync handlers, call directly
                        message_handler(message.topic, event_message, headers)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing message JSON: {e}")
                    # TODO: Implement dead-letter queue / retry logic here
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # TODO: Implement dead-letter queue / retry logic here
                    
        except Exception as e:
            logger.error(f"Error in consumer: {e}")
            raise
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


# Create singleton instance using global config
kafka_message_queue = KafkaMessageQueue()