from abc import ABC, abstractmethod
import dataclasses
from typing import Optional

from article_metadata_scrapper import utils


@dataclasses.dataclass
class ScrapperConfig:
    xpaths: dict
    article_identifiers: dict
    url: str
    getter_function: utils.GetMetadataFunction = utils.get_raw_metadata


class Scrapper(ABC):

    def __init__(self, config: ScrapperConfig):
        self.config = config
        self.raw_metadata: list[Optional[dict]] = []
        self.metadata: list[Optional[dict]] = []
        self.dois = utils.get_identifiers(self.config.article_identifiers)

    @abstractmethod
    def get_metadata(self, identifiers: list = None) -> None:
        raise NotImplemented

    @abstractmethod
    def format_metadata(self) -> None:
        raise NotImplemented
