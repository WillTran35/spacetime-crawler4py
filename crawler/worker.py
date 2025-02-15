from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time
from scraper import visited_urls, all_hashes, subdomains, all_pages, all_words

class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            print(len(self.frontier.to_be_downloaded))
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                print(visited_urls, all_hashes , subdomains, all_pages, all_words)
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                # if not (self.frontier.checkRatio() < 0.1 or self.frontier.getNumTokens() < 50):
                self.frontier.add_url(scraped_url)
            if scraped_urls:  # if this url is worth scraping, it is considered a valid scrape
                with open("allurlsNEW.txt", "a") as x:
                    x.write("New Scraped NEW NEW : " + tbd_url + "\n\n")
                    print(f"done, length of scraped url: {len(scraped_urls)}")
                with open("allHashes.txt", "a") as y:
                    y.write("hashin....\n")
                    for i in all_hashes:
                        y.write(f"{i}, {all_hashes[i]}\n")
                    y.write("\nDONE!")
                    y.write("\n\n\n\n")
                with open("all_subdomains.txt", "a") as z:
                    z.write("subdomains....\n")
                    for i in subdomains:
                        z.write(f"{i}, {subdomains[i]}\n")
                    z.write("\nDONE!")
                    z.write("\n\n\n\n")

                with open("all_pages.txt", "a") as z:
                    z.write("ALL PAGES....\n")
                    for i in all_pages:
                        z.write(f"{i}, {all_pages[i]}\n")
                    z.write("\nDONE!")
                    z.write("\n\n\n\n")

                with open("all_words.txt", "a") as z:
                    z.write("ALL WORDS....\n")
                    for i in all_words:
                        z.write(f"{i}, {all_words[i]}\n")
                    z.write("DONE!")
                    z.write("\n\n\n\n")

            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
