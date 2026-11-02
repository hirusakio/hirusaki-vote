import requests,re,json,urllib.parse
URL="https://oogiri-mi.com/hangiri7/match/"
s=requests.Session(); s.headers.update({"User-Agent":"Mozilla/5.0"})
html=s.get(URL,timeout=60).text
uuids=sorted(set(re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',html)))
needles=["event-matches:hangiri7","1回戦","2回戦","3回戦"]+uuids
snips={}
for n in needles:
    arr=[]; pos=0
    while True:
        i=html.find(n,pos)
        if i<0: break
        arr.append(html[max(0,i-800):min(len(html),i+1800)])
        pos=i+len(n)
        if len(arr)>=5: break
    if arr: snips[n]=arr
links=sorted(set(re.findall(r'href=["\']([^"\']+)["\']',html)))
open("hangiri7_discovery.json","w",encoding="utf-8").write(json.dumps({
 "html_len":len(html),"uuids":uuids,"links":[x for x in links if "hangiri7" in x],
 "snippets":snips
},ensure_ascii=False,indent=2))
