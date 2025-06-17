from http_client import HTTPClient
from xml_parser import XMLParser
from logger import Logger
from stats_collector import StatsCollector
import re # For variable substitution

class TestRunner:
    """
    Orchestrates the execution of API tests based on configurations.
    """
    def __init__(self, config, logger: Logger, stats_collector: StatsCollector):
        self.config = config
        self.logger = logger
        self.stats_collector = stats_collector
        
        base_url = self.config.get('endpoints.base_url')
        timeout = self.config.get('endpoints.timeout', 10)
        default_headers = self.config.get('endpoints.headers', {})
        
        if not base_url:
            self.logger.critical("Base URL not defined in configuration. Cannot proceed with tests.")
            raise ValueError("Base URL is required in configuration.")
            
        self.http_client = HTTPClient(base_url, timeout, default_headers)
        self.tests_config = self.config.get('tests', [])

    def _substitute_variables(self, text, variables):
        """
        Substitutes placeholders like {variable_name} in a string with actual values.
        """
        if not isinstance(text, str):
            return text
        
        def replace_match(match):
            key = match.group(1)
            return str(variables.get(key, match.group(0))) # Return original if key not found
        
        return re.sub(r'\{(\w+)\}', replace_match, text)

    def run_tests(self, test_names_to_run=None, override_params=None):
        """
        Runs the configured tests.
        :param test_names_to_run: A list of specific test names to run. If None, runs all.
        :param override_params: A dictionary of parameters to override in test configs (e.g., product_id).
        """
        self.logger.info("Starting XML endpoint tests...")
        
        if not self.tests_config:
            self.logger.warning("No tests defined in configuration.")
            return

        for test_case in self.tests_config:
            test_name = test_case.get('name', 'Unnamed Test')
            
            if test_names_to_run and test_name not in test_names_to_run:
                self.logger.info(f"Skipping test '{test_name}' as it's not in the specified run list.")
                self.stats_collector.record_test_result(test_name, "SKIP", error_message="Test not in run list.")
                continue

            self.logger.info(f"Running test: '{test_name}'")
            self.logger.trace("TEST_START", {"test_name": test_name})

            method = test_case.get('method', 'GET').upper()
            path = test_case.get('path')
            expected_status = test_case.get('expected_status')
            body = test_case.get('body')
            headers = test_case.get('headers', {})
            validation_xpath = test_case.get('validation_xpath')
            validation_regex = test_case.get('validation_regex')
            
            if not path:
                self.logger.error(f"Test '{test_name}' is missing 'path'. Skipping.")
                self.stats_collector.record_test_result(test_name, "ERROR", error_message="Missing 'path' in configuration.")
                continue

            # Apply overrides to path, body, and headers
            current_params = test_case.get('params', {})
            if override_params:
                current_params.update(override_params)

            path = self._substitute_variables(path, current_params)
            body = self._substitute_variables(body, current_params)
            
            # Substitute variables in headers
            substituted_headers = {k: self._substitute_variables(v, current_params) for k, v in headers.items()}
            
            self.logger.debug(f"Requesting: {method} {self.http_client.base_url}{path}")
            self.logger.debug(f"Request Body: {body}")
            self.logger.debug(f"Request Headers: {substituted_headers}")
            
            response = self.http_client.send_request(method, path, headers=substituted_headers, data=body, params=current_params)
            
            self.logger.trace("REQUEST_COMPLETE", {
                "test_name": test_name,
                "url": f"{self.http_client.base_url}{path}",
                "method": method,
                "status_code": response['status_code'],
                "response_time_ms": response['response_time_ms'],
                "success": response['success'],
                "error": response.get('error')
            })

            test_status = "FAIL"
            error_message = None
            details = {
                "status_code": response['status_code'],
                "response_time_ms": response['response_time_ms'],
                "response_success": response['success'],
                "validation_results": {}
            }

            if not response['success']:
                error_message = f"HTTP Request failed: {response.get('error', 'Unknown Error')}"
                self.logger.error(f"Test '{test_name}' failed HTTP request: {error_message}")
            elif expected_status and response['status_code'] != expected_status:
                error_message = f"Expected status {expected_status}, got {response['status_code']}"
                self.logger.error(f"Test '{test_name}' failed status check: {error_message}")
            else:
                parser = XMLParser(response['content'])
                xml_validation_pass = True
                
                if not parser.soup and response['content']: # XML content might be present but unparseable
                    xml_validation_pass = False
                    error_message = "Could not parse XML response."
                    details['validation_results']['xml_parseable'] = False
                    self.logger.error(f"Test '{test_name}': Could not parse XML response.")
                else:
                    details['validation_results']['xml_parseable'] = True

                    if validation_xpath:
                        xpath_result = parser.validate_xpath_like(validation_xpath)
                        details['validation_results']['xpath_validation'] = xpath_result
                        if not xpath_result:
                            xml_validation_pass = False
                            error_message = (error_message + "; " if error_message else "") + f"XPath validation failed for '{validation_xpath}'"
                            self.logger.error(f"Test '{test_name}': XPath validation failed for '{validation_xpath}'")
                        else:
                            self.logger.info(f"Test '{test_name}': XPath validation passed for '{validation_xpath}'")

                    if validation_regex:
                        regex_result = parser.validate_content_regex(validation_regex)
                        details['validation_results']['regex_validation'] = regex_result
                        if not regex_result:
                            xml_validation_pass = False
                            error_message = (error_message + "; " if error_message else "") + f"Regex validation failed for '{validation_regex}'"
                            self.logger.error(f"Test '{test_name}': Regex validation failed for '{validation_regex}'")
                        else:
                            self.logger.info(f"Test '{test_name}': Regex validation passed for '{validation_regex}'")

                if xml_validation_pass and response['success'] and \
                   (not expected_status or response['status_code'] == expected_status):
                    test_status = "PASS"
                else:
                    test_status = "FAIL"

            self.stats_collector.record_test_result(
                test_name, test_status, response['response_time_ms'], details, error_message
            )
            self.logger.trace("TEST_END", {"test_name": test_name, "status": test_status})
            self.logger.info(f"Test '{test_name}' finished with status: {test_status} ({response['response_time_ms']:.2f} ms)")
            if test_status == "FAIL":
                self.logger.info(f"Response Content:\n{response['content']}")
                self.logger.info(f"Error Message: {error_message}")


        self.logger.info("All tests completed.")
        self.stats_collector.print_summary()
        self.stats_collector.generate_report()

# Example Usage (for testing the module)
if __name__ == "__main__":
    # Create dummy config and initialize dependencies
    from config_manager import ConfigManager
    import os
    import shutil

    # Ensure clean slate for testing
    if os.path.exists("test_reports_runner"):
        shutil.rmtree("test_reports_runner")
    if os.path.exists("test_logs_runner"):
        shutil.rmtree("test_logs_runner")

    dummy_config_content = """
    general:
      log_level: DEBUG
      output_dir: ./test_reports_runner
      enable_tracing: true
    endpoints:
      base_url: http://httpbin.org # A public service for testing HTTP requests
      timeout: 5
      headers:
        User-Agent: XMLTester/1.0
        Accept: application/xml
    tests:
      - name: GetXMLData
        path: /xml
        method: GET
        expected_status: 200
        validation_xpath: slides/slide[id='slide-title']
        validation_regex: <title>Slide 1</title>
      - name: PostXMLData
        path: /post
        method: POST
        body: <data><value>test_value</value><param>{dynamic_param}</param></data>
        expected_status: 200
        validation_xpath: form/data/value
        validation_regex: <value>test_value</value>
      - name: NonExistentEndpoint
        path: /nonexistent
        method: GET
        expected_status: 404
      - name: InvalidXMLResponse
        path: /html # This endpoint returns HTML, not XML, to test XML parsing failure
        method: GET
        expected_status: 200
        validation_xpath: /html/body
    """
    with open("runner_config.yaml", "w") as f:
        f.write(dummy_config_content)

    try:
        config_manager = ConfigManager("runner_config.yaml")
        config = config_manager.get_config()

        logger_instance = Logger(
            name="runner_tester", 
            log_level=config_manager.get('general.log_level'), 
            output_dir=config_manager.get('general.output_dir'),
            enable_tracing=config_manager.get('general.enable_tracing', True)
        )
        stats_collector_instance = StatsCollector(
            output_dir=config_manager.get('general.output_dir')
        )

        runner = TestRunner(config_manager, logger_instance, stats_collector_instance)

        print("\n--- Running all tests ---")
        runner.run_tests()

        print("\n--- Running specific tests with parameter override ---")
        # Ensure clean slate for the second run's stats if you want separate reports
        # For simplicity, this will add to the existing stats collector here.
        # In a real scenario, you might create a new StatsCollector for each parameterized run.
        
        # Reset stats for a clearer demonstration of parameterized run
        stats_collector_parameterized = StatsCollector(
            output_dir=config_manager.get('general.output_dir'),
            report_filename="my_test_report_parameterized.json"
        )
        runner_parameterized = TestRunner(config_manager, logger_instance, stats_collector_parameterized)

        runner_parameterized.run_tests(
            test_names_to_run=["PostXMLData", "GetXMLData"],
            override_params={"dynamic_param": "custom_value_123"}
        )

    except Exception as e:
        print(f"An error occurred during TestRunner execution: {e}")
    finally:
        # Clean up dummy config and report directories
        if os.path.exists("runner_config.yaml"):
            os.remove("runner_config.yaml")
        if os.path.exists("test_reports_runner"):
            shutil.rmtree("test_reports_runner")
        if os.path.exists("test_logs_runner"):
            shutil.rmtree("test_logs_runner")
