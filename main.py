import argparse
from config_manager import ConfigManager
from logger import Logger
from stats_collector import StatsCollector
from test_runner import TestRunner
import os

def main():
    parser = argparse.ArgumentParser(description="XML Web Endpoint Tester")
    parser.add_argument(
        "-c", "--config", 
        default="endpoints.yaml", 
        help="Path to the YAML configuration file (default: endpoints.yaml)"
    )
    parser.add_argument(
        "-t", "--tests", 
        nargs='*', 
        help="Space-separated list of specific test names to run (e.g., -t GetProductInfo SubmitOrder). If not specified, all tests run."
    )
    parser.add_argument(
        "-p", "--params", 
        nargs='*', 
        help="Key-value pairs for test parameters to override (e.g., -p product_id=123 order_id=A456). These will substitute {key} in paths/bodies."
    )
    parser.add_argument(
        "-l", "--log_level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
        help="Set the logging level (overrides config file)."
    )
    parser.add_argument(
        "-o", "--output_dir", 
        help="Specify the output directory for logs and reports (overrides config file)."
    )
    parser.add_argument(
        "--no_trace", 
        action="store_true", 
        help="Disable detailed tracing messages."
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config_manager = ConfigManager(args.config)
        config_data = config_manager.get_config()
    except (FileNotFoundError, ValueError) as e:
        print(f"Error loading configuration: {e}")
        return

    # Apply command-line overrides to config
    log_level = args.log_level if args.log_level else config_manager.get('general.log_level', 'INFO')
    output_dir = args.output_dir if args.output_dir else config_manager.get('general.output_dir', './reports')
    enable_tracing = not args.no_trace if args.no_trace else config_manager.get('general.enable_tracing', True)

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Initialize Logger and StatsCollector
    logger = Logger(
        name="xml_tester", 
        log_level=log_level, 
        output_dir=output_dir, 
        log_to_file=True, # Always log to file for comprehensive record
        enable_tracing=enable_tracing
    )
    stats_collector = StatsCollector(output_dir=output_dir)

    logger.info(f"Using configuration file: {args.config}")
    logger.info(f"Log Level: {log_level}")
    logger.info(f"Output Directory: {output_dir}")
    logger.info(f"Tracing Enabled: {enable_tracing}")

    # Parse command-line parameters
    override_params = {}
    if args.params:
        for param in args.params:
            if '=' in param:
                key, value = param.split('=', 1)
                override_params[key] = value
            else:
                logger.warning(f"Invalid parameter format: '{param}'. Expected key=value.")

    # Initialize and run tests
    try:
        runner = TestRunner(config_manager, logger, stats_collector)
        runner.run_tests(test_names_to_run=args.tests, override_params=override_params)
    except ValueError as e:
        logger.critical(f"Test runner initialization failed: {e}")
    except Exception as e:
        logger.critical(f"An unexpected error occurred during test execution: {e}", exc_info=True)
    finally:
        logger.info("Script execution finished.")

if __name__ == "__main__":
    main()
