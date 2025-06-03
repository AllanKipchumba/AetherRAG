import { Request, Response } from 'express';
import { clientResponse } from '../utils/response';

export default function HealthCheckController(req: Request, res: Response) {
  return clientResponse.success(res, 'Welcome to Aether Rag API Service');
}
