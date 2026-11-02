import { writeFileSync } from 'node:fs';

const url='https://oogiri-mi.com/hangiri7/theme/8f7dd4df-ba8f-4283-96c7-dcc445b26843';
const html=await (await fetch(url,{headers:{'user-agent':'Mozilla/5.0'}})).text();
const assets=[...new Set([
 ...[...html.matchAll(/<script[^>]+src="([^"]+)"/g)].map(m=>m[1]),
 ...[...html.matchAll(/<link[^>]+(?:rel="modulepreload"|rel="prefetch")[^>]+href="([^"]+\.js)"/g)].map(m=>m[1])
])];
const out=[];
for(const src of assets){
 const u=new URL(src,url).href;
 try{
   const r=await fetch(u,{headers:{'user-agent':'Mozilla/5.0'}});
   const txt=await r.text();
   const hits=[...new Set([
     ...[...txt.matchAll(/["'`](\/api\/[^"'\`\s]*)["'`]/g)].map(m=>m[1]),
     ...[...txt.matchAll(/["'`]([^"'\`]*vote[^"'\`]{0,100})["'`]/gi)].map(m=>m[1])
   ])].filter(x=>/theme|post|vote|result|event|match|score/i.test(x));
   if(hits.length) out.push({url:u,hits:hits.slice(0,300)});
 }catch(e){out.push({url:u,error:String(e)})}
}
writeFileSync('hangiri7_rounds_debug.json',JSON.stringify({assets,out},null,2));
