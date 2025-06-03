import { Client, ClientOptions } from 'minio';
import { config } from '../../config/configs';

class MinioService {
  private client: Client;
  private bucketName: string;

  constructor() {
    const options: ClientOptions = {
      endPoint: config.minio.endpoint!,
      port: config.minio.port,
      useSSL: false,
      accessKey: config.minio.accessKey,
      secretKey: config.minio.secretKey,
    };

    this.client = new Client(options);
    this.bucketName = config.minio.bucketName!;
  }

  private async ensureBucketExists(): Promise<void> {
    const exists = await this.client.bucketExists(this.bucketName);
    if (!exists) {
      await this.client.makeBucket(this.bucketName);
    }
  }

  // Method to upload a file to MinIO
  public async uploadFile(file: Express.Multer.File): Promise<{
    objectName: string;
    bucketName: string;
    size: number;
    contentType: string;
    etag: string;
    lastModified: Date;
    url: string;
  }> {
    await this.ensureBucketExists();

    const objectName = `${Date.now()}-${file.originalname}`;
    const metaData = {
      'Content-Type': file.mimetype,
    };

    await this.client.putObject(
      this.bucketName,
      objectName,
      file.buffer,
      file.size,
      metaData
    );

    const stat = await this.client.statObject(this.bucketName, objectName);
    const url = await this.client.presignedGetObject(
      this.bucketName,
      objectName,
      24 * 60 * 60
    ); // 24 hours

    return {
      objectName,
      bucketName: this.bucketName,
      size: stat.size,
      contentType:
        stat.metaData['content-type'] || stat.metaData['Content-Type'],
      etag: stat.etag,
      lastModified: stat.lastModified,
      url,
    };
  }

  //method to gerearate presigned document url
  public async generatePresignedUrl(objectName: string): Promise<string> {
    return await this.client.presignedGetObject(
      this.bucketName,
      objectName,
      1 * 24 * 60 * 60
    ); // 1 day
  }
}

export const minioService = new MinioService();
