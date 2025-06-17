# xmltrace

## Run based on config

python main.py

## Run specific tests

python main.py -t GetBasicXMLData CheckNonExistentEndpoint

## Run tests with overridden parameters

python main.py -t PostXMLWithDynamicParameter -p item_id=2002 quantity=5

## Set different loglevel and output directory

python main.py -l DEBUG -o ./my_test_results

## Disable tracing

python main.py --no_trace

## Combine parameters

python main.py -c custom_config.yaml -t GetBasicXMLData -p product_id=XYZ -l DEBUG


# Explanation and features

• Modular Design: Each component (HTTP client, XML parser, logger, stats, test runner, config) is a separate module, promoting reusability and testability.

### Configuration (endpoints.yaml, config_manager.py):

• Uses YAML for easy-to-read and hierarchical configuration.
• Allows defining base URL, default headers, and individual test cases.
• Each test case can specify:
- name: Unique identifier for the test.
- path: Endpoint path (relative to base_url).
- method: HT TP method (GET, POST, etc.).
- body: Request body for POST/PUT (supports text/xml and application/xml via headers).
- params: Default parameters for the test case, useful for templating the path or body.
   - expected_status: Expected HTTP status code.
   - validation_path: A simplified XPath-like expression for content validation using BeautifulSoup's capabilities (e.g., product/name, item[id='123'l).
   - validation _regex: A regular expression to validate the entire response content.

### Parameterization (main.py --params):

• Command-line arguments (--params key=value) allow overriding specific parameters within the test configurations (e.g., for dynamic data like product_id). These are substituted into the path and body using _substitute_variables.

### Tracing (logger.py, TestRunner):

• The Logger class provides structured logging,
• logger.trace() calls within TestRunner capture key events (request sent, response received, validation results) for detailed debugging and analysis, written to the log file.
• Can be enabled/disabled via configuration or command line (--no_trace).

### Statistics (stats_collector.py):

• Collects and aggregates test results (total, passed, failed, skipped).
• Records response times and detailed outcomes for each test.
• Generates a human-readable summary to the console and a detailed JSON report file for further analysis.

### XML Parsing (xml_parser.py):

• Utilizes BeautifulSoup for robust XML parsing.
• Provides methods like find, find_all, get_text.
• validate_xpath_like offers a convenient way to perform common XML structure/ content checks without a full XPath engine. It supports basic tag navigation and attribute filtering similar to CSS selectors.
• validate_content_regex allows for more generic text-based content validation.

### Error Handling: 
• Includes basic error handling for file operations, network issues (timeouts, connection errors), and XML parsing.
