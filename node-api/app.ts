import express from 'express';
import bodyParser from 'body-parser';
import apis from './routes/routes';
import { initializeKafkaListeners } from './app/controllers/prompt/prompt';
import { log } from './app/utils/logger';

const app = express();
const PORT = 5000;

// Initialize Kafka listeners
async function startServer() {
  try {
    // Initialize Kafka listeners first
    await initializeKafkaListeners();

    app.use(bodyParser.json());

    app.use('/', apis);

    // Start the HTTP server
    app.listen(PORT, () => {
      log.info(`Server running on port ${PORT}`);
    });
  } catch (error) {
    log.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();

// Graceful shutdown
process.on('SIGINT', async () => {
  log.info('Shutting down server...');
  // Kafka disconnection is handled in the kafka client
  process.exit(0);
});
