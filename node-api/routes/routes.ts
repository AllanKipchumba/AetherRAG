import express, { Request, Response } from 'express';
import HealthCheckController from '../app/controllers/health_check';
import fileRoutes from './file_routes';
import { handleUserPrompt } from '../app/controllers/prompt/prompt';

const router = express.Router();

//healthcheck api
router.get('/', (req: Request, res: Response) => {
  HealthCheckController(req, res);
});

router.post('/prompt', (req: Request, res: Response) => {
  handleUserPrompt(req, res);
});

router.use('/file', fileRoutes);

export default router;
