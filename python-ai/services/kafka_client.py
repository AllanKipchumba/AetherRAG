# kafka_client.py
import json
import uuid
from datetime import datetime
from typing import Dict, List, Callable, Optional
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import logging

logger = logging.getLogger(__name__)

class KafkaMessageQueue:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.brokers = self.config.get('brokers', ['localhost:9092'])
        self.service_name = self.config.get('service_name', 'python-service')
        
        self.producer = KafkaProducer(
            bootstrap_servers=self.brokers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=5,
            enable_idempotence=True
        )
        
        self.consumers = {}

    def create_message(self, event_type: str, payload: Dict, destination: str = None) -> Dict:
        return {
            'messageId': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'source': self.service_name,
            'destination': destination,
            'eventType': event_type,
            'version': '1.0',
            'payload': payload,
            'metadata': {
                'correlationId': str(uuid.uuid4()),
                'retryCount': 0,
                'priority': 'normal'
            }
        }

    def publish_event(self, topic: str, message: Dict, key: str = None) -> bool:
        try:
            future = self.producer.send(
                topic=topic,
                value=message,
                key=key or message['messageId'],
                headers=[
                    ('event-type', message['eventType'].encode('utf-8')),
                    ('source', message['source'].encode('utf-8')),
                    ('timestamp', message['timestamp'].encode('utf-8'))
                ]
            )
            
            # Block for synchronous sends
            result = future.get(timeout=10)
            logger.info(f"Message published to {topic}: {result}")
            return True
            
        except KafkaError as e:
            logger.error(f"Error publishing message: {e}")
            return False

    def subscribe(self, topics: List[str], group_id: str, message_handler: Callable):
        consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=self.brokers,
            group_id=group_id,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            session_timeout_ms=30000,
            heartbeat_interval_ms=3000
        )
        
        self.consumers[group_id] = consumer
        
        for message in consumer:
            try:
                headers = {k: v.decode('utf-8') for k, v in message.headers}
                message_handler(message.topic, message.value, headers)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Implement DLQ logic here

    def close(self):
        self.producer.close()
        for consumer in self.consumers.values():
            consumer.close()