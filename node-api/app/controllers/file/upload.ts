import { Request, Response } from 'express';
import { minioService } from '../../services/minio_service';
import { clientResponse } from '../../utils/response';
import { log } from '../../utils/logger';
import { kafkaMessageQueue } from '../../services/kafka_client';
import { Enums } from '../../utils/enums';

export const uploadFile = async (req: Request, res: Response) => {
  try {
    const file = req.file;

    const result = await minioService.uploadFile(file!);

    // Build the message payload
    const fileMetadata = {
      objectName: result.objectName,
      bucketName: result.bucketName,
      size: result.size,
      contentType: result.contentType,
      url: result.url,
      etag: result.etag,
      lastModified: result.lastModified,
    };

    // Create Kafka event message
    const kafkaEvent = kafkaMessageQueue.createMessage(
      Enums.FILE_EMBEDDING_CREATE,
      fileMetadata,
      Enums.PYTHON_AI_SERVICE
    );

    // Publish to Kafka
    await kafkaMessageQueue.publishEvent(
      Enums.TOPIC_EMBEDDING_CREATE,
      kafkaEvent
    );

    log.info('File metadata published to Kafka for embedding');

    return clientResponse.success(res, result, 'File uploaded successfully');
  } catch (error: any) {
    log.error('File upload error:', error);
    return clientResponse.error(res, `File upload failed: ${error.message}`);
  }
};
