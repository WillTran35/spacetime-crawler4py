import re
from urllib.parse import urlparse, urljoin
from lxml import html
from bs4 import BeautifulSoup
import hashlib

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

urls = [r"^https?://(?:\w+\.)?ics\.uci\.edu/?.*",
        r"^https?://(?:\w+\.)?cs\.uci\.edu/?.*",
        r"^https?://(?:\w+\.)?informatics\.uci\.edu/?.*",
        r"^https?://(?:\w+\.)?stat\.uci\.edu/?.*"]

#keep /events/ or /event/ but if has stuff after it we dont scrape
urls_to_avoid = [r'.*\d{4}-\d{2}-\d{2}.*$' , r'.*/events/.+$', r'.*/event/.+$', r'.*\d{4}-\d{2}', r'.*/people.*',
                 r'.*/happening.*']

all_hashes = {}  # key: url, value [hashvalue]

subdomains = {}  # dictionary that holds all subdomains and their respective pages

# longest page in terms of words
all_pages = {}  # pages : word count

# 50 most common words
all_words = {}  # word : count

visited_urls = set()
def scraper(url, resp):
    if isUrlToAvoid(url):
        print(f"avoiding url: {url}")
        return []
    if url in visited_urls:
        print("rejecting, matched already visited url")
        return []  # don't scrape a url we already scraped
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def hash_function(token):
    """Hashes a word and converts to 64 bit representation"""
    return int(hashlib.md5(token.encode()).hexdigest(), 16) & ((1 << 64) - 1)

def simhash(text):
    """Computes the Simhash fingerprint for text"""
    # tokenize the words
    words = tokenizeline(text)

    vector = [0] * 64

    for word in words:
        hash_value = hash_function(word)
        for i in range(64):  # Iterate over each bit in 64-bit hash
            if (hash_value >> i) & 1:  # If bit is 1, increment vector
                vector[i] += 1
            else:
                vector[i] -= 1
    fingerprint = 0
    for i in range (64):
        if vector[i] > 0:
            fingerprint |= (1 << i)

    return fingerprint


def hamming_distance(hash1, hash2):
    """Computes the Hamming distance between two SimHashes."""
    return bin(hash1 ^ hash2).count("1")  # XOR and count 1s


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
            if re.search(j, i) is None and validLink(i):
                result.append(i)
            else:
                print(f"rejected url found in urls_to_avoid: {i}")

    return result

def getAllSubdomains(linksList):
    # only get the subdomains if when parsed is in ics.uci.edu
    for i in linksList:
        netloc = urlparse(i).netloc  # Extract subdomain
        if re.search(r"(?:\w+\.)?ics\.uci\.edu$", netloc):
            subdomains[netloc] = subdomains.get(netloc, 0) + 1


def extractLink(page : str, url : str) -> set:
    """Helper function to help extract all links from a given url."""
    # '<a href="https://example.com">Example</a> <a href="https://test.com">Test</a>'
    soup = BeautifulSoup(page, "html.parser")
    text = soup.get_text(separator=" ").strip()
    if isSimilar(simhash(text)):
        return set()
    if url not in all_hashes:
        all_hashes[url] = simhash(text)

    tree = html.fromstring(page)
    links: list[str] = tree.xpath("//a/@href")
    # we should make sure all the links are trimmed here and transform all relative to absolute urls
    links = [trimFragment(link) for link in links]  # trims the fragment part out of all urls
    links = [urljoin(url, link) if is_relative(link) else link for link in links]

    getAllSubdomains(links)
    visited_urls.add(url)

    links = trapDection(links)
    return set(links)  # no duplicate links to avoid traps


def isSimilar(hash_value):
    for key, value in all_hashes.items():
        # print(f"this is key value {key}: {value}")
        distance = hamming_distance(hash_value, value)
        if distance <= 3:
            print(f"rejecting {key}, already found similar hash, distance is {distance}")
            return True
    print("did not find similar hash, proceeding...")
    return False

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
    if not validLink(url):
        print("not a valid link, not in the 4 required links ")
        return []
    if resp.raw_response is None:
        print("error, raw_response is None")
        return []
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
        print(f"number tokens: {getNumTokens(resp)} or ratio: {checkRatio(resp)} too high")
        return []
    html = resp.raw_response.content
    if len(html) > 2_097_152:
        print(f"length of content too big: {len(html)}")
        return []
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
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|img|apk|war|sql|mpg)$", parsed.path.lower()) #checks the end of the url
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
    computeWordFrequencies(result)

    return result


def computeWordFrequencies(token:list):
    """Write another method/function that counts the number of occurrences of each token in the token list.
    Remember that you should write this assignment yourself from scratch, so you are not allowed to import
    a counter when the assignment asks you to write that method."""

    # This function runs in O(n) time where n is the length of the list. It iterates through the list and adds
    # itself to the dictionary.
    for i in token:
        all_words[i] = all_words.setdefault(i, 0) + 1



def getNumTokens(response) -> int:
    # Crawl all pages with high textual information content
    # crawl if text to html ratio is at least 0.1 and over 50 tokens

    # check text to html ratio
    if response.raw_response is not None:
        soup = BeautifulSoup(response.raw_response.content, "html.parser")
        text = soup.get_text(separator=" ").strip()

        result = set(tokenizeline(text))
        if response.url not in all_pages:
            all_pages[response.url] = len(result)
        # all_pages[response.url] = all_pages.get(response.url, 0) + len(result)
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


