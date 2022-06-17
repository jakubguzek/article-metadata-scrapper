from abc import ABC, abstractmethod
import dataclasses
import enum
import functools
from typing import Callable, Optional, Union

from lxml import html
import requests

from article_metadata_scrapper import utils, exceptions

PUBMED_XPATHS = {
    "AUTHORS": "//div[@class='authors-list']/span/a",
    "TITLE": "//h1[@class='heading-title']",
    "JOURNAL": "//button[@class='journal-actions-trigger trigger']",
    "DOI": "//span[@class='citation-doi']",
    "OTHER": "//span[@class='cit']",
    "YEAR": None,
    "VOLUME": None,
    "PAGES": None,
    "PMID": "//strong[@class='current-id']"
}

_GetMetadataFunction = Callable[[html.HtmlElement], Union[str, tuple[str, ...]]]


def _get_authors(root: html.HtmlElement, xpath: str) -> tuple[str, ...]:
    authors: tuple[str, ...] = tuple(utils.de_duplicate_list(
        root.xpath(f"{xpath}/text()")))
    return authors


def _get_metadata(
        root: html.HtmlElement, xpath: str) -> Union[str, tuple[str, ...]]:
    metadata: Union[list, str] = root.xpath(f"{xpath}/text()")
    try:
        return metadata[0].strip()
    except IndexError:
        raise exceptions.HtmlContentError(
            xpath, "Failed to extract metadata from")
    finally:
        return tuple(metadata)


def _get_article_page(identifier: str, url: str) -> html.HtmlElement:
    header = {"User-Agent": utils.get_random_agent()}
    article_url: str = f"{url}{identifier}"
    return html.fromstring(requests.get(article_url, headers=header).text)


def _get_dois(dict_data: dict) -> tuple[str, ...]:
    return tuple(data["doi"].strip() for data in dict_data.values()
                 if data["doi"] is not None)


@dataclasses.dataclass
class UrlPaths:

    AUTHORS: str
    TITLE: str
    JOURNAL: str
    DOI: str
    OTHER: str
    YEAR: Optional[str] = None
    VOLUME: Optional[str] = None
    PAGES: Optional[str] = None
    PMID: Optional[str] = None


@dataclasses.dataclass
class ArticleMetadata:

    authors: _GetMetadataFunction
    title: _GetMetadataFunction
    journal: _GetMetadataFunction
    doi: _GetMetadataFunction
    other = _GetMetadataFunction
    year: _GetMetadataFunction = None
    volume: _GetMetadataFunction = None
    pages: _GetMetadataFunction = None
    pmid: Optional[_GetMetadataFunction] = None


@dataclasses.dataclass
class Scrapper(ABC):

    xpaths: UrlPaths
    identifiers: dict
    url: str

    def __post_init__(self):
        self.dois = _get_dois(self.identifiers)
        self.metadata: list[ArticleMetadata] = []
        self.authors_partial = functools.partial(
            _get_authors, xpath=self.xpaths.AUTHORS)
        self.title_partial = functools.partial(
            _get_metadata, xpath=self.xpaths.TITLE)
        self.journal_partial = functools.partial(
            _get_metadata, xpath=self.xpaths.JOURNAL)
        self.doi_partial = functools.partial(
            _get_metadata, xpath=self.xpaths.DOI)
        self.other_partial = functools.partial(
            _get_metadata, xpath=self.xpaths.OTHER)

    @abstractmethod
    def get_metadata(self) -> None:
        raise NotImplemented


class PubMedScrapper(Scrapper):

    def __post__init__(self):
        super().__post_init__()
        self.pmids = tuple(data["pmid"].strip()
                           for data in self.identifiers.values()
                           if data["pmid"] is not None)

    def get_metadata(self) -> None:
        identifier_index = 1
        for doi in self.dois:
            print(f'{identifier_index}/{int(len(self.dois))}', end="\t")
            print(f'Extracting metadata for: {doi}')
            root: html.HtmlElement = _get_article_page(doi, self.url)
            self.metadata.append(ArticleMetadata(
                self.authors_partial(root),
                self.title_partial(root),
                self.journal_partial(root),
                self.doi_partial(root),
                self.other_partial(root)
            ))
            identifier_index += 1
        for pmid in self.dois:
            print(f'{identifier_index}/{int(len(self.pmids))}', end="\t")
            print(f'Extracting metadata for: {pmid}')
            root: html.HtmlElement = _get_article_page(pmid, self.url)
            self.metadata.append(ArticleMetadata(
                self.authors_partial(root),
                self.title_partial(root),
                self.journal_partial(root),
                self.doi_partial(root),
                self.other_partial(root)
            ))
            identifier_index += 1



def main():
    pubmed_paths = UrlPaths(**PUBMED_XPATHS)
    scrapper = PubMedScrapper(
        xpaths=pubmed_paths,
        identifiers=utils.load_json_data("./test.json"),
        url="https://pubmed.ncbi.nlm.nih.gov/?term="
    )
    print(scrapper.get_metadata())


if __name__ == "__main__":
    main()
