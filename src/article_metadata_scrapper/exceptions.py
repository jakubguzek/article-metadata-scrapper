class HtmlContentError(Exception):
    """The desired xpath was not found within url page html content"""

    def __init__(self, xpath,
                 message="The desired xpath was not found within html"):
        self.xpath = xpath
        self.message = message
        super().__init__()

    def __str__(self):
        return f"{self.message}: {self.xpath}"
