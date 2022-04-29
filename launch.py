from configparser import ConfigParser
from argparse import ArgumentParser

from utils.server_registration import get_cache_server
from utils.config import Config
from crawler import Crawler
from scraper import fragmented_urls, most_common_words, longest_page, ics_uci_edu_subdomains

def main(config_file, restart):
    cparser = ConfigParser()
    cparser.read(config_file)
    config = Config(cparser)
    config.cache_server = get_cache_server(config, restart)
    crawler = Crawler(config, restart)
    crawler.start()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--restart", action="store_true", default=False)
    parser.add_argument("--config_file", type=str, default="config.ini")
    args = parser.parse_args()
    main(args.config_file, args.restart)
    print("Unique Pages: {}".format(len(fragmented_urls)))
    print("Longest Page (based on words): {}".format(longest_page))
    sorted_common_words_list = [(word, freq) for word, freq in sorted(most_common_words.items(), key=lambda item: item[1], reverse=True)]
    top_50_common_words = sorted_common_words_list[:50]
    print("TOP 50 COMMON WORDS")
    for word in top_50_common_words:
        print("Word: {}. Freq: {}.".format(word[0], word[1]))
    sorted_ics_uci_edu = [(domain, unique_pages) for domain, unique_pages in sorted(ics_uci_edu_subdomains.items(), key=lambda item: item[0])]
    print("ICS UCI EDU SUBDOMAINS")
    for domain in sorted_ics_uci_edu:
        print("{}, {}".format(domain[0], domain[1]))
