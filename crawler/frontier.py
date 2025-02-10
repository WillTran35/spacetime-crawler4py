import os
import shelve
import requests
import re
from bs4 import BeautifulSoup
from threading import Thread, RLock
from queue import Queue, Empty

from utils import get_logger, get_urlhash, normalize
from scraper import is_valid

class Frontier(object):
    def __init__(self, config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config
        self.to_be_downloaded = list()
        
        if not os.path.exists(self.config.save_file) and not restart:
            # Save file does not exist, but request to load save.
            self.logger.info(
                f"Did not find save file {self.config.save_file}, "
                f"starting from seed.")
        elif os.path.exists(self.config.save_file) and restart:
            # Save file does exists, but request to start from seed.
            self.logger.info(
                f"Found save file {self.config.save_file}, deleting it.")
            os.remove(self.config.save_file)
        # Load existing save file, or create one if it does not exist.
        self.save = shelve.open(self.config.save_file)
        if restart:
            for url in self.config.seed_urls:
                self.add_url(url)
        else:
            # Set the frontier state with contents of save file.
            self._parse_save_file()
            if not self.save:
                for url in self.config.seed_urls:
                    self.add_url(url)

    def _parse_save_file(self):
        ''' This function can be overridden for alternate saving techniques. '''
        total_count = len(self.save)
        tbd_count = 0
        for url, completed in self.save.values():
            if not completed and is_valid(url):
                self.to_be_downloaded.append(url)
                tbd_count += 1
        self.logger.info(
            f"Found {tbd_count} urls to be downloaded from {total_count} "
            f"total urls discovered.")

    def get_tbd_url(self):
        try:
            return self.to_be_downloaded.pop()
        except IndexError:
            return None

    def add_url(self, url):
        url = normalize(url)
        urlhash = get_urlhash(url)
        if urlhash not in self.save:
            self.save[urlhash] = (url, False)
            self.save.sync()
            self.to_be_downloaded.append(url)
    
    def mark_url_complete(self, url):
        urlhash = get_urlhash(url)
        if urlhash not in self.save:
            # This should not happen.
            self.logger.error(
                f"Completed url {url}, but have not seen it before.")

        self.save[urlhash] = (url, True)
        self.save.sync()

    def tokenizeline(self, line: str) -> list:
        """Helper function to tokenize an individual line."""
        # This function runs in O(n) time complexity, where n is the length of the line.
        # It must iterate through the entire string getting each letter.
        result = []
        string = ""
        line = line.lower()
        pattern = "[a-zA-Z0-9]"
        for i in line:
            if re.search(pattern, i):
                string += i
            else:
                if string != "":
                    result.append(string)
                string = ""
        if string != "":
            result.append(string)
        return result

    def getNumTokens(self, url: str) -> int:
        # Crawl all pages with high textual information content
        # crawl if text to html ratio is at least 0.1 and over 50 tokens

        # check text to html ratio

        response = requests.get(url)
        html_content = response.text

        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator=" ").strip()

        result = set(self.tokenizeline(text))

        return len(result)

    def checkRatio(self,url: str) -> float:
        """Checks the text to html ratio. Only crawl pages with high textual information (ratio > 0.1)."""
        response = requests.get(url)
        html_content = response.text

        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator=" ").strip()
        text_len = len(text)
        html_length = len(html_content)

        return text_len / html_length if html_length > 0 else 0


