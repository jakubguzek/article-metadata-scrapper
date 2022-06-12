#! /usr/bin/env python3

from scrapper import PubMedScrapper


def main() -> int:
    file_path = input("Enter path to json file: ")
    scrapper = PubMedScrapper(json_data=file_path)
    print(scrapper.dois)
    scrapper.get_data()
    return 0


if __name__ == "__main__":
    main()
