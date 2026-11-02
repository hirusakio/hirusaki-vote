import { parse } from 'devalue';
import { writeFileSync } from 'node:fs';

const samples = {
  r1: '8f7dd4df-ba8f-4283-96c7-dcc445b26843',
  r2: '80b57476-d331-4d3f-9ff7-9eb28f0039de'
};
const revivers = {ShallowReactive:v=>v,Reactive:v=>v,Set:v=>new Set(v),Map:v=>new Map(v)};
const out={};
for (const [name,id] of Object.entries(samples)) {
  const url=`https://oogiri-mi.com/hangiri7/theme/${id}`;
  const res=await fetch(url,{headers:{'user-agent':'Mozilla/5.0'}});
  const html=await res.text();
  const m=html.match(/<script type="application\/json" data-nuxt-data="nuxt-app"[^>]*id="__NUXT_DATA__">([\s\S]*?)<\/script>/);
  out[name]={url,status:res.status,htmlLen:html.length};
  if(m){
    const parsed=parse(m[1],revivers);
    out[name].keys=Object.keys(parsed?.data||{});
    out[name].data=parsed?.data||null;
  } else {
    out[name].prefix=html.slice(0,5000);
  }
}
writeFileSync('hangiri7_rounds_debug.json',JSON.stringify(out,null,2));
