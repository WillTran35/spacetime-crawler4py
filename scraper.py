import re
from urllib.parse import urlparse, urljoin
from lxml import html
from bs4 import BeautifulSoup

from utils.download import download

# Make sure to defragment the URLs, i.e. remove the fragment part. DONE
# look into lxml and beautifulsoup

# Crawl all pages with high textual information content DONE
# Detect and avoid infinite traps -> we can make a set of urls instead of a list DONE
# Detect and avoid sets of similar pages with no information
# Detect redirects and if the page redirects your crawler, index the redirected content DONE
# Detect and avoid dead URLs that return a 200 status but no data
# Detect and avoid crawling very large files, especially if they have  low information value DONE (checked ratio)

# Please remember to transform relative to absolute URLs DONE

# Before launching your crawler, ensure that you send the server a request with an ASCII URL, but neither the
# entire HTML content of the webpage that you are crawling nor garbage/Unicode strings. DONE?

# You should write simple automatic trap detection systems based on repeated URL patterns and/or (ideally) DONE
# webpage content similarity repetition over a certain amount of chained pages (the threshold definition is up to you!)

urls = [r"^https?://(?:\w+\.)?ics.uci.edu/?.*",
        r"^https?://(?:\w+\.)?cs.uci.edu/?.*",
        r"^https?://(?:\w+\.)?informatics.uci.edu/?.*",
        r"^https?://(?:\w+\.)?stat.uci.edu/?.*"]

# visited_urls = {}
def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extractLink(page : str, url : str) -> set:
    """Helper function to help extract all links from a given url."""
    # '<a href="https://example.com">Example</a> <a href="https://test.com">Test</a>'
    tree = html.fromstring(page)
    links: list[str] = tree.xpath("//a/@href")
    # we should make sure all the links are trimmed here and transform all relative to absolute urls
    links = [trimFragment(link) for link in links]  # trims the fragment part out of all urls
    links = [urljoin(url, link) if is_relative(link) else link for link in links]
    return set(links)  # no duplicate links to avoid traps

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    # check resp.status, make sure it returns 200 before we crawl
    # go thru resp.raw_response and look for <a> anchor tags

    # 204 is nothing on page
    if not (200 <= resp.status_code < 300):
        return []
    html = resp.raw_response.content
    return extractLink(html, url)

def validLink(link):
    """Checks if the link matches any of the required links to crawl. Returns true if matches, returns false otherwise."""
    # print(f"in valid link: {link}")
    for i in urls:
        if len(re.findall(i, link)) > 0:
            return True
    return False

def is_valid(url):
    # Decide whether to crawl this url or not.
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)  # returns a ParsedObject
        if parsed.scheme not in {"http", "https"}:  # checks the protocol; absolute urls must have http/https
            return False
        elif not validLink(url):  # checks the domain
            return False
        # elif getNumTokens(url) < 50 or checkRatio(url) < 0.1:  # Crawls all pages with high textual information content
        #     return False
        # needs to check if it works outside of site

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()) #checks the end of the url
        # ex. "https://user:pass@example.com:8080/path/to/page?query=value#fragment"
        # ParseResult(scheme='https', netloc='user:pass@example.com:8080', path='/path/to/page',
        #             params='', query='query=value', fragment='fragment')
        # parsed.path only returns /path/to/page this part
    except TypeError:
        print ("TypeError for ", parsed)
        raise

def trimFragment(url : str ):
    """Trims the fragment of a url.
    For example, https://example.com/page.html#section2 will return https://example.com/page.html"""
    return url.split("#", 1)[0]


# Detect and avoid sets of similar pages with no information

def is_relative(url: str):
    """Checks if the url is a relative url. A relative url is a direction to a page without a scheme nor domain."""
    parsed = urlparse(url)
    return parsed.scheme not in {'https', 'http'} or parsed.netloc == ""


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


def getNumTokens(url: str) -> int:
    # Crawl all pages with high textual information content
    # crawl if text to html ratio is at least 0.1 and over 50 tokens

    # check text to html ratio

    response = download(url)
    html_content = response.text

    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator=" ").strip()

    result = set(tokenizeline(text))

    return len(result)


def checkRatio( url: str) -> float:
    """Checks the text to html ratio. Only crawl pages with high textual information (ratio > 0.1)."""
    response = requests.get(url)
    html_content = response.text

    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator=" ").strip()
    text_len = len(text)
    html_length = len(html_content)

    return text_len / html_length if html_length > 0 else 0

