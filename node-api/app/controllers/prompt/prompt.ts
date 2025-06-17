// Enhanced handler with response mechanism
import { kafkaMessageQueue } from '../../services/kafka_client';
import { Enums } from '../../utils/enums';
import { clientResponse } from '../../utils/response';
import { log } from './../../utils/logger';
import { Request, Response } from 'express';

// Store for pending requests with timeout
const pendingRequests = new Map<
  string,
  {
    resolve: (value: any) => void;
    reject: (error: any) => void;
    timeout: NodeJS.Timeout;
  }
>();

export async function handleUserPrompt(req: Request, res: Response) {
  try {
    const prompt = req.body.prompt;

    const metadata = {
      user_prompt: prompt,
      document_id: '1750147609544-Allan_Kipchumba_CV.pdf',
      query_type: 'specific_document',
    };

    // Create the Kafka event message
    const kafkaEvent = kafkaMessageQueue.createMessage(
      Enums.USER_PROMPT_CREATE,
      metadata,
      Enums.PYTHON_AI_SERVICE
    );

    // Publish the event
    await kafkaMessageQueue.publishEvent(Enums.TOPIC_USER_PROMPT, kafkaEvent);

    // Wait for response with timeout
    const response = await waitForResponse('test-correlation-123', 30000); // 30 second timeout

    return clientResponse.success(res, response);
  } catch (error: any) {
    log.error('Error handling user prompt:', error);
    return clientResponse.error(
      res,
      `Failed to handle user prompt: ${error.message}`
    );
  }
}

function waitForResponse(
  correlationId: string,
  timeoutMs: number
): Promise<any> {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      pendingRequests.delete(correlationId);
      reject(new Error('Response timeout'));
    }, timeoutMs);

    pendingRequests.set(correlationId, {
      resolve,
      reject,
      timeout,
    });
  });
}

// Message handler for LLM responses
export async function handleLLMResponse(
  topic: string,
  message: any,
  headers: any
): Promise<void> {
  try {
    log.info(`Received LLM response on topic ${topic}: {
      eventType: message.eventType,
      correlationId: message.metadata?.correlationId,
    }`);

    const correlationId = message.metadata?.correlationId;
    if (!correlationId) {
      log.warn('No correlation ID in LLM response');
      return;
    }

    const pendingRequest = pendingRequests.get(correlationId);
    if (pendingRequest) {
      clearTimeout(pendingRequest.timeout);
      pendingRequests.delete(correlationId);

      // Resolve the waiting request with the response
      pendingRequest.resolve({
        prompt: message.payload.prompt,
        response: message.payload.response,
        model: message.payload.model,
        finishReason: message.payload.finish_reason,
      });
    } else {
      log.warn(`No pending request found for correlation ID: ${correlationId}`);
    }
  } catch (error) {
    log.error('Error handling LLM response:', error);
  }
}

// Initialize response listener when the service starts
export async function initializeKafkaListeners() {
  try {
    // Connect to Kafka
    await kafkaMessageQueue.connect();

    // Subscribe to LLM response topic
    await kafkaMessageQueue.subscribe(
      [Enums.TOPIC_LLM_RESPONSE],
      'nodejs-llm-response-consumer',
      handleLLMResponse
    );

    log.info('Kafka listeners initialized successfully');
  } catch (error) {
    log.error('Failed to initialize Kafka listeners:', error);
    throw error;
  }
}
