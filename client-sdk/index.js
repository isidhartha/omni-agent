"use strict";
class OmniAgentClient {
  constructor(o={}) { this.host=o.host||"http://localhost:8000"; this.timeout=o.timeout||60000; }
  async _req(m,p,b) {
    const c=new AbortController(),t=setTimeout(()=>c.abort(),this.timeout);
    try {
      const r=await fetch(`${this.host}${p}`,{method:m,headers:{"Content-Type":"application/json"},body:b?JSON.stringify(b):undefined,signal:c.signal});
      if(!r.ok) throw new Error(`OmniAgent API ${r.status}`);
      return r.json();
    } finally { clearTimeout(t); }
  }
  runAgent(type,task,options={}) { return this._req("POST","/api/v1/agent/run",{agent_type:type,task,...options}); }
  reviewPR(diff,context="") { return this._req("POST","/api/v1/pr/review",{diff,context}); }
  debug(code,error) { return this._req("POST","/api/v1/debug",{code,error}); }
  analyzeRepo(path) { return this._req("POST","/api/v1/repo/analyze",{path}); }
  listAgents() { return this._req("GET","/api/v1/agents",null); }
  health() { return this._req("GET","/health",null); }
}
module.exports=OmniAgentClient;
