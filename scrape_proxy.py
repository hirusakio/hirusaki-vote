import requests
url="https://r.jina.ai/http://oogiri-tmd.net/home/page.php?id=63"
r=requests.get(url,timeout=30)
print(r.status_code, len(r.text))
open("debug63.txt","w",encoding="utf-8").write(r.text)
