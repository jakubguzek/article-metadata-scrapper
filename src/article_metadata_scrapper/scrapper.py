import os.path
from abc import ABC, abstractmethod
from json import load
from re import search, findall
from typing import NoReturn
from lxml import html
from requests import get, models
from . import utils, exceptions


class Scrapper(ABC):
    """ Interface for other scrappers

    Attributes:
        - dois: list[str] - list of article doi identifiers as strings
        - pmids: list[str] - list of article pmid identifiers as strings
        - url: str - string representing url address of an article page
        - json_data - dictionary containing article's dois and/or pmids loaded from json file
    Methods:
        - get_article_data(self, doi: str)
    Abstract methods:
        - get_authors(self, root)
        - get_primary_metadata(root, doi=None, pmid=None)
        - get_secondary_metadata(self, root):
        - generate_csl_json_entry(self, authors, primary_metadata, secondary_metadata):
        - extract_data(self, identifier_list):
        - get_data(self):
    """

    def __init__(self, json_data=None) -> NoReturn:
        self.dois: list[str] = []
        self.pmids: list[str] = []
        self.url: str = ""
        path = os.path.abspath(json_data)
        with open(path, "r") as json_file:
            self.json_data: dict = load(json_file)
        for data in self.json_data.values():
            try:
                self.dois.append(data["doi"].strip())
            except AttributeError:
                self.pmids.append(data["pmid"])

    def get_article_page(self, doi: str) -> models.Response:
        """Set appropriate article url and return a requests.models.Response object from this url."""
        headers = {'User-Agent': utils.get_random_agent()}
        article_url: str = f'{self.url}"{doi}"'
        page = get(article_url, headers=headers)
        return page

    @abstractmethod
    def get_authors(self, root):
        """Get names of authors of an article from html.HtmlElement and return them as list."""
        pass

    @abstractmethod
    def get_primary_metadata(self, root, doi=None, pmid=None):
        """Get article title, journal and doi or pmid and return them as a tuple."""
        pass

    @abstractmethod
    def get_secondary_metadata(self, root):
        """Get other metadata such as publication dates, volume, pages, etc. and return them as a tuple."""
        pass

    @abstractmethod
    def generate_csl_json_entry(self, authors, primary_metadata, secondary_metadata):
        """Generate an entry from extracted data in a form of csl_json format compliant dictionary."""
        pass

    @abstractmethod
    def extract_data(self, identifier_list):
        """Extract data from html.HtmlElement of each article and append it to self.article_metadata in csl_json format.
        """
        pass

    @abstractmethod
    def get_data(self):
        """Get article metadata by doi nad by pmid."""
        pass


class PubMedScrapper(Scrapper):
    """Implementation of Scrapper for getting article metadata from https://pubmed.ncbi.nlm.nih.gov

    Instance methods:
        - is_in_pubmed(self, doi: str, root: xpath) -> int
        - get_authors(self, root) -> list:
        - get_primary_metadata(self, root, doi="", pmid="") -> tuple:
        - get_secondary_metadata(self, root) -> tuple:
        - generate_csl_json_entry(
            self,
            authors: list,
            primary_metadata: tuple[str, str, str, str],
            secondary_metadata: tuple[list, str, list]) -> dict:
        - extract_data(self, identifier_list) -> int:
        - get_data(self):
    """

    def __init__(self, json_data=None) -> NoReturn:
        super().__init__(json_data)
        self.url = f'https://pubmed.ncbi.nlm.nih.gov/?term='
        self.article_metadata: list[dict] = []
        self.articles_not_found: list[str] = []

    def is_in_pubmed(self, doi: str, root) -> int:
        """Check if article is in available in PubMed, otherwise raise an exception"""
        try:
            query_error_message: str = root.xpath(
                "//em[@class='altered-search-explanation query-error-message']/text()")[0]
            if ("term was ignored" in query_error_message) or ("term was not found" in query_error_message):
                self.articles_not_found.append(doi)
                raise exceptions.UrLContentError(f"The following term was not found in PubMed: {doi}")
            else:
                return 0
        # It's stupid but if index is out of range it means that the query-error-message was not found within url.
        # Ergo, root.xpath returns empty list, and IndexError is raised.
        # Effectively it means that we return 0 from the method when there is an error.
        # I don't like it, but I'm going to leave it as is for now
        except IndexError:
            return 0

    def get_authors(self, root) -> list:
        authors: list[dict[str, str]] = []
        try:
            raw_authors: list[str] = root.xpath("//div[@class='authors-list']/span/a/text()")
            raw_authors = raw_authors[0:int(len(raw_authors) / 2)]
        except IndexError:
            raise exceptions.UrLContentError("Failed to extract authors")
        last_name: str = ""
        for author in raw_authors:
            first_name = author.split(" ")[0]
            middle_names: list[str] = findall(" \w ", author)
            given_name: str = first_name
            for name in middle_names:
                given_name += name
            for string in author.split(" "):
                if string not in (first_name or middle_names):
                    last_name: str = string
            authors.append({"family": last_name.strip(), "given": given_name.strip()})
        return authors

    def get_primary_metadata(self, root, doi="", pmid="") -> tuple:
        try:
            title: str = root.xpath("//h1[@class='heading-title']/text()")[0].strip()
            journal: str = root.xpath("//button[@class='journal-actions-trigger trigger']/text()")[0].strip()
            if not pmid:
                pmid = root.xpath("//strong[@class='current-id']/text()")[0].strip()
            elif not doi:
                doi = root.xpath("//span[@class='citation-doi']/text()")
        except IndexError:
            raise exceptions.UrLContentError("Failed to extract primary metadata")
        primary_metadata = (title, journal, pmid, doi)
        return primary_metadata

    def get_secondary_metadata(self, root) -> tuple:
        try:
            raw_secondary_metadata: str = root.xpath("//span[@class='cit']/text()")[0].strip()
        except IndexError:
            raise exceptions.UrLContentError("Failed to extract secondary metadata")
        year: list[list[str]] = [[raw_secondary_metadata.split(" ")[0]]]
        volume: str = search('(\d*?)\(|;(\d*?):', raw_secondary_metadata).group(1)
        try:
            pages: list[int] = \
                [int(search(':(\d*)', raw_secondary_metadata).group(1)),
                 int(search("(\d*)\.", raw_secondary_metadata).group(1))]
            if pages[0] > pages[1]:
                start = str(pages[0])
                stop = str(pages[1])
                stop = f'{start[0:(int(len(start)) - int(len(stop)))]}{stop}'
                pages[0], pages[1] = start, stop
        except (ValueError, AttributeError):
            try:
                pages: str = search(r':(e\d*)', raw_secondary_metadata).group(1)
            except AttributeError:
                pages: str = ''
        secondary_metadata = (year, volume, pages)
        return secondary_metadata

    def generate_csl_json_entry(
            self,
            authors: list,
            primary_metadata: tuple[str, str, str, str],
            secondary_metadata: tuple[list, str, list]) -> dict:
        entry: dict = {}
        entry.setdefault("title", primary_metadata[0])
        entry.setdefault("type", "article")
        entry.setdefault("author", authors)
        entry.setdefault("issued", {"raw": secondary_metadata[0]})
        entry.setdefault("journal", primary_metadata[1])
        entry.setdefault("doi", primary_metadata[3])
        entry.setdefault("pmid", primary_metadata[2])
        entry.setdefault("volume", secondary_metadata[1])
        if isinstance(secondary_metadata[1], list):
            entry.setdefault("pages", f'{secondary_metadata[2][0]}-{secondary_metadata[2][1]}')
        else:
            entry.setdefault("pages", secondary_metadata[2])
        entry.setdefault("id", str(authors[0]['family'].lower()) + str(secondary_metadata[0][0][0]))
        return entry

    def extract_data(self, identifier_list) -> int:
        identifier_index = 1
        for identifier in identifier_list:
            print(f'{identifier_index}/{int(len(identifier_list))}', end="\t")
            print(f'Extracting metadata for: {identifier}')
            root = html.fromstring(self.get_article_page(identifier).text)
            try:
                self.is_in_pubmed(identifier, root)
                primary_metadata = self.get_primary_metadata(root, doi=identifier)
                secondary_metadata = self.get_secondary_metadata(root)
                authors = self.get_authors(root)
            except exceptions.UrLContentError as error:
                print(error)
                identifier_index += 1
                continue
            entry = self.generate_csl_json_entry(authors, primary_metadata, secondary_metadata)
            self.article_metadata.append(entry)
            identifier_index += 1
        return 0

    def get_data(self):
        self.extract_data(self.dois)
        self.extract_data(self.pmids)
