import { writeFileSync } from 'node:fs';
const ids=['8f7dd4df-ba8f-4283-96c7-dcc445b26843','80b57476-d331-4d3f-9ff7-9eb28f0039de'];
const out={};
for(const id of ids){
 const url=`https://oogiri-mi.com/api/theme/${id}/view?preview=results`;
 const r=await fetch(url,{headers:{'user-agent':'Mozilla/5.0','accept':'application/json'}});
 const txt=await r.text();
 let data; try{data=JSON.parse(txt)}catch{data=txt.slice(0,10000)}
 out[id]={status:r.status,data};
}
writeFileSync('hangiri7_rounds_debug.json',JSON.stringify(out,null,2));
