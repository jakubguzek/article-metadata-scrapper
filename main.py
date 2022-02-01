import os.path
import utils
from abc import ABC, abstractmethod
from json import load
from re import search, findall
from time import sleep
from typing import Union
from lxml import html
from requests import get


class Scrapper(ABC):

    def __init__(self, jsonData=None):
        self.dois: list[str] = []
        self.pmids: list[str] = []
        self.url: str = ""
        path = os.path.abspath(jsonData)
        jsonFile = open(path, 'r')
        self.jsonData: dict = load(jsonFile)
        jsonFile.close()
        for data in self.jsonData.values():
            try:
                self.dois.append(data["doi"].strip())
            except AttributeError:
                self.pmids.append(data["pmid"])

    def __get_article_page__(self, doi: str):
        headers = {'User-Agent': utils.get_random_agent()}
        self.articleUrl: str = f'{self.url}"{doi}"'
        page = get(self.articleUrl, headers=headers)
        return page

    @abstractmethod
    def __get_authors__(self, root):
        pass

    @abstractmethod
    def __get_primary_metadata__(self, root, doi=None, pmid=None):
        pass

    @abstractmethod
    def __get_secondary_metadata__(self, root):
        pass

    @abstractmethod
    def __generate_csl_json_entry__(self, authors, primaryMetadata, secondaryMetadata):
        pass

    @abstractmethod
    def __extract_data__(self, identifierList):
        pass

    @abstractmethod
    def get_data(self):
        pass


class PubMedScrapper(Scrapper):

    def __init__(self, jsonData=None):
        super().__init__(jsonData)
        self.url = f'https://pubmed.ncbi.nlm.nih.gov/?term='
        self.articleMetadata: list[dict] = []
        self.articlesNotFound: list[str] = []

    def __is_in_pubmed__(self, doi, root):
        try:
            queryErrorMessage: str = root.xpath("//em[@class='altered-search-explanation query-error-message']/text()")[0]
            if ("term was ignored" in queryErrorMessage) or ("term was not found" in queryErrorMessage):
                print(f"The following term was not found in PubMed: {doi}")
                self.articlesNotFound.append(doi)
                return False
            else:
                return True
        except IndexError:
            return True

    def __get_authors__(self, root) -> Union[list[dict[str, str]], int]:
        authorList: list[dict[str, str]] = []
        try:
            rawAuthorsList: list[str] = root.xpath("//div[@class='authors-list']/span/a/text()")
            rawAuthorsList = rawAuthorsList[0:int(len(rawAuthorsList) / 2)]
        except IndexError:
            print("Failed to extract authors")
            return 1
        lastName: str = ""
        for author in rawAuthorsList:
            firstName = author.split(" ")[0]
            middleNames: list[str] = findall(" \w ", author)
            givenName: str = firstName
            for name in middleNames:
                givenName += name
            for string in author.split(" "):
                if string not in (firstName or middleNames):
                    lastName: str = string
            authorList.append({"family": lastName.strip(), "given": givenName.strip()})
        return authorList

    def __get_primary_metadata__(self, root, doi=None, pmid=None) -> Union[tuple[str, str, str, str], int]:
        try:
            title: str = root.xpath("//h1[@class='heading-title']/text()")[0].strip()
            journal: str = root.xpath("//button[@class='journal-actions-trigger trigger']/text()")[0].strip()
            if pmid is None:
                pmid = root.xpath("//strong[@class='current-id']/text()")[0].strip()
            if doi is None:
                doi = root.xpath("//span[@class='citation-doi']/text()")
        except IndexError:
            print("Failed to extract primary metadata")
            return 1
        primaryMetadata = (title, journal, pmid, doi)
        return primaryMetadata

    def __get_secondary_metadata__(self, root) -> Union[tuple[list[list[str]], str, Union[list[int], str]], int]:
        try:
            rawSecondaryMetadata: str = root.xpath("//span[@class='cit']/text()")[0].strip()
        except IndexError:
            print("Failed to extract secondary metadata")
            return 1
        year: list[list[str]] = [[rawSecondaryMetadata.split(" ")[0]]]
        volume: str = search('([0-9]*?)\(|;([0-9]*?):', rawSecondaryMetadata).group(1)
        try:
            pages: list[int] = \
                [int(search(':([0-9]*)', rawSecondaryMetadata).group(1)),
                 int(search("([0-9]*)\.", rawSecondaryMetadata).group(1))]
            if pages[0] > pages[1]:
                start = str(pages[0])
                stop = str(pages[1])
                stop = f'{start[0:(int(len(start)) - int(len(stop)))]}{stop}'
                pages[0], pages[1] = start, stop
        except ValueError:
            pages: str = search(':(e[0-9]*)', rawSecondaryMetadata).group(1)
        except AttributeError:
            pages: str = ''
        secondaryMetadata = (year, volume, pages)
        return secondaryMetadata

    def __generate_csl_json_entry__(self, authors: list, primaryMetadata: tuple[str, str, str, str], secondaryMetadata: tuple[list, str, list]) -> dict:
        entry: dict = {}
        entry.setdefault("title", primaryMetadata[0])
        entry.setdefault("type", "article")
        entry.setdefault("author", authors)
        entry.setdefault("issued", {"raw": secondaryMetadata[0]})
        entry.setdefault("journal", primaryMetadata[1])
        entry.setdefault("doi", primaryMetadata[3])
        entry.setdefault("pmid", primaryMetadata[2])
        entry.setdefault("volume", secondaryMetadata[1])
        if type(secondaryMetadata[2]) is list:
            entry.setdefault("pages", f'{secondaryMetadata[2][0]}-{secondaryMetadata[2][1]}')
        else:
            entry.setdefault("pages", secondaryMetadata[2])
        entry.setdefault("id", str(authors[0]['family'].lower()) + str(secondaryMetadata[0][0][0]))
        return entry

    def __extract_data__(self, identifierList):
        identifieIndex = 1
        for identifier in identifierList:
            print(f'{identifieIndex}/{int(len(identifierList))}', end="\t")
            print(f'Extracting metadata for: {identifier}')
            root = html.fromstring(self.__get_article_page__(identifier).text)
            if not self.__is_in_pubmed__(identifier, root):
                identifieIndex += 1
                continue
            primaryMetadata = self.__get_primary_metadata__(root, doi=identifier)
            secondaryMetadata = self.__get_secondary_metadata__(root)
            authors = self.__get_authors__(root)
            if primaryMetadata == 1 or secondaryMetadata == 1 or authors == 1:
                continue
            entry = self.__generate_csl_json_entry__(authors, primaryMetadata, secondaryMetadata)
            self.articleMetadata.append(entry)
            sleep(1)
            identifieIndex += 1

    def get_data(self):
        self.__extract_data__(self.dois)
        self.__extract_data__(self.pmids)


scrapper = PubMedScrapper(jsonData='/Users/jakubguzek/Documents/articles/doi_index.json')
print(scrapper.dois)
scrapper.get_data()
