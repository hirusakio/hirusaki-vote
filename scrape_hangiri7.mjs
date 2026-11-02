import { parse } from 'devalue';
import { writeFileSync } from 'node:fs';

const rounds = {
  1: 'f8709851-cfb3-4b8d-923d-dc4369888a7a',
  2: '0ef04231-168d-4576-896b-2fb97f51caf2'
};
const revivers = {
  ShallowReactive: v => v,
  Reactive: v => v,
  Set: v => new Set(v),
  Map: v => new Map(v)
};
const out = {};
for (const [round,id] of Object.entries(rounds)) {
  const url = `https://oogiri-mi.com/hangiri7/match/${id}`;
  const res = await fetch(url, {headers:{'user-agent':'Mozilla/5.0'}});
  if (!res.ok) throw new Error(`${url}: ${res.status}`);
  const html = await res.text();
  const m = html.match(/<script type="application\/json" data-nuxt-data="nuxt-app"[^>]*id="__NUXT_DATA__">([\s\S]*?)<\/script>/);
  if (!m) throw new Error(`Nuxt data missing for round ${round}`);
  const data = parse(m[1], revivers);
  const keys = Object.keys(data?.data || {});
  const texts = JSON.stringify(data);
  const uuidSet = [...new Set(texts.match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/g) || [])];
  out[round] = {
    url,
    keys,
    data: data?.data || null,
    uuidCount: uuidSet.length,
    uuids: uuidSet
  };
}
writeFileSync('hangiri7_rounds_debug.json', JSON.stringify(out,null,2));
