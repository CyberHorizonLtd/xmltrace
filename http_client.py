import requests
import time

class HTTPClient:
    """
    Handles making HTTP requests and basic response handling.
    """
    def __init__(self, base_url, timeout=10, default_headers=None):
        self.base_url = base_url
        self.timeout = timeout
        self.default_headers = default_headers if default_headers is not None else {}

    def _build_url(self, path):
        return f"{self.base_url}{path}"

    def send_request(self, method, path, headers=None, data=None, params=None):
        url = self._build_url(path)
        combined_headers = {**self.default_headers, **(headers if headers is not None else {})}
        
        start_time = time.time()
        try:
            response = requests.request(
                method,
                url,
                headers=combined_headers,
                data=data,
                params=params,
                timeout=self.timeout
            )
            response_time = (time.time() - start_time) * 1000 # in ms
            return {
                "status_code": response.status_code,
                "headers": response.headers,
                "content": response.text,
                "response_time_ms": response_time,
                "success": True
            }
        except requests.exceptions.Timeout:
            response_time = (time.time() - start_time) * 1000 # in ms
            return {
                "status_code": None,
                "headers": {},
                "content": "Request Timed Out",
                "response_time_ms": response_time,
                "success": False,
                "error": "Timeout"
            }
        except requests.exceptions.ConnectionError:
            response_time = (time.time() - start_time) * 1000 # in ms
            return {
                "status_code": None,
                "headers": {},
                "content": "Connection Error",
                "response_time_ms": response_time,
                "success": False,
                "error": "ConnectionError"
            }
        except requests.exceptions.RequestException as e:
            response_time = (time.time() - start_time) * 1000 # in ms
            return {
                "status_code": None,
                "headers": {},
                "content": f"An unexpected request error occurred: {e}",
                "response_time_ms": response_time,
                "success": False,
                "error": str(e)
            }

# Example Usage (for testing the module)
if __name__ == "__main__":
    # You'd typically need a running server for this.
    # For a quick test, you can try an existing public API that returns XML if available,
    # or a simple local Flask/Django app.

    # Example with a dummy base_url that will likely fail or timeout if not running a server
    client = HTTPClient(base_url="http://localhost:5000", timeout=5, default_headers={"Accept": "application/xml"})

    print("--- Testing GET request ---")
    response_get = client.send_request("GET", "/test_endpoint")
    print(f"Status Code: {response_get['status_code']}")
    print(f"Content: {response_get['content'][:100]}...")
    print(f"Response Time: {response_get['response_time_ms']:.2f} ms")
    print(f"Success: {response_get['success']}")
    if not response_get['success']:
        print(f"Error: {response_get.get('error')}")

    print("\n--- Testing POST request with XML body ---")
    xml_data = "<data><item>value</item></data>"
    response_post = client.send_request("POST", "/submit_data", headers={"Content-Type": "application/xml"}, data=xml_data)
    print(f"Status Code: {response_post['status_code']}")
    print(f"Content: {response_post['content'][:100]}...")
    print(f"Response Time: {response_post['response_time_ms']:.2f} ms")
    print(f"Success: {response_post['success']}")
    if not response_post['success']:
        print(f"Error: {response_post.get('error')}")

    print("\n--- Testing Timeout ---")
    # This will simulate a timeout if the server doesn't respond quickly
    client_timeout = HTTPClient(base_url="http://192.0.2.1", timeout=1) # Non-routable IP for guaranteed timeout
    response_timeout = client_timeout.send_request("GET", "/slow_endpoint")
    print(f"Status Code: {response_timeout['status_code']}")
    print(f"Content: {response_timeout['content']}")
    print(f"Response Time: {response_timeout['response_time_ms']:.2f} ms")
    print(f"Success: {response_timeout['success']}")
    if not response_timeout['success']:
        print(f"Error: {response_timeout.get('error')}")
