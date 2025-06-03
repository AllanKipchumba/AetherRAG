import { Request, Response } from 'express';
import { minioService } from '../../services/minio_service';
import { clientResponse } from '../../utils/response';
import { log } from '../../utils/logger';

export const uploadFile = async (req: Request, res: Response) => {
  try {
    const file = req.file;

    const result = await minioService.uploadFile(file!);

    return clientResponse.success(res, result, 'File uploaded successfully');
  } catch (error: any) {
    log.error('File upload error:', error);
    return clientResponse.error(res, `File upload failed: ${error.message}`);
  }
};
