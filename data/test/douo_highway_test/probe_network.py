import urllib.request
import json
import ssl
import sys

# SSL context
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_fetch():
    # Wikipedia API for 道央自動車道
    url = "https://ja.wikipedia.org/w/api.php?action=parse&page=%E9%81%93%E5%A4%AE%E8%87%AA%E5%8B%95%E8%BB%8A%E9%81%93&prop=wikitext&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'AntigravityResearchBot/1.0'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print("Successfully fetched Wikipedia wikitext! Length:", len(data.get('parse', {}).get('wikitext', {}).get('*', '')))
    except Exception as e:
        print("Wikipedia fetch failed:", e)

if __name__ == '__main__':
    test_fetch()
