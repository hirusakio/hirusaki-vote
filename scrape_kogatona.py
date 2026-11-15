"""Refresh the public Kogatona results with Python and lxml."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import os
from hashlib import sha256
from pathlib import Path
import re
import time
from urllib.parse import urljoin
from urllib.request import urlopen

from lxml import html

BASE = 'https://koganezawa.main.jp/cgi-bin/votekt2026/vote.cgi'
PLAYER = '昼崎'

def get(url):
    cache_dir = os.environ.get("KOGATONA_CACHE")
    cache = Path(cache_dir) / sha256(url.encode()).hexdigest() if cache_dir else None
    if cache and cache.exists():
        return html.fromstring(cache.read_bytes().decode("cp932", errors="replace"))
    for attempt in range(3):
        try:
            with urlopen(url, timeout=25) as response:
                raw = response.read()
                if cache:
                    cache.write_bytes(raw)
                return html.fromstring(raw.decode('cp932', errors='replace'))
        except OSError:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

def content(node, url):
    for line_break in node.xpath('.//br'):
        line_break.tail = '\n' + (line_break.tail or '')
    text = node.text_content().strip()
    images = [urljoin(url, src) for src in node.xpath('.//img/@src')]
    return text, [src for src in images if src.startswith('https://')]

def read_match(entry):
    title, url, block, round_name = entry
    page = get(url)
    prompt = page.xpath('//td[@class="THEME"]/div[@class="BOX3"]')[0]
    text, images = content(prompt, url)
    text = text.split('※このお題に投稿できるのは')[0].strip()
    answers = []
    for link in page.xpath('//a[contains(@href,"mode=cmt") and contains(@href,"eno=")]'):
        row = link.xpath('ancestor::tr[1]')[0]
        cells = row.xpath('./td')
        detail = urljoin(url, link.get('href'))
        label = link.xpath('ancestor::div[1]')[0]
        tt = label.xpath('./tt')[0]
        suffix = label.text_content().removeprefix(tt.text_content()).strip()
        author = suffix.removesuffix('さんの作品').strip()
        if not suffix.endswith('さんの作品'):
            raise ValueError((detail, suffix))
        body = cells[2].xpath('./div[starts-with(@class,"ITEM")]')[0]
        answer, media = content(body, url)
        breakdown = {int(p): int(n) for p, n in re.findall(r'(\d+)点\s*(\d+)', label.xpath('./tt')[0].text_content())}
        score = int(cells[1].text_content())
        if sum(p*n for p,n in breakdown.items()) != score:
            raise ValueError((detail, score, breakdown))
        answers.append(dict(rank=int(cells[0].text_content()), score=score, author=author,
                            text=answer, images=media, source=detail, breakdown=breakdown))
    note = page.xpath('//td[@class="NOTE"]')[0].text_content()
    expected = int(re.search(r'投稿数：(\d+)', note)[1])
    if expected != len(answers):
        raise ValueError((url, expected, len(answers)))
    return dict(title=title, source=url, block=block, round=round_name, prompt=text,
                images=images, answers=answers)

def read_vote(answer):
    page = get(answer['source'])
    tables = page.xpath('//table[.//td[contains(text(),"この作品への投票者")]]')
    if not tables:
        raise ValueError(f"Missing voter list: {answer['source']}")
    voters = []
    for row in tables[0].xpath('.//tr'):
        cells = row.xpath('./td')
        if len(cells) == 2 and (m := re.fullmatch(r'(\d+)点', cells[0].text_content().strip())):
            voters.append((int(m[1]), cells[1].text_content().strip()))
    expected = Counter({p:n for p,n in answer['breakdown'].items() if n})
    actual = Counter(p for p, _ in voters)
    if actual != expected:
        answer['voteListMismatch'] = True
        print('Voter count mismatch:', answer['source'], dict(expected), dict(actual), flush=True)
    return sum(p for p, name in voters if name == PLAYER)

def main():
    path = Path(__file__).with_name('kogatona.json')
    previous = json.loads(path.read_text()) if path.exists() else []
    known = {m['source'] for m in previous}
    entries = []
    pages = [BASE]
    visited = set()
    found = set()
    while pages:
        page_url = pages.pop(0)
        if page_url in visited:
            continue
        visited.add(page_url)
        page = get(page_url)
        pages.extend(urljoin(BASE, href) for href in page.xpath(
            '//a[starts-with(@href,"vote.cgi?start=")]/@href'
        ) if urljoin(BASE, href) not in visited)
        for a in page.xpath('//a[starts-with(@href,"vote.cgi?no=")]'):
            row = a.xpath('ancestor::tr[1]')[0]
            title = a.text_content().strip()
            match = re.match(r'コガトナ2026(?:-27)?\s+(?:([A-Z])\s+)?([^\s]+?(?:戦|決勝))\s+(.+)', title)
            url = urljoin(BASE, a.get('href'))
            if not match or url in known or url in found:
                continue
            if '結果' in row.xpath('./td[3]')[0].text_content():
                entries.append((match[3], url, match[1] or '', match[2]))
                found.add(url)
    print('New matches:', len(entries), flush=True)
    with ThreadPoolExecutor(max_workers=12) as pool:
        new = list(pool.map(read_match, reversed(entries)))
        answers = [a for m in new for a in m['answers']]
        print('Answer pages:', len(answers), flush=True)
        for i, (answer, points) in enumerate(zip(answers, pool.map(read_vote, answers)), 1):
            answer['vote'] = points
            if i % 100 == 0:
                print('Checked:', i, flush=True)
    output = path.with_suffix('.tmp')
    output.write_text(json.dumps(previous + new, ensure_ascii=False, separators=(',', ':')) + '\n')
    output.replace(path)

if __name__ == '__main__':
    main()
