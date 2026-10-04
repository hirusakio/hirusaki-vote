import requests, re, json, time

target='[昼崎](http://oogiri-tmd.net/home/mypage.php?user_id=309)'
out={}
session=requests.Session()
session.headers.update({"User-Agent":"Mozilla/5.0"})

for rid in range(82,88):
    u=f"https://r.jina.ai/http://oogiri-tmd.net/home/page.php?id={rid}"
    t=""
    for attempt in range(6):
        r=session.get(u,timeout=90)
        if r.ok and "投稿数：" in r.text:
            t=r.text.replace("\r\n","\n")
            break
        time.sleep(3+attempt*2)
    if not t:
        raise RuntimeError(f"failed to fetch round {rid}")

    m=re.search(r'投稿数：(\d+)',t)
    submissions=int(m.group(1))

    topic_m=re.search(r'(?s)\nお題\n(.*?)(?=\n\d+位\[)',t)
    if not topic_m:
        raise RuntimeError(f"round {rid}: prompt not found")
    topic_raw=topic_m.group(1).strip()
    img_m=re.search(r'!\[[^\]]*\]\((https?://oogiri-tmd\.net/home/image/[^)]+)\)',topic_raw)
    image_url=img_m.group(1) if img_m else None
    prompt="画像で一言" if image_url else re.sub(r'\s+',' ',topic_raw).strip()

    pat=re.compile(r'(?m)^(\d+)位\[([^\]]+)\]\(([^\n]+)\)\n\n\1位\[\2\]\([^\n]+\)\n')
    starts=list(pat.finditer(t))
    if len(starts)!=submissions:
        raise RuntimeError(f"round {rid}: parsed {len(starts)} != submissions {submissions}")

    votes=[]; answers=[]; self_answer=None
    for k,mt in enumerate(starts):
        end=starts[k+1].start() if k+1<len(starts) else len(t)
        block=t[mt.end():end]
        lines=[x.strip() for x in block.splitlines()]
        answer=next((x for x in lines if x),"")
        raw_rank=int(mt.group(1))
        author=mt.group(2)
        author_url=mt.group(3)
        display_rank=k+1

        score_match=re.search(r'(?m)^(\d+) 点｜([0-9.]+)$',block)
        score=int(score_match.group(1)) if score_match else None
        vote_rate=float(score_match.group(2)) if score_match else None

        vote_points=None
        voter_line=next((x for x in lines if target in x and any(f"{p}点 [" in x for p in (2,3,4))),None)
        if voter_line:
            pos=voter_line.index(target)
            marks=[(voter_line.rfind(f"{p}点 ",0,pos),p) for p in (2,3,4)]
            marks=[x for x in marks if x[0]>=0]
            if marks:
                vote_points=max(marks)[1]
                votes.append({
                    "rawRank":raw_rank,
                    "displayRank":display_rank,
                    "points":vote_points,
                    "author":author,
                    "answer":answer,
                    "percentile":raw_rank/submissions
                })

        is_self=('user_id=309' in author_url or author=='昼崎')
        if is_self:
            self_answer={"rawRank":raw_rank,"displayRank":display_rank,"answer":answer}

        answers.append({
            "rawRank":raw_rank,
            "displayRank":display_rank,
            "author":author,
            "answer":answer,
            "score":score,
            "voteRate":vote_rate,
            "votePoints":vote_points,
            "isSelf":is_self
        })

    division=2 if ((rid-52)%6)<4 else 1
    out[str(rid)]={
        "id":rid,
        "division":division,
        "prompt":prompt,
        "imageUrl":image_url,
        "source":f"https://oogiri-tmd.net/home/page.php?id={rid}",
        "submissions":submissions,
        "parsed":len(starts),
        "answers":answers,
        "votes":votes,
        "self":self_answer
    }
    time.sleep(2)

open("audit_82_87_full.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=2))
