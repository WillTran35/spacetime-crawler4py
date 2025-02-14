from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time
from scraper import visited_urls

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
                print(visited_urls.size())
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
                with open("urls.txt", "a") as x:
                    x.write("New Scraped2: " + tbd_url + "\n")
                    print(f"done, length of scraped url: {len(scraped_urls)}")
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
