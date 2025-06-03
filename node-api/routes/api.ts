import express, { Request, Response } from 'express';
import HealthCheckController from '../controllers/health_check';
const router = express.Router();

//healthcheck api
router.get('/', (req: Request, res: Response) => {
  HealthCheckController(req, res);
});

export default router;
