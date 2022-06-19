import functools

from article_metadata_scrapper import pubmed_formatters, utils

PUBMED_XPATHS = {
    "authors": "//div[@class='authors-list']/span/a",
    "title": "//h1[@class='heading-title']",
    "journal": "//button[@class='journal-actions-trigger trigger']",
    "doi": "//span[@class='citation-doi']",
    "other": "//span[@class='cit']",
    "year": None,
    "volume": None,
    "pages": None,
    "pmid": "//strong[@class='current-id']"
}

PUBMED_FORMATTER = {
    "authors": functools.partial(utils.strip_and_extract, key="authors"),
    "title": functools.partial(utils.strip_and_extract, key="title"),
    "journal": functools.partial(utils.strip_and_extract, key="journal"),
    "doi": pubmed_formatters.format_doi,
    "year": pubmed_formatters.format_year,
    "volume": pubmed_formatters.format_volume,
    "pages": pubmed_formatters.format_pages
}
