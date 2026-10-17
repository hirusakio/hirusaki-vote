import requests, json, datetime

BASE="https://l4xp33cq4l.execute-api.ap-northeast-1.amazonaws.com/prd/"
CDN="https://dan0h5umj3b5n.cloudfront.net/"
USER_ID="27445a98-00d1-70e7-99dc-674b38fa7a19"

s=requests.Session()
s.headers.update({"User-Agent":"Mozilla/5.0"})
timeline=s.get(BASE+"timeline",params={"lastEvaluatedKey":"","limit":30},timeout=60)
timeline.raise_for_status()
items=timeline.json().get("Items",[])
result=next((x for x in items if x.get("ThemeStatus")=="結果表示"),None)
if not result:
    raise RuntimeError("no result theme found")

tid=result["ThemeId"]
r=s.get(BASE+"theme/before-login",params={"themeId":tid},timeout=60)
r.raise_for_status()
j=r.json()
th=j["theme"]
answers=j.get("answers") or []
expected=int(th.get("AnswerCount",0))
if len(answers)!=expected:
    raise RuntimeError(f"answer count mismatch {len(answers)} != {expected}")

out_answers=[]
bad_totals=[]
for pos,a in enumerate(answers,1):
    sl=a.get("ScoreList") or []
    calc=sum(float(x.get("Score",0)) for x in sl)
    total=float(a.get("TotalScore",0))
    if abs(calc-total)>1e-9:
        bad_totals.append({"position":pos,"calc":calc,"total":total,"answerId":a.get("AnswerId")})
    uv=next((x for x in sl if x.get("UserId")==USER_ID),None)
    out_answers.append({
        "id":a.get("AnswerId"),
        "rank":int(a.get("AnswerRank",pos)),
        "position":pos,
        "answer":a.get("AnswerSentence",""),
        "author":a.get("UserName",""),
        "total":int(total) if total.is_integer() else total,
        "vote":int(uv.get("Score",0)) if uv else 0,
        "self":a.get("UserId")==USER_ID
    })

date=(th.get("ScoringDeadline") or "")[:10]
if not date:
    raise RuntimeError("no result date")
theme_data={
    "id":tid,
    "date":date,
    "theme":th.get("ThemeSentence",""),
    "image":CDN+tid+".jpg" if th.get("IsImageTheme") else None,
    "count":expected,
    "voters":int(th.get("ScoreCount",0)),
    "answers":out_answers,
    "source":"https://oogiri-b1.com/theme?themeId="+tid,
    "week":17
}
summary={
    "theme":theme_data,
    "validation":{
        "answerCountMatches":len(answers)==expected,
        "badTotalCount":len(bad_totals),
        "badTotals":bad_totals[:10],
        "voteCount":sum(1 for a in out_answers if a["vote"]),
        "votePoints":sum(a["vote"] for a in out_answers),
        "self":next(({"rank":a["rank"],"position":a["position"],"answer":a["answer"],"total":a["total"]} for a in out_answers if a["self"]),None)
    },
    "updatedAt":datetime.datetime.now(datetime.timezone.utc).isoformat()
}
open("b1_latest_theme.json","w",encoding="utf-8").write(json.dumps(summary,ensure_ascii=False,indent=2))
