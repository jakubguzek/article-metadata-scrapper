import dataclasses
from typing import Callable, Union

_FormatterFunction = Callable[[dict], Union[tuple[str, ...], str]]


@dataclasses.dataclass
class MetadataFormatter:
    authors: _FormatterFunction
    title: _FormatterFunction
    journal: _FormatterFunction
    doi: _FormatterFunction
    year: _FormatterFunction = None
    volume: _FormatterFunction = None
    pages: _FormatterFunction = None
    pmid: _FormatterFunction = None
