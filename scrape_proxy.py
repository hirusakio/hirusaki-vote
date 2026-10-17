import requests, json
base="https://l4xp33cq4l.execute-api.ap-northeast-1.amazonaws.com/prd/"
s=requests.Session(); s.headers.update({"User-Agent":"Mozilla/5.0"})
timeline=s.get(base+"timeline",params={"lastEvaluatedKey":"","limit":40},timeout=60)
timeline.raise_for_status()
tj=timeline.json()
out={"timeline":tj}
for item in tj.get("Items",[])[:10]:
    tid=item.get("ThemeId")
    if not tid: continue
    r=s.get(base+"theme/before-login",params={"themeId":tid},timeout=60)
    out.setdefault("themes",[]).append({"id":tid,"status":r.status_code,"data":r.json() if r.ok else r.text[:1000]})
open("b1_api_debug.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=2))
