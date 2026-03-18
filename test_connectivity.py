
import requests
import sys

def test(url):
    print(f"Testing: {url}")
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Content-Length: {len(r.text)}")
        print(f"Snippet: {r.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test("https://www.bbc.com/news/articles/cv2g4peljngo")
    test("https://www.nature.com/articles/d41586-025-00449-2")
