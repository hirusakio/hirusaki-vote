import requests, re, json, time

TARGET='[昼崎](http://oogiri-tmd.net/home/mypage.php?user_id=309)'
data={}
for rid in range(52,82):
    url=f"https://r.jina.ai/http://oogiri-tmd.net/home/page.php?id={rid}"
    r=requests.get(url,timeout=60)
    r.raise_for_status()
    text=r.text.replace('\r\n','\n')
    m=re.search(r'投稿数：(\d+)',text)
    submissions=int(m.group(1)) if m else None

    # Each answer starts with two identical rank/author lines in Jina markdown.
    pat=re.compile(r'(?m)^(\d+)位\[([^\]]+)\]\([^\n]+\)\n\n\1位\[\2\]\([^\n]+\)\n')
    starts=list(pat.finditer(text))
    votes=[]
    for display_idx, mt in enumerate(starts, start=1):
        end=starts[display_idx].start() if display_idx < len(starts) else len(text)
        block=text[mt.end():end]
        raw_rank=int(mt.group(1))
        author=mt.group(2)

        # First non-empty line after the duplicated header is the answer.
        lines=[ln.strip() for ln in block.splitlines()]
        answer=''
        for ln in lines:
            if ln:
                answer=ln
                break

        # Find the detailed voter line containing Hirusaki, not the author header.
        voter_line=None
        for ln in lines:
            if TARGET in ln and ('2点 [' in ln or '3点 [' in ln or '4点 [' in ln):
                voter_line=ln
                break
        if not voter_line:
            continue

        idx=voter_line.index(TARGET)
        markers=[]
        for pts in (4,3,2):
            p=voter_line.rfind(f'{pts}点 ',0,idx)
            if p>=0:
                markers.append((p,pts))
        if not markers:
            raise RuntimeError(f'Could not determine points round {rid}, rank {raw_rank}')
        points=max(markers)[1]
        votes.append({
            'rawRank':raw_rank,
            'displayRank':display_idx,
            'points':points,
            'author':author,
            'answer':answer,
            'percentile': (raw_rank/submissions if submissions else None),
        })

    data[str(rid)]={
        'submissions':submissions,
        'answerCountParsed':len(starts),
        'votes':votes,
        'voteCount':len(votes),
        'pointTotal':sum(v['points'] for v in votes),
        'source':f'https://oogiri-tmd.net/home/page.php?id={rid}',
    }
    time.sleep(0.25)

open('audit_scraped_52_81.json','w',encoding='utf-8').write(json.dumps(data,ensure_ascii=False,indent=2))
print(json.dumps({rid:{'submissions':v['submissions'],'parsed':v['answerCountParsed'],'votes':v['voteCount'],'points':v['pointTotal']} for rid,v in data.items()},ensure_ascii=False,indent=2))
