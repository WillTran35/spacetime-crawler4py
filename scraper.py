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
# Detect redirects and if the page redirects your crawler, index the redirected content
# Detect and avoid dead URLs that return a 200 status but no data DONE
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

#keep /events/ or /event/ but if has stuff after it we dont scrape
urls_to_avoid = [r'.*\d{4}-\d{2}-\d{2}.*$' , r'.*/events/.+$', r'.*/event/.+$', r'.*\d{4}-\d{2}', r'.*/people.*',
                 r'.*/happening.*', r'.*/page/\d+$']
# filter out events with date after it \d4-\d2-\d2

visited_urls = set()
def scraper(url, resp):
    if isUrlToAvoid(url):
        print(f"avoiding url: {url}")
        return []
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def simHash():
    # tokenize the document
    # generate hash value with b bits , hash value should be unique for each word
    pass

def isUrlToAvoid(url):
    for i in urls_to_avoid:
        if len(re.findall(i, url)) > 0:
            return True
    return False

def trapDection(linkList : list):
    # handle trap detection here: we will go through each link and see if they are relatively similar to each other ?
    #
    # You should write simple automatic trap detection systems based on repeated URL patterns and/or (ideally)
    # webpage content similarity repetition over a certain amount of chained pages (the threshold definition is up to you!)
    #
    # set a crawl depth limit (ex. 5 pages of pagination)
    # filter out session based urls (ignore ?session=xyz)
    # detect redirect loops (stop after 5 redirects)
    # monitor crawl speed (dont go on pages that take too long) this can be taken care of by looking at text content
    # use robots.txt (respect site rules for bots)

    # implement simhash to find similar pages -> gives u a hash value and u see if this is hash value exists already,
    # if it does , dont scrape

    result = []
    for i in linkList:
        for j in urls_to_avoid:
            if re.search(j, i) is None:
                result.append(i)
            else:
                print(f"rejected url found in urls_to_avoid: {i}")
        if i in visited_urls:
            print("rejecting, matched already visited url")
            return []  # don't scrape a url we already scraped

    return result

def extractLink(page : str, url : str) -> set:
    """Helper function to help extract all links from a given url."""
    # '<a href="https://example.com">Example</a> <a href="https://test.com">Test</a>'
    tree = html.fromstring(page)
    links: list[str] = tree.xpath("//a/@href")
    # we should make sure all the links are trimmed here and transform all relative to absolute urls
    links = [trimFragment(link) for link in links]  # trims the fragment part out of all urls
    links = [urljoin(url, link) if is_relative(link) else link for link in links]

    links = trapDection(links)
    visited_urls.add(url)
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
    if 400 <= resp.status < 500:
        print("Error. 400 status")
        return []  # dont scrape at 400 error
    if 300 <= resp.status < 400:  # redirection
        print("in 300")
        return [resp.raw_response.get("Location")]
    if not (200 <= resp.status < 300):
        # only handle success
        print("resp status not in 200 - 299")
        return []
    elif getNumTokens(resp) < 50 or checkRatio(resp) < 0.1:  # Crawls all pages with high textual information content
        print(f"number tokens: {getNumTokens(resp)} or ratio: {checkRatio(resp)}")
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


def tokenizeline(line: str) -> list:
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


def getNumTokens(response) -> int:
    # Crawl all pages with high textual information content
    # crawl if text to html ratio is at least 0.1 and over 50 tokens

    # check text to html ratio
    if response.raw_response is not None:
        soup = BeautifulSoup(response.raw_response.content, "html.parser")
        text = soup.get_text(separator=" ").strip()

        result = set(tokenizeline(text))
        # print(f"THis is the num of tokens: {len(result)}")
        return len(result)

    return 0


def checkRatio(response) -> float:
    """Checks the text to html ratio. Only crawl pages with high textual information (ratio > 0.1)."""
    if response.raw_response is None or not response.raw_response.content:
        return 0
    else:
        print("its not none")
        html_content = html.fromstring(response.raw_response.content)
        # soup = BeautifulSoup(response.raw_response.content, "html.parser")
        # text = soup.get_text(separator=" ").strip()
        text_len = len(html_content.text_content())
        html_length = len(html.tostring(html_content))
        result = text_len / html_length if html_length > 0 else 0
        # print(f"This is the text: html : {result} textlen {text_len} html {html_length}")
        return text_len / html_length if html_length > 0 else 0


