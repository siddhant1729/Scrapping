
import requests
from utils.helpers import get_request_headers
from scraper.blog_scraper import _extract_with_newspaper, _extract_with_readability
from scraper.pubmed_scraper import _fetch_pubmed_xml, _parse_xml
import logging

logging.basicConfig(level=logging.INFO)

def diag_blog(url):
    print(f"\n--- Testing Blog: {url} ---")
    try:
        resp = requests.get(url, headers=get_request_headers(), timeout=15)
        print(f"Status: {resp.status_code}")
        print(f"Content length: {len(resp.text)}")
        
        print("\nTesting Newspaper3k...")
        try:
            data = _extract_with_newspaper(url)
            print(f"Title: {data.get('title')}")
            print(f"Text snippet: {data.get('text')[:200]}...")
        except Exception as e:
            print(f"Newspaper3k failed: {e}")

        print("\nTesting Readability...")
        try:
            data = _extract_with_readability(url)
            print(f"Title: {data.get('title')}")
            print(f"Text snippet: {data.get('text')[:200]}...")
        except Exception as e:
            print(f"Readability failed: {e}")
    except Exception as e:
        print(f"Request failed: {e}")

def diag_pubmed(pmid):
    print(f"\n--- Testing PubMed: {pmid} ---")
    try:
        xml = _fetch_pubmed_xml(pmid)
        print(f"XML length: {len(xml)}")
        meta = _parse_xml(xml)
        print(f"Title: {meta.get('title')}")
        print(f"Abstract snippet: {meta.get('abstract')[:200]}...")
    except Exception as e:
        print(f"PubMed test failed: {e}")

if __name__ == "__main__":
    diag_blog("https://www.bbc.com/news/articles/cv2g4peljngo")
    diag_pubmed("39848003")
