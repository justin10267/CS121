import re
from urllib.parse import urlparse, urljoin
import urllib.error
import urllib.robotparser
import urllib.request
import nltk
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
from bs4 import BeautifulSoup
from collections import defaultdict

nltk.download('punkt')
nltk.download('stopwords')

checked_urls = set() # set check
checked_netloc_and_paths = set() # set check
fragmented_urls = set() # find unique urls
most_common_words = defaultdict(int) # find most common words 
text = set() # check textual similarity
longest_page = ""
longest_page_length = 0
ics_uci_edu_subdomains = dict()

def scraper(url, resp):
    with open('assignment2.txt', 'w') as f:
        f.write("Unique Pages: {}\n".format(len(fragmented_urls)))
        f.write("Longest Page (based on words): {}\n".format(longest_page))
        sorted_common_words_list = [(word, freq) for word, freq in sorted(most_common_words.items(), key=lambda item: item[1], reverse=True)]
        top_50_common_words = sorted_common_words_list[:50]
        f.write("TOP 50 COMMON WORDS\n")
        for word in top_50_common_words:
            f.write("Word: {}. Freq: {}.\n".format(word[0], word[1]))
        sorted_ics_uci_edu = [(domain, unique_pages) for domain, unique_pages in sorted(ics_uci_edu_subdomains.items(), key=lambda item: item[0])]
        f.write("ICS UCI EDU SUBDOMAINS\n")
        for domain in sorted_ics_uci_edu:
            f.write("{}, {}\n".format(domain[0], domain[1]))
        f.write("\n")
    return extract_next_links(url, resp)

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
    
    global fragmented_urls
    global most_common_words
    global text
    global longest_page
    global longest_page_length
    global ics_uci_edu_subdomains
    
    if resp.status != 200:
        return list()
    if resp.raw_response == None:
        return list()
    
    soup = BeautifulSoup(resp.raw_response.text, 'html.parser')
    
    urls = []
    for link in soup.find_all('a'):
        # relative to absolute
        temp = link.get('href')
        if not bool(urlparse(link.get('href')).netloc):
            temp = urljoin(resp.url, link.get('href'))
            temp = temp.replace(" ", "%20")
        if is_valid(temp):
            html = urllib.request.urlopen(temp).read()
            tempsoup = BeautifulSoup(html, "html.parser")
            raw = tempsoup.get_text()
            # new
            no_punctuation_raw = re.sub(r'\W+', ' ', raw)
            tokenizer = RegexpTokenizer(r'\w+')
            tokens = tokenizer.tokenize(no_punctuation_raw)
            #
            if len(tokens) > 50:
                if raw not in text:
                    fragmented_urls.add(urlparse(temp)._replace(fragment="").geturl())
                    urls.append(temp)
                text.add(raw)
                for token in tokens:
                    if token.lower() not in stopwords.words('english') and not token.isnumeric() and len(token) != 1:
                        most_common_words[token.lower()] += 1
                if len(tokens) > longest_page_length:
                    longest_page = temp
                    longest_page_length = len(tokens)
    
    if (re.search(r"\.ics\.uci\.edu", urlparse(url).netloc)):
        ics_uci_edu_subdomains[url] = len(urls)
    
    print(urls)
    
    return urls

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    global checked_urls
    global checked_netloc_and_paths
    global fragmented_urls
    
    print("Url: {}".format(url))
    
    if url in checked_urls:
        return False
    
    try:
        checked_urls.add(url)
        parsed = urlparse(url)
        
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        if re.match(r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            # custom
            + r"svn|DS_Store|java|ss|scm|rkt|class|svg|sh|txt|py|conf|sql|war|tgz|ppsx|mpg|zip"
            #
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False
        
        # only links placed into the frontier are those with these domains
        if not (re.search("|".join([r"\.ics\.uci\.edu",
                r"\.cs\.uci\.edu",
                r"\.informatics\.uci\.edu",
                r"\.stat\.uci\.edu"]), parsed.netloc) or \
            re.match(r"today\.uci\.edu/department/information_computer_sciences/", parsed.netloc)):
            return False
        
        # to avoid cases like evoke
        # placed here since ran into error with forbes url (bytes with string operation error)
        url_up_to_path = parsed.scheme + "://" + parsed.netloc + parsed.path
        
        if url_up_to_path in checked_netloc_and_paths:
            return False
        checked_netloc_and_paths.add(parsed.scheme + "://" + parsed.netloc + parsed.path)
        
        # cases like stayconnected urls
        split_path = parsed.path.split("/")
        
        #black-list "census-1990" to prevent running into html, txt, ...
        if "census1990-mld" in split_path[-1]:
            return False
        
        # https://grape.ics.uci.edu/wiki/public/zip-attachment/wiki/cs122b-2018-winter-project1-eclipse-project/ example
        if "zip-attachment" in split_path:
            return False
        
        freq_dict = defaultdict(int)
        for item in split_path:
            freq_dict[item] += 1
            
        # check if the most common item that is not " " occurrs more than 5 times
        try:
            most_common_item = max(freq_dict, key=freq_dict.get)
        except ValueError:
            most_common_item = ""
        if (freq_dict[most_common_item] >= 3 and most_common_item != ""):
            return False
        
        # find robot.txt using scheme and netloc/domain and check whether the url should be added to frontier
        robot_url = parsed.scheme + "://" + parsed.netloc + "/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robot_url)
        rp.read()
        if not (rp.can_fetch("*", url)):
            return False
        # archives coverage
        if urllib.request.urlopen(url).getcode() != 200:
            return False
        return True
    
    # https://hombao.ics.uci.edu/hernando.html
    # server not found - url
    except urllib.error.URLError:
        return False
    
    except UnicodeEncodeError:
        return False
        
    except TypeError:
        print ("TypeError for ", parsed)
        raise
