import { parse } from 'devalue';
import { writeFileSync } from 'node:fs';

const EVENT='hangiri7';
const SELF='昼崎';
const rounds=[
  {round:1,id:'f8709851-cfb3-4b8d-923d-dc4369888a7a'},
  {round:2,id:'0ef04231-168d-4576-896b-2fb97f51caf2'}
];
const revivers={ShallowReactive:v=>v,Reactive:v=>v,Set:v=>new Set(v),Map:v=>new Map(v)};

const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function get(url,headers={}){
  let last;
  for(let i=0;i<5;i++){
    try{
      const r=await fetch(url,{headers:{'user-agent':'Mozilla/5.0',...headers}});
      if(r.ok)return r;
      last=new Error(`${url}: ${r.status}`);
    }catch(e){last=e}
    await sleep(1200*(i+1));
  }
  throw last;
}
async function nuxtData(url){
  const r=await get(url);
  const html=await r.text();
  const m=html.match(/<script type="application\/json" data-nuxt-data="nuxt-app"[^>]*id="__NUXT_DATA__">([\s\S]*?)<\/script>/);
  if(!m) throw new Error('Nuxt data missing: '+url);
  return parse(m[1],revivers)?.data||{};
}

const out={event:EVENT,generatedAt:new Date().toISOString(),rounds:[]};
for(const rr of rounds){
  const matchUrl=`https://oogiri-mi.com/${EVENT}/match/${rr.id}`;
  const nd=await nuxtData(matchUrl);
  const view=nd[`match-view:${EVENT}:${rr.id}`]?.data;
  if(!view) throw new Error('match view missing '+rr.round);
  const themes=[...view.themes].sort((a,b)=>a.display_order-b.display_order);
  const groups=[];
  for(const t of themes){
    const api=`https://oogiri-mi.com/api/theme/${t.id}/view?preview=results`;
    const r=await get(api,{'accept':'application/json'});
    const j=await r.json();
    const d=j.data;
    if(!d?.isResultsAnnounced) throw new Error('results not announced '+t.id);
    const th=d.theme;
    const answers=(d.finalResults||[]).map((a,i)=>({
      position:i+1,
      rank:a.rank,
      postId:a.post_id,
      author:a.username,
      answer:a.work_text,
      totalScore:a.total_score,
      voteRate:a.vote_rate,
      voteBreakdown:a.vote_breakdown||{},
      isSelf:a.username===SELF,
      passed:a.rank<=th.advancement_team_count
    }));
    if(answers.length!==d.totalPostCount) throw new Error(`count mismatch ${t.id}: ${answers.length} != ${d.totalPostCount}`);
    const selfVoter=(d.voters||[]).find(v=>v.username===SELF);
    groups.push({
      id:t.id,
      group:t.group_name,
      displayOrder:t.display_order,
      prompt:th.theme_text||'画像で一言',
      promptType:th.theme_type,
      imageUrl:th.theme_image_url||null,
      provider:th.theme_provider||null,
      submissions:d.totalPostCount,
      voters:d.totalVoteCount,
      advancementCount:th.advancement_team_count,
      selfVoteCount:selfVoter?.vote_count??null,
      source:`https://oogiri-mi.com/${EVENT}/theme/${t.id}`,
      answers
    });
    await sleep(350);
  }
  out.rounds.push({
    round:rr.round,
    matchId:rr.id,
    name:view.currentMatch.match_name,
    adminMessage:view.currentMatch.admin_message,
    source:matchUrl,
    groups
  });
}
writeFileSync('hangiri7_1_2.json',JSON.stringify(out,null,2));
