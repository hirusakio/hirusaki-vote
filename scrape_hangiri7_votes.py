"""Read public per-answer voters; publish only the selected user's vote points."""
import collections
import concurrent.futures
import datetime
import json
import pathlib
import time
import urllib.request

DATA = pathlib.Path(__file__).with_name('hangiri7_1_2.json')
CACHE = pathlib.Path('/tmp/hangiri7-vote-cache')
SELF = '昼崎'
SELF_ID = 'a7949ad8-4081-704b-64cd-5a2f3f0e7551'


def read_answer(item):
    round_number, group, answer = item
    url = f"https://oogiri-mi.com/api/theme/{group['id']}/post/{answer['postId']}/view"
    cached = CACHE / (answer['postId'] + '.json')
    for attempt in range(4):
        try:
            if cached.exists():
                response = json.loads(cached.read_text())
            else:
                request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(request, timeout=40) as stream:
                    response = json.load(stream)
            assert response['success'], url
            detail = response['data']
            assert detail['theme']['id'] == group['id'], url
            assert detail['post']['id'] == answer['postId'], url
            assert detail['post']['username'] == answer['author'], url
            stats = detail['voteStats']
            voters = detail['voters']
            actual = collections.Counter(v['vote_points'] for v in voters if not v.get('is_bonus'))
            expected = {v['points']: v['count'] for v in stats['vote_breakdown'] if v['count']}
            assert dict(actual) == expected, (url, actual, expected)
            own = [v for v in voters if v['user_id'] == SELF_ID and not v.get('is_bonus')]
            assert len(own) <= 1, url
            assert all(v['username'] == SELF for v in own), url
            points = own[0]['vote_points'] if own else 0
            assert points in (0, 2, 3, 4), url
            assert not (answer['isSelf'] and points), 'Bonus counted as self vote'
            cached.write_text(json.dumps(response, ensure_ascii=False))
            return answer['postId'], points, stats['total_score']
        except Exception:
            if attempt == 3:
                raise
            time.sleep(1 + attempt * 2)


if __name__ == '__main__':
    CACHE.mkdir(exist_ok=True)
    data = json.loads(DATA.read_text())
    items = [(r['round'], g, a) for r in data['rounds'] for g in r['groups'] for a in g['answers']]
    results = {}
    detail_scores = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(read_answer, item) for item in items]
        for future in concurrent.futures.as_completed(futures):
            post_id, points, score = future.result()
            results[post_id] = points
            detail_scores[post_id] = score
            if len(results) % 20 == 0:
                print(f'Checked {len(results)}/{len(items)} answers', flush=True)
    assert len(results) == len(items)
    for _, _, answer in items:
        answer['selfVote'] = results[answer['postId']]
        if detail_scores[answer['postId']] != answer['totalScore']:
            answer['detailTotalScore'] = detail_scores[answer['postId']]
        else:
            answer.pop('detailTotalScore', None)
    data['selfVotes'] = {
        'username': SELF,
        'checkedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'checkedAnswers': len(results),
        'source': 'public-post-voters',
        'complete': True,
    }
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    for round_data in data['rounds']:
        points = collections.Counter(a['selfVote'] for g in round_data['groups'] for a in g['answers'])
        print(f"Round {round_data['round']}: {dict(points)}", flush=True)
