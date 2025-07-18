// import {
//   Kafka,
//   Producer,
//   Consumer,
//   KafkaConfig,
//   ProducerRecord,
//   logLevel,
//   KafkaMessage,
// } from 'kafkajs';
// import { v4 as uuidv4 } from 'uuid';
// import { config } from '../../config/configs';

// interface Metadata {
//   correlationId: string;
//   retryCount: number;
//   priority: 'normal' | 'high' | 'low';
// }

// interface EventMessage<T = any> {
//   messageId: string;
//   timestamp: string;
//   source: string;
//   destination: string | null;
//   eventType: string;
//   version: string;
//   payload: T;
//   metadata: Metadata;
// }

// type MessageHandler = (
//   topic: string,
//   message: EventMessage,
//   headers: KafkaMessage['headers']
// ) => Promise<void>;

// export class KafkaMessageQueue {
//   private kafka: Kafka;
//   private producer: Producer;
//   private consumer: Consumer | null = null;
//   private serviceName: string;

//   constructor() {
//     this.kafka = new Kafka({
//       clientId: config.kafka.client_id,
//       brokers: config.kafka.brokers!,
//       retry: {
//         initialRetryTime: 100,
//         retries: 8,
//       },
//       logLevel: logLevel.ERROR,
//       // ssl: {
//       //   rejectUnauthorized: true,
//       //   ca: config.kafka.ca,
//       //   key: config.kafka.key,
//       //   cert: config.kafka.cert,
//       // },
//     });

//     this.producer = this.kafka.producer({
//       maxInFlightRequests: 1,
//       idempotent: true,
//       transactionTimeout: 30000,
//     });

//     this.serviceName = config.kafka.service_name!;
//   }

//   async connect(): Promise<void> {
//     await this.producer.connect();
//     console.log('Kafka producer connected');
//   }

//   async disconnect(): Promise<void> {
//     await this.producer.disconnect();
//     if (this.consumer) {
//       await this.consumer.disconnect();
//       console.log('Kafka consumer disconnected');
//     }
//   }

//   createMessage<T>(
//     eventType: string,
//     payload: T,
//     destination: string | null = null
//   ): EventMessage<T> {
//     return {
//       messageId: uuidv4(),
//       timestamp: new Date().toISOString(),
//       source: this.serviceName,
//       destination,
//       eventType,
//       version: '1.0',
//       payload,
//       metadata: {
//         correlationId: uuidv4(),
//         retryCount: 0,
//         priority: 'normal',
//       },
//     };
//   }

//   async publishEvent(
//     topic: string,
//     message: EventMessage,
//     key: string | null = null
//   ): Promise<any> {
//     try {
//       const result = await this.producer.send({
//         topic,
//         messages: [
//           {
//             key: key || message.messageId,
//             value: JSON.stringify(message),
//             headers: {
//               'event-type': message.eventType,
//               source: message.source,
//               timestamp: message.timestamp,
//             },
//           },
//         ],
//       });

//       console.log(`Message published to ${topic}:`, result);
//       return result;
//     } catch (error) {
//       console.error('Error publishing message:', error);
//       throw error;
//     }
//   }

//   async subscribe(
//     topics: string[],
//     groupId: string,
//     messageHandler: MessageHandler
//   ): Promise<void> {
//     this.consumer = this.kafka.consumer({
//       groupId,
//       sessionTimeout: 30000,
//       heartbeatInterval: 3000,
//     });

//     await this.consumer.connect();
//     for (const topic of topics) {
//       await this.consumer.subscribe({ topic });
//     }

//     await this.consumer.run({
//       eachMessage: async ({ topic, message }) => {
//         try {
//           const parsedMessage: EventMessage = JSON.parse(
//             message.value?.toString() || '{}'
//           );
//           await messageHandler(topic, parsedMessage, message.headers);
//         } catch (error) {
//           console.error('Error processing message:', error);
//           // dead-letter queue / retry logic here
//         }
//       },
//     });
//   }
// }

// export const kafkaMessageQueue = new KafkaMessageQueue();

import {
  Kafka,
  Producer,
  Consumer,
  KafkaConfig,
  ProducerRecord,
  logLevel,
  KafkaMessage,
} from 'kafkajs';
import { v4 as uuidv4 } from 'uuid';
import { config } from '../../config/configs';

interface Metadata {
  correlationId: string;
  retryCount: number;
  priority: 'normal' | 'high' | 'low';
}

interface EventMessage<T = any> {
  messageId: string;
  timestamp: string;
  source: string;
  destination: string | null;
  eventType: string;
  version: string;
  payload: T;
  metadata: Metadata;
}

type MessageHandler = (
  topic: string,
  message: EventMessage,
  headers: KafkaMessage['headers']
) => Promise<void>;

export class KafkaMessageQueue {
  private kafka: Kafka;
  private producer: Producer;
  private consumers: Map<string, Consumer> = new Map();
  private serviceName: string;
  private isConnected: boolean = false;

  constructor() {
    this.kafka = new Kafka({
      clientId: config.kafka.client_id,
      brokers: config.kafka.brokers!,
      retry: {
        initialRetryTime: 100,
        retries: 8,
      },
      logLevel: logLevel.ERROR,
      // ssl: {
      //   rejectUnauthorized: true,
      //   ca: config.kafka.ca,
      //   key: config.kafka.key,
      //   cert: config.kafka.cert,
      // },
    });

    this.producer = this.kafka.producer({
      maxInFlightRequests: 1,
      idempotent: true,
      transactionTimeout: 30000,
    });

    this.serviceName = config.kafka.service_name!;
  }

  async connect(): Promise<void> {
    if (!this.isConnected) {
      await this.producer.connect();
      this.isConnected = true;
      console.log('Kafka producer connected');
    }
  }

  async disconnect(): Promise<void> {
    if (this.isConnected) {
      await this.producer.disconnect();

      // Disconnect all consumers
      for (const [groupId, consumer] of this.consumers) {
        await consumer.disconnect();
        console.log(`Kafka consumer ${groupId} disconnected`);
      }
      this.consumers.clear();

      this.isConnected = false;
      console.log('Kafka producer disconnected');
    }
  }

  createMessage<T>(
    eventType: string,
    payload: T,
    destination: string | null = null
  ): EventMessage<T> {
    return {
      messageId: uuidv4(),
      timestamp: new Date().toISOString(),
      source: this.serviceName,
      destination,
      eventType,
      version: '1.0',
      payload,
      metadata: {
        correlationId: uuidv4(),
        retryCount: 0,
        priority: 'normal',
      },
    };
  }

  async publishEvent(
    topic: string,
    message: EventMessage,
    key: string | null = null
  ): Promise<any> {
    try {
      if (!this.isConnected) {
        await this.connect();
      }

      const result = await this.producer.send({
        topic,
        messages: [
          {
            key: key || message.messageId,
            value: JSON.stringify(message),
            headers: {
              'event-type': message.eventType,
              source: message.source,
              timestamp: message.timestamp,
              'correlation-id': message.metadata.correlationId,
            },
          },
        ],
      });

      console.log(`Message published to ${topic}:`, result);
      return result;
    } catch (error) {
      console.error('Error publishing message:', error);
      throw error;
    }
  }

  async subscribe(
    topics: string[],
    groupId: string,
    messageHandler: MessageHandler
  ): Promise<void> {
    try {
      // Check if consumer already exists for this group
      if (this.consumers.has(groupId)) {
        console.log(`Consumer for group ${groupId} already exists`);
        return;
      }

      const consumer = this.kafka.consumer({
        groupId,
        sessionTimeout: 30000,
        heartbeatInterval: 3000,
      });

      await consumer.connect();
      console.log(`Kafka consumer ${groupId} connected`);

      for (const topic of topics) {
        await consumer.subscribe({ topic, fromBeginning: false });
        console.log(`Subscribed to topic: ${topic}`);
      }

      // Store consumer reference
      this.consumers.set(groupId, consumer);

      await consumer.run({
        eachMessage: async ({ topic, partition, message }) => {
          try {
            if (!message.value) {
              console.warn('Received empty message value');
              return;
            }

            const parsedMessage: EventMessage = JSON.parse(
              message.value.toString()
            );

            console.log(`Processing message from topic ${topic}:`, {
              messageId: parsedMessage.messageId,
              eventType: parsedMessage.eventType,
              correlationId: parsedMessage.metadata?.correlationId,
            });

            await messageHandler(topic, parsedMessage, message.headers);
          } catch (error) {
            console.error('Error processing message:', error);
            // TODO: Implement dead-letter queue / retry logic here
          }
        },
      });
    } catch (error) {
      console.error(`Error setting up consumer for group ${groupId}:`, error);
      throw error;
    }
  }

  // Method to get all active consumers (for monitoring)
  getActiveConsumers(): string[] {
    return Array.from(this.consumers.keys());
  }

  // Method to check if connected
  isProducerConnected(): boolean {
    return this.isConnected;
  }
}

export const kafkaMessageQueue = new KafkaMessageQueue();

// Graceful shutdown handling
process.on('SIGINT', async () => {
  console.log('Shutting down Kafka connections...');
  await kafkaMessageQueue.disconnect();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('Shutting down Kafka connections...');
  await kafkaMessageQueue.disconnect();
  process.exit(0);
});
