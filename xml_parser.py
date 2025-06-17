from bs4 import BeautifulSoup
import re # For simple regex-based content validation

class XMLParser:
    """
    Parses XML content using BeautifulSoup and provides methods for data extraction and validation.
    """
    def __init__(self, xml_content):
        self.soup = None
        if xml_content:
            try:
                self.soup = BeautifulSoup(xml_content, 'xml')
            except Exception as e:
                print(f"Error parsing XML content: {e}")
                self.soup = None

    def find_all(self, tag_name, attributes=None):
        """
        Finds all occurrences of a tag with optional attributes.
        """
        if self.soup:
            return self.soup.find_all(tag_name, attrs=attributes)
        return []

    def find(self, tag_name, attributes=None):
        """
        Finds the first occurrence of a tag with optional attributes.
        """
        if self.soup:
            return self.soup.find(tag_name, attrs=attributes)
        return None

    def get_text(self, tag_name, attributes=None, default=""):
        """
        Gets the text content of the first occurrence of a tag.
        """
        tag = self.find(tag_name, attributes)
        if tag:
            return tag.get_text(strip=True)
        return default
    
    def validate_xpath_like(self, xpath_like_expression):
        """
        Performs a basic "XPath-like" validation using BeautifulSoup's CSS selectors or simple tag navigation.
        This is not a full XPath engine but can simulate common checks.
        
        Examples of xpath_like_expression:
        - "product > name": Checks if a 'name' tag exists directly under a 'product' tag.
        - "item[id='123']": Checks for an 'item' tag with id="123".
        - "price": Checks if any 'price' tag exists.
        - "response //status": Checks if a 'status' tag exists anywhere within a 'response' tag.
        
        Returns True if the element is found, False otherwise.
        """
        if not self.soup:
            return False

        # Simple cases: direct tag, tag with attribute
        if '[' in xpath_like_expression and ']' in xpath_like_expression:
            try:
                tag_name, attr_part = xpath_like_expression.split('[', 1)
                attr_name, attr_value = attr_part[:-1].split('=', 1)
                attr_value = attr_value.strip("'\"") # Remove quotes
                found_elements = self.soup.find_all(tag_name, {attr_name: attr_value})
                return len(found_elements) > 0
            except ValueError:
                pass # Not a simple attribute expression, try CSS selector

        # Basic CSS selector support
        try:
            # BeautifulSoup's select method uses CSS selectors.
            # Convert simple XPath-like to CSS selector where possible.
            # //tag -> tag (any descendant)
            # parent/child -> parent > child
            css_selector = xpath_like_expression.replace('//', ' ').replace('/', ' > ')
            return len(self.soup.select(css_selector)) > 0
        except Exception:
            pass # Fallback to simpler tag check if CSS selector fails

        # Fallback: Just check for the existence of a tag
        return self.find(xpath_like_expression.split('/')[-1].split('[')[0].strip()) is not None

    def validate_content_regex(self, regex_pattern):
        """
        Validates the entire XML content against a regular expression.
        """
        if not self.soup or not self.soup.prettify():
            return False
        return bool(re.search(regex_pattern, self.soup.prettify(), re.DOTALL))

# Example Usage (for testing the module)
if __name__ == "__main__":
    xml_data = """
    <root>
        <product id="123">
            <name>Example Product</name>
            <price currency="USD">19.99</price>
            <details>
                This is a detailed description.
                <info>More info here.</info>
            </details>
        </product>
        <order id="A1">
            <item id="i1">Laptop</item>
            <item id="i2">Mouse</item>
        </order>
        <status>active</status>
    </root>
    """

    parser = XMLParser(xml_data)

    print("--- Basic Finds ---")
    product_name = parser.get_text("name")
    print(f"Product Name: {product_name}")

    price_tag = parser.find("price")
    if price_tag:
        print(f"Price: {price_tag.get_text()} (Currency: {price_tag.get('currency')})")

    all_items = parser.find_all("item")
    print("All Items:")
    for item in all_items:
        print(f"- {item.get_text()} (ID: {item.get('id')})")

    print("\n--- XPath-like Validation ---")
    print(f"Has product tag: {parser.validate_xpath_like('product')}")
    print(f"Has product > name: {parser.validate_xpath_like('product > name')}")
    print(f"Has product price with currency='USD': {parser.validate_xpath_like('price[currency=\'USD\']')}")
    print(f"Has item with id='i1': {parser.validate_xpath_like('item[id=\'i1\']')}")
    print(f"Has status tag: {parser.validate_xpath_like('status')}")
    print(f"Has non-existent tag: {parser.validate_xpath_like('nonexistent')}")
    print(f"Has root //info: {parser.validate_xpath_like('root //info')}")


    print("\n--- Regex Content Validation ---")
    print(f"Contains 'Example Product': {parser.validate_content_regex(r'Example Product')}")
    print(f"Contains 'Laptop' and 'Mouse': {parser.validate_content_regex(r'Laptop.*Mouse')}")
    print(f"Contains 'xyz': {parser.validate_content_regex(r'xyz')}")
