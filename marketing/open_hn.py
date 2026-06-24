import requests
import webbrowser
import time

def main():
    print("Fetching live Hacker News threads...")
    # Fetch top recent stories about resumes and rejection
    res = requests.get('https://hn.algolia.com/api/v1/search?query=resume%20rejected&tags=story')
    data = res.json()
    
    hits = data.get('hits', [])[:3]
    for hit in hits:
        url = f"https://news.ycombinator.com/item?id={hit['objectID']}"
        print(f"Opening: {url}")
        webbrowser.open(url)
        time.sleep(1) # Small delay so browser handles tabs cleanly

if __name__ == '__main__':
    main()
