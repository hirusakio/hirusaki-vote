import requests, json
base="https://l4xp33cq4l.execute-api.ap-northeast-1.amazonaws.com/prd/"
s=requests.Session(); s.headers.update({"User-Agent":"Mozilla/5.0"})
tj=s.get(base+"timeline",params={"lastEvaluatedKey":"","limit":30},timeout=60).json()
out={"timeline":[],"themes":[]}
for item in tj.get("Items",[]):
    out["timeline"].append({k:item.get(k) for k in item.keys() if k in ["ThemeId","ThemeSentence","ThemeStatus","OpenDate","AnswerDeadline","ScoringDeadline","IsImageTheme","AnswerCount","ScoredCount","Score1","Score2","Score3","ScoringQuota","ScoringBonus"]})
for item in tj.get("Items",[])[:8]:
    tid=item.get("ThemeId")
    if not tid: continue
    r=s.get(base+"theme/before-login",params={"themeId":tid},timeout=60)
    if not r.ok:
        out["themes"].append({"id":tid,"status":r.status_code}); continue
    j=r.json()
    th=j.get("theme",{})
    ans=j.get("answers") or []
    out["themes"].append({
      "id":tid,
      "theme":th,
      "answer_count":len(ans),
      "answer_keys": list(ans[0].keys()) if ans else [],
      "sample_answers":ans[:3]
    })
open("b1_api_summary.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=2))
