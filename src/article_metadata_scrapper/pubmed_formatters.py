import re
from typing import Union

from article_metadata_scrapper import utils


def format_doi(raw_metadata: dict) -> Union[tuple[str, ...], str]:
    return utils.strip_and_extract(raw_metadata, "doi").strip("doi: ")


def format_year(raw_metadata: dict) -> Union[tuple[str, ...], str]:
    return utils.strip_and_extract(raw_metadata, "other").split(" ")[0]


def format_volume(raw_metadata: dict) -> Union[tuple[str, ...], str]:
    other = utils.strip_and_extract(raw_metadata, "other")
    return re.search(r"(\d+?)\(|;(\d+?):", other).group(1)


def format_pages(raw_metadata: dict) -> Union[tuple[str, ...], str]:
    other = utils.strip_and_extract(raw_metadata, "other")
    try:
        pages: list[int] = [
            int(re.search(r':(\d*)', other).group(1)),
            int(re.search(r"(\d*)\.", other).group(1))
        ]
        if pages[0] > pages[1]:
            start = str(pages[0])
            stop = str(pages[1])
            stop = f'{start[0:(int(len(start)) - int(len(stop)))]}{stop}'
            return start, stop
    except (ValueError, AttributeError):
        try:
            return re.search(r':(e\d*)', other).group(1)
        except AttributeError:
            return ''
