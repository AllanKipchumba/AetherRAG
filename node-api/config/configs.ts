import dotenv from 'dotenv';
dotenv.config();

interface MinioConfig {
  endpoint: string | undefined;
  port: number | undefined;
  accessKey: string | undefined;
  secretKey: string | undefined;
  bucketName: string | undefined;
}

interface Kafka {
  host: string | undefined;
  port: number | undefined;
  service_uri: string | undefined;
  cert: string | undefined;
  key: string | undefined;
  ca: string | undefined;

  client_id: string | undefined;
  brokers: string[] | undefined;
  service_name: string | undefined;
  group_id: string | undefined;
  security_protocol: string | undefined;
  topics: string[] | undefined;
}

interface Config {
  minio: MinioConfig;
  kafka: Kafka;
}

export const config: Config = {
  minio: {
    endpoint: process.env.MINIO_ENDPOINT,
    port: parseInt(process.env.MINIO_PORT || '9000', 10),
    accessKey: process.env.MINIO_ACCESS_KEY,
    secretKey: process.env.MINIO_SECRET_KEY,
    bucketName: process.env.MINIO_BUCKET_NAME,
  },
  kafka: {
    host: process.env.KAFKA_HOST,
    port: parseInt(process.env.KAFKA_PORT!),
    service_uri: process.env.KAFKA_SERVICE_URI,
    cert: process.env.KAFKA_CLIENT_CERT,
    key: process.env.KAFKA_CLIENT_KEY,
    ca: process.env.KAFKA_CA_CERT,
    client_id: process.env.KAFKA_CLIENT_ID,
    brokers: (process.env.KAFKA_BROKERS || '')
      .split(',')
      .map((broker) => broker.trim()),
    service_name: process.env.KAFKA_SERVICE_NAME,
    group_id: process.env.KAFKA_GROUP_ID,
    security_protocol: process.env.KAFKA_SECURITY_PROTOCOL,
    topics: (process.env.KAFKA_TOPICS || '')
      .split(',')
      .map((topic) => topic.trim()),
  },
};
