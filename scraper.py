import re
from urllib.parse import urlparse
from lxml import html

# Make sure to defragment the URLs, i.e. remove the fragment part.
# look into lxml and beautifulsoup

# Crawl all pages with high textual information content
# Detect and avoid infinite traps
# Detect and avoid sets of similar pages with no information
# Detect redirects and if the page redirects your crawler, index the redirected content
# Detect and avoid dead URLs that return a 200 status but no data
# Detect and avoid crawling very large files, especially if they have low information value

# Please remember to transform relative to absolute URLs

# Before launching your crawler, ensure that you send the server a request with an ASCII URL, but neither the
# entire HTML content of the webpage that you are crawling nor garbage/Unicode strings.

# You should write simple automatic trap detection systems based on repeated URL patterns and/or (ideally)
# webpage content similarity repetition over a certain amount of chained pages (the threshold definition is up to you!)

urls =  ["[\w-]*.ics.uci.edu/\w*",
        "\w*.cs.uci.edu/\w*",
        "\w*.informatics.uci.edu/\w*",
        "\w*.stat.uci.edu/\w*"]
def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extractLink(page : str):
    # '<a href="https://example.com">Example</a> <a href="https://test.com">Test</a>'
    # pattern = r'href="(.*?)"' #lazy method only goes up to the end of the link

    tree = html.fromstring(page)
    return tree.xpath("//a/@href")

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
    # convert to a string using resp.raw_response.content.decode("utf-8");

    if resp.status != 200:
        return []
    html = resp.raw_response.content.decode("utf-8")
    return extractLink(html)

def check(link):
    for i in urls:
        if len(re.findall(i, link)) > 0:
            return True
    return False

def is_valid(url):
    # Decide whether to crawl this url or not.
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)

        if parsed.scheme not in set(["http", "https"]): #checks the protocol; absolute urls must have http/https
            return False
        elif not check(url): #checks the domain
            return False

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

    except TypeError:
        print ("TypeError for ", parsed)
        raise
