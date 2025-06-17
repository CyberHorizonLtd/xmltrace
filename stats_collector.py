import os
import json
from datetime import datetime

class StatsCollector:
    """
    Collects and manages statistics for test runs.
    """
    def __init__(self, output_dir=".", report_filename="test_report.json"):
        self.stats = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "test_results": [] # Detailed results for each test
        }
        self.output_dir = output_dir
        self.report_filename = report_filename
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def record_test_result(self, test_name, status, response_time_ms=None, details=None, error_message=None):
        """
        Records the result of a single test.
        :param test_name: Name of the test.
        :param status: "PASS", "FAIL", "SKIP", "ERROR"
        :param response_time_ms: Response time in milliseconds (optional).
        :param details: Dictionary of additional details (e.g., status code, validation results).
        :param error_message: Error message if the test failed or encountered an error.
        """
        self.stats["total_tests"] += 1
        result = {
            "test_name": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "response_time_ms": response_time_ms,
            "details": details if details is not None else {},
            "error_message": error_message
        }
        
        if status == "PASS":
            self.stats["passed_tests"] += 1
        elif status == "FAIL":
            self.stats["failed_tests"] += 1
        elif status == "SKIP":
            self.stats["skipped_tests"] += 1
        elif status == "ERROR": # For errors during test execution itself (e.g., config error)
            self.stats["failed_tests"] += 1 # Count as a failure for overall pass/fail rate

        self.stats["test_results"].append(result)

    def get_summary(self):
        """
        Returns a summary of the test statistics.
        """
        summary = {
            "Total Tests Run": self.stats["total_tests"],
            "Passed": self.stats["passed_tests"],
            "Failed": self.stats["failed_tests"],
            "Skipped": self.stats["skipped_tests"],
            "Pass Rate": f"{(self.stats['passed_tests'] / self.stats['total_tests'] * 100):.2f}%" if self.stats["total_tests"] > 0 else "N/A"
        }
        return summary

    def generate_report(self):
        """
        Generates a JSON report of all test statistics and detailed results.
        """
        report_path = os.path.join(self.output_dir, self.report_filename)
        try:
            with open(report_path, 'w') as f:
                json.dump(self.stats, f, indent=4)
            print(f"Test report generated successfully: {report_path}")
        except IOError as e:
            print(f"Error writing report to file: {e}")

    def print_summary(self):
        """
        Prints the test summary to the console.
        """
        summary = self.get_summary()
        print("\n--- Test Summary ---")
        for key, value in summary.items():
            print(f"{key}: {value}")
        print("--------------------")

# Example Usage (for testing the module)
if __name__ == "__main__":
    output_dir_stats = "test_reports"
    stats_collector = StatsCollector(output_dir=output_dir_stats, report_filename="my_test_report.json")

    stats_collector.record_test_result("TestProductAPI", "PASS", 120, {"status_code": 200, "validation": "ok"})
    stats_collector.record_test_result("TestOrderSubmission", "FAIL", 300, {"status_code": 400, "validation": "failed"}, "Missing required field")
    stats_collector.record_test_result("TestUserLogin", "PASS", 80, {"status_code": 200})
    stats_collector.record_test_result("TestInvalidEndpoint", "ERROR", error_message="Connection refused")
    stats_collector.record_test_result("TestSkippedFeature", "SKIP")

    stats_collector.print_summary()
    stats_collector.generate_report()

    print(f"\nReport files should be in: {output_dir_stats}")

    # Clean up dummy directory (optional)
    # import shutil
    # shutil.rmtree(output_dir_stats)
