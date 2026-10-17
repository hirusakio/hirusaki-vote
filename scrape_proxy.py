import requests, re, json, os
s=requests.Session()
s.headers.update({"User-Agent":"Mozilla/5.0"})
u="https://oogiri-b1.com/"
r=s.get(u,timeout=60)
r.raise_for_status()
html=r.text
out={"html":html,"scripts":[]}
for src in re.findall(r'<script[^>]+src=["\']([^"\']+)["\']',html):
    if src.startswith("/"): src=u.rstrip("/")+src
    elif not src.startswith("http"): src=u+src
    rr=s.get(src,timeout=60)
    out["scripts"].append({"url":src,"text":rr.text[:500000]})
open("b1_debug.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False))
