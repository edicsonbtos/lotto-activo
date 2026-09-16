import sys
from scrapling import Fetcher

url = "https://www.loteriadehoy.com/animalito/lottoactivo/"
page = Fetcher.get(url, stealthy_headers=True)
print("status:", page.status)
print("attrs:", [a for a in dir(page) if not a.startswith("_")])
b = page.body
print("body type:", type(b), "len:", len(b))
t = page.text
print("text len:", len(t) if t else 0)
print(repr(t[:200]) if t else "VACIO")
