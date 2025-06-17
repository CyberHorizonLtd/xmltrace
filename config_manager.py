import yaml
import os

class ConfigManager:
    """
    Manages loading configuration from a YAML file.
    """
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = {}
        self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        try:
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML configuration file: {e}")

    def get_config(self):
        return self.config

    def get(self, key, default=None):
        """
        Get a configuration value by key, with an optional default.
        Supports dot notation for nested keys (e.g., "endpoints.base_url").
        """
        keys = key.split('.')
        val = self.config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

# Example Usage (for testing the module)
if __name__ == "__main__":
    # Create a dummy config file for testing
    dummy_config_content = """
    general:
      log_level: INFO
      output_dir: ./reports
    endpoints:
      base_url: http://localhost:8000
      timeout: 10
      headers:
        Content-Type: application/xml
    tests:
      - name: GetProductInfo
        path: /products/{product_id}
        method: GET
        expected_status: 200
        validation_xpath: //product/name
      - name: SubmitOrder
        path: /orders
        method: POST
        body: <order><item>A</item></order>
        expected_status: 201
    """
    with open("dummy_config.yaml", "w") as f:
        f.write(dummy_config_content)

    try:
        config_manager = ConfigManager("dummy_config.yaml")
        config = config_manager.get_config()
        print("Loaded Config:")
        print(config)

        print(f"\nBase URL: {config_manager.get('endpoints.base_url')}")
        print(f"Log Level: {config_manager.get('general.log_level')}")
        print(f"Non-existent key (default None): {config_manager.get('non_existent.key')}")
        print(f"Non-existent key (default 'default_value'): {config_manager.get('non_existent.key', 'default_value')}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        os.remove("dummy_config.yaml") # Clean up dummy file
