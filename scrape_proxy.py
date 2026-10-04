import requests
u="https://r.jina.ai/http://oogiri-tmd.net/home/page.php?id=82"
r=requests.get(u,timeout=90,headers={"User-Agent":"Mozilla/5.0"})
r.raise_for_status()
open("raw_82.txt","w",encoding="utf-8").write(r.text)
