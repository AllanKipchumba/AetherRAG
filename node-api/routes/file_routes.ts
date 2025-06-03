import express, { Request, Response } from 'express';
import { upload } from '../app/middleware/multer';
import { uploadFile } from '../app/controllers/file/upload';
import { validateFileUpload } from '../app/validation/file_validation';
import { validateUserInput } from '../app/middleware/validate_user_input';

const router = express.Router();

router.post(
  '/upload',
  upload.single('file'),
  validateFileUpload,
  validateUserInput,
  (req: Request, res: Response) => {
    uploadFile(req, res);
  }
);

export default router;
