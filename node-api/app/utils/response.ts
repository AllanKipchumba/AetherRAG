import { Response } from 'express';
import { log } from './logger';

interface SuccessResponseBody {
  status: 'success';
  message: string;
  data?: any;
}

interface ErrorResponseBody {
  status: 'error';
  message: string;
}

class ClientResponse {
  /**
   * Sends a successful response to the client
   * @param res Express response object
   * @param data Optional data to be sent
   * @param message Success message (defaults to 'Success')
   * @param statusCode HTTP status code (defaults to 200)
   * @returns Express response
   */
  success(
    res: Response,
    data?: any,
    message = 'Success',
    statusCode = 200
  ): Response {
    const responseBody: SuccessResponseBody = {
      status: 'success',
      message,
      ...(data !== undefined && { data }),
    };

    this.logResponse(statusCode, responseBody);
    return res.status(statusCode).json(responseBody);
  }

  /**
   * Sends an error response to the client
   * @param res Express response object
   * @param message Error message (defaults to 'Error')
   * @param statusCode HTTP status code (defaults to 500)
   * @returns Express response
   */
  error(res: Response, message: any = 'Error', statusCode = 500): Response {
    const responseBody: ErrorResponseBody = {
      status: 'error',
      message,
    };

    this.logResponse(statusCode, responseBody);
    return res.status(statusCode).json(responseBody);
  }

  /**
   * Logs the response for tracking and debugging
   * @param statusCode HTTP status code
   * @param responseBody Response body to log
   */
  private logResponse(
    statusCode: number,
    responseBody: SuccessResponseBody | ErrorResponseBody
  ): void {
    log.info(
      `[StatusCode: ${statusCode}], Payload: ${JSON.stringify(responseBody)}`
    );
  }
}

export const clientResponse = new ClientResponse();
