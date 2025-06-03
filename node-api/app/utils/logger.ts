class ServerLogs {
  private formatMessage(
    level: 'INFO' | 'WARN' | 'ERROR',
    message: string,
    stack?: string
  ): string {
    const timestamp = this.convertToNairobiTime(new Date());
    let log = `[${timestamp}] [${level}] [${JSON.stringify(message)}]`;
    if (stack) {
      log += ` [Stack Trace: ${JSON.stringify(stack)}]`;
    }
    return log;
  }

  private convertToNairobiTime(date: Date | string | number): string {
    const inputDate = date instanceof Date ? date : new Date(date);

    // Format options for Nairobi time (EAT - East Africa Time, UTC+3)
    const options: Intl.DateTimeFormatOptions = {
      timeZone: 'Africa/Nairobi',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    };

    // Format the date
    return new Intl.DateTimeFormat('en-KE', options).format(inputDate);
  }

  public info(message: string): void {
    console.log(this.formatMessage('INFO', message));
  }

  public warn(message: string): void {
    console.warn(this.formatMessage('WARN', message));
  }

  public error(message: string, error: unknown): void {
    if (error instanceof Error) {
      console.error(this.formatMessage('ERROR', message, error.stack));
    } else {
      const fallback =
        typeof error === 'string' ? error : JSON.stringify(error);
      console.error(
        this.formatMessage(
          'ERROR',
          `${message} - Non-Error thrown: ${fallback}`
        )
      );
    }
  }
}

class LoggingService {
  private serverLogs = new ServerLogs();

  /**
   * Gets the filename of the caller
   * @param depth Stack depth to look for the caller (default: 3)
   * @returns The filename of the caller
   */
  private getCallerFile(depth: number = 3): string {
    const stackLines = new Error().stack?.split('\n') || [];

    if (stackLines.length >= depth) {
      const callerLine = stackLines[depth];
      // Extract filename from the stack trace
      const match = callerLine.match(
        /(?:at\s+.+\s+\()?([^:]+):[0-9]+:[0-9]+\)?$/
      );
      if (match && match[1]) {
        // Get just the filename without the path
        const fullPath = match[1];
        return fullPath.substring(fullPath.lastIndexOf('/') + 1);
      }
    }

    return 'unknown';
  }

  public info(message: string, callerFile?: string): void {
    const caller = callerFile || this.getCallerFile();
    this.serverLogs.info(`[${caller} file], ${message}`);
  }

  public warn(message: string, callerFile?: string): void {
    const caller = callerFile || this.getCallerFile();
    this.serverLogs.warn(`[${caller} file], ${message}`);
  }

  public error(message: string, error: unknown, callerFile?: string): void {
    const caller = callerFile || this.getCallerFile();
    this.serverLogs.error(`[${caller} file], ${message}`, error);
  }
}

// Export the instance of the class
export const log = new LoggingService();
