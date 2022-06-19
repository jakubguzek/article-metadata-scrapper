import json
import os.path
import random
from typing import Any, Callable, Union

from lxml import html
import requests

from article_metadata_scrapper import exceptions

GetMetadataFunction = Callable[[html.HtmlElement, str],
                               Union[tuple[str, ...], str]]

# noinspection PyPep8
USER_AGENT_LIST = [
    # Firefox
    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0'
]


def get_random_agent() -> str:
    return random.choice(USER_AGENT_LIST)


def load_json_data(json_file: str) -> dict[str, Any]:
    path: str = os.path.realpath(os.path.expanduser(json_file))
    with open(path, "r") as f:
        json_data: dict = json.load(f)
    return json_data


def de_duplicate_list(iterable: list, preserve_order=True) -> list:
    if preserve_order:
        return list(dict.fromkeys(iterable))
    else:
        return list(set(iterable))


def get_raw_metadata(root: html.HtmlElement, xpath: str) -> list[str]:
    metadata = root.xpath(f"{xpath}/text()")
    if metadata:
        return metadata
    else:
        raise exceptions.HtmlContentError(xpath)


def get_article_page(identifier: str, url: str) -> html.HtmlElement:
    header = {"User-Agent": get_random_agent()}
    article_url: str = f"{url}{identifier}"
    return html.fromstring(requests.get(article_url, headers=header).text)


def get_identifiers(dict_data: dict,
                    identifier: str = "doi") -> tuple[str, ...]:
    return tuple(
        str(data[identifier]).strip()
        for data in dict_data.values()
        if data[identifier] is not None)


def strip_and_extract(raw_metadata: dict,
                      key: str) -> Union[tuple[str, ...], str]:
    de_duplicated_list = de_duplicate_list(raw_metadata[key])
    if len(de_duplicated_list) == 1:
        return str(de_duplicated_list[0].strip(" \n"))
    else:
        for item in de_duplicated_list:
            item = item.strip(" \n")
        return tuple(de_duplicated_list)
