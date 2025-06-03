import dotenv from 'dotenv';
dotenv.config();

interface MinioConfig {
  endpoint?: string;
  port?: number;
  accessKey?: string;
  secretKey?: string;
  bucketName?: string;
}

interface Config {
  minio: MinioConfig;
}

export const config: Config = {
  minio: {
    endpoint: process.env.MINIO_ENDPOINT,
    port: parseInt(process.env.MINIO_PORT || '9000', 10),
    accessKey: process.env.MINIO_ACCESS_KEY,
    secretKey: process.env.MINIO_SECRET_KEY,
    bucketName: process.env.MINIO_BUCKET_NAME,
  },
};
