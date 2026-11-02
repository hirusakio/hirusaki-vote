import { parse } from 'devalue';
import { writeFileSync } from 'node:fs';
const EVENT='hangiri7';
const rounds=[
 {round:1,id:'f8709851-cfb3-4b8d-923d-dc4369888a7a'},
 {round:2,id:'0ef04231-168d-4576-896b-2fb97f51caf2'}
];
const revivers={ShallowReactive:v=>v,Reactive:v=>v,Set:v=>new Set(v),Map:v=>new Map(v)};
async function nuxtData(url){
 const r=await fetch(url,{headers:{'user-agent':'Mozilla/5.0'}});
 const html=await r.text();
 const m=html.match(/<script type="application\/json" data-nuxt-data="nuxt-app"[^>]*id="__NUXT_DATA__">([\s\S]*?)<\/script>/);
 if(!m)throw new Error('nuxt missing');
 return parse(m[1],revivers)?.data||{};
}
const out={};
for(const rr of rounds){
 const nd=await nuxtData(`https://oogiri-mi.com/${EVENT}/match/${rr.id}`);
 const view=nd[`match-view:${EVENT}:${rr.id}`]?.data;
 out[rr.round]=[];
 for(const t of [...view.themes].sort((a,b)=>a.display_order-b.display_order)){
  const item={id:t.id,group:t.group_name};
  try{
   const r=await fetch(`https://oogiri-mi.com/api/theme/${t.id}/view?preview=results`,{headers:{'user-agent':'Mozilla/5.0','accept':'application/json'}});
   item.status=r.status;
   const txt=await r.text();
   let j; try{j=JSON.parse(txt)}catch{item.body=txt.slice(0,1000);out[rr.round].push(item);continue}
   const d=j.data;
   item.success=j.success;
   item.isResultsAnnounced=d?.isResultsAnnounced;
   item.totalPostCount=d?.totalPostCount;
   item.finalResultsCount=d?.finalResults?.length;
   item.themeType=d?.theme?.theme_type;
   item.prompt=d?.theme?.theme_text;
   item.error=j.error||null;
  }catch(e){item.error=String(e)}
  out[rr.round].push(item);
 }
}
writeFileSync('hangiri7_rounds_debug.json',JSON.stringify(out,null,2));
