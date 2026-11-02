import requests,re,json,urllib.parse
BASE="https://oogiri-mi.com"
URL=BASE+"/hangiri7/match/"
s=requests.Session(); s.headers.update({"User-Agent":"Mozilla/5.0"})
r=s.get(URL,timeout=60); r.raise_for_status()
html=r.text
srcs=re.findall(r'<script[^>]+src=["\']([^"\']+)["\']',html)
scripts=[]
for src in srcs:
    u=urllib.parse.urljoin(URL,src)
    try:
        rr=s.get(u,timeout=60)
        txt=rr.text
    except Exception as e:
        scripts.append({"url":u,"error":str(e)}); continue
    endpoints=sorted(set(re.findall(r'["\']([^"\']*(?:/api/|api/event|hangiri7)[^"\']*)["\']',txt)))
    if endpoints:
        scripts.append({"url":u,"status":rr.status_code,"endpoints":endpoints[:200]})
payloads=sorted(set(re.findall(r'["\']([^"\']*(?:_payload\.json|/api/|hangiri7)[^"\']*)["\']',html)))
open("hangiri7_discovery.json","w",encoding="utf-8").write(json.dumps({
 "status":r.status_code,"final_url":r.url,"html_prefix":html[:5000],
 "script_srcs":srcs,"html_candidates":payloads,"scripts":scripts
},ensure_ascii=False,indent=2))
