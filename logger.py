import logging
import os
from datetime import datetime

class Logger:
    """
    A centralized logging utility with support for different log levels and file output.
    """
    def __init__(self, name="xml_tester", log_level="INFO", output_dir=".", log_to_file=True, enable_tracing=True):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self._get_log_level(log_level))
        self.enable_tracing = enable_tracing

        # Prevent adding multiple handlers if already configured
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            if log_to_file:
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                log_file = os.path.join(output_dir, f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)

    def _get_log_level(self, level_str):
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return level_map.get(level_str.upper(), logging.INFO)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)

    def trace(self, event_type, details=None):
        """
        Records a trace event if tracing is enabled.
        """
        if self.enable_tracing:
            trace_message = f"TRACE: Type={event_type}"
            if details:
                trace_message += f", Details={details}"
            self.logger.debug(trace_message) # Traces typically go to DEBUG or a separate trace level
            
# Example Usage (for testing the module)
if __name__ == "__main__":
    # Create a dummy output directory
    output_dir_test = "test_logs"
    if not os.path.exists(output_dir_test):
        os.makedirs(output_dir_test)

    logger_instance = Logger(name="my_tester", log_level="DEBUG", output_dir=output_dir_test, log_to_file=True, enable_tracing=True)

    logger_instance.debug("This is a debug message.")
    logger_instance.info("This is an info message.")
    logger_instance.warning("This is a warning message.")
    logger_instance.error("This is an error message.")
    logger_instance.critical("This is a critical message.")

    logger_instance.trace("REQUEST_SENT", {"url": "http://example.com/api", "method": "GET"})
    logger_instance.trace("RESPONSE_RECEIVED", {"status": 200, "latency": 150})
    logger_instance.trace("VALIDATION_FAILED", {"test_name": "ProductInfo", "reason": "MissingPriceTag"})

    print(f"\nLog files should be in: {output_dir_test}")

    # Clean up dummy directory (optional)
    # import shutil
    # shutil.rmtree(output_dir_test)
