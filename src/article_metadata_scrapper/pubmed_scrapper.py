from lxml import html

from article_metadata_scrapper import data_formatter, exceptions, scrapper, utils
from article_metadata_scrapper import pubmed_config


class PubMedScrapper(scrapper.Scrapper):

    def __init__(self, config: scrapper.ScrapperConfig):
        super().__init__(config)
        print("initializing PubMedScrapper object")
        # self.pmids = utils.get_identifiers(self.config.article_identifiers, identifier="pmid")

    def get_metadata(self, identifiers: list = None) -> None:
        if identifiers is None:
            identifiers = self.dois
        index = 1
        for identifier in identifiers:
            print(f'{index}/{int(len(identifiers))}', end="\t")
            print(f'Extracting metadata for: {identifier}')
            root: html.HtmlElement = utils.get_article_page(
                identifier, self.config.url)
            try:
                raw = {
                    k: self.config.getter_function(root, v)
                    for k, v in self.config.xpaths.items()
                    if v is not None
                }
            except exceptions.HtmlContentError as e:
                print(e)
                index += 1
            else:
                self.raw_metadata.append(raw)
                index += 1

    def format_metadata(self) -> None:
        formatter = data_formatter.MetadataFormatter(
            **pubmed_config.PUBMED_FORMATTER)
        for raw_metadata in self.raw_metadata:
            self.metadata.append({
                "authors": formatter.authors(raw_metadata),
                "title": formatter.title(raw_metadata),
                "journal": formatter.journal(raw_metadata),
                "doi": formatter.doi(raw_metadata),
                "year": formatter.year(raw_metadata),
                "volume": formatter.volume(raw_metadata),
                "pages": formatter.pages(raw_metadata)
            })


def main():
    config = scrapper.ScrapperConfig(
        xpaths=pubmed_config.PUBMED_XPATHS,
        article_identifiers=utils.load_json_data("test.json"),
        url="https://pubmed.ncbi.nlm.nih.gov/?term=")
    scr = PubMedScrapper(config)
    scr.get_metadata()
    scr.format_metadata()
    for i in scr.metadata:
        print(i)


if __name__ == "__main__":
    main()
