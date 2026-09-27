import requests
url="https://oogiri-tmd.net/home/page.php?id=63"
r=requests.get(url,timeout=30)
r.raise_for_status()
open("debug63.html","w",encoding="utf-8").write(r.text)
print(r.status_code, len(r.text))
