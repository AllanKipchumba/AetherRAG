import { Request, Response, NextFunction } from 'express';
import { validationResult } from 'express-validator';
import { log } from '../utils/logger';

export async function validateUserInput(
  req: Request,
  res: Response,
  next: NextFunction
) {
  const errors = validationResult(req);

  if (!errors.isEmpty()) {
    log.info(`Validation errors: ${JSON.stringify(errors.array())}`);

    res.status(422).json({
      status: 'error',
      message: 'Validation Errors',
      errors: errors.array(),
    });
    return;
  }

  next();
}
