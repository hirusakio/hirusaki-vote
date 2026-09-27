import requests, re, json, time

target='[昼崎](http://oogiri-tmd.net/home/mypage.php?user_id=309)'
out={}
for rid in range(52,82):
    u=f"https://r.jina.ai/http://oogiri-tmd.net/home/page.php?id={rid}"
    t=requests.get(u,timeout=60).text.replace("\r\n","\n")
    m=re.search(r'投稿数：(\d+)',t)
    submissions=int(m.group(1)) if m else None
    pat=re.compile(r'(?m)^(\d+)位\[([^\]]+)\]\(([^\n]+)\)\n\n\1位\[\2\]\([^\n]+\)\n')
    starts=list(pat.finditer(t))
    votes=[]
    answers=[]
    self_answer=None
    for k,mt in enumerate(starts):
        end=starts[k+1].start() if k+1<len(starts) else len(t)
        block=t[mt.end():end]
        lines=[x.strip() for x in block.splitlines()]
        answer=next((x for x in lines if x),"")
        raw_rank=int(mt.group(1))
        author=mt.group(2)
        author_url=mt.group(3)
        display_rank=k+1

        vote_points=None
        voter_line=next((x for x in lines if target in x and any(f"{p}点 [" in x for p in (2,3,4))),None)
        if voter_line:
            pos=voter_line.index(target)
            marks=[(voter_line.rfind(f"{p}点 ",0,pos),p) for p in (2,3,4)]
            marks=[x for x in marks if x[0]>=0]
            if marks:
                vote_points=max(marks)[1]
                votes.append({"rawRank":raw_rank,"displayRank":display_rank,"points":vote_points,"author":author,"answer":answer,"percentile":raw_rank/submissions})

        is_self=('user_id=309' in author_url or author=='昼崎')
        if is_self:
            self_answer={"rawRank":raw_rank,"displayRank":display_rank,"answer":answer}

        answers.append({
            "rawRank":raw_rank,
            "displayRank":display_rank,
            "author":author,
            "answer":answer,
            "votePoints":vote_points,
            "isSelf":is_self
        })

    out[str(rid)]={"submissions":submissions,"parsed":len(starts),"answers":answers,"votes":votes,"self":self_answer,"voteCount":len(votes),"pointTotal":sum(v["points"] for v in votes)}
    time.sleep(.2)
open("audit_scraped_52_81.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=2))
