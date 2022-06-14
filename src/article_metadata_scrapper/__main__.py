#! /usr/bin/env python3

from pprint import pformat

from scrapper import PubMedScrapper


def main() -> int:
    file_path = input("Enter path to json file: ")
    scrapper = PubMedScrapper(json_data=file_path)
    print(scrapper.dois)
    scrapper.get_data()
    with open("article_metadata.csl_json", "a") as csl_json:
        csl_json.write(pformat(scrapper.article_metadata))
    return 0


if __name__ == "__main__":
    main()
