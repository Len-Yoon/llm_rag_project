import urllib.parse, json, sys
import http.client

base = "127.0.0.1:8000"
params = {
    "q": "미국 경제",
    "days": "3",
    "pages": "1",
    "headless": "false",
}
qs = urllib.parse.urlencode(params, safe="")

conn = http.client.HTTPConnection(base)
conn.request("GET", f"/debug/crawl?{qs}")
res = conn.getresponse()
print(res.status, res.reason)
print(res.read().decode("utf-8", errors="ignore"))
conn.close()