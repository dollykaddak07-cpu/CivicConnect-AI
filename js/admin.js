document.addEventListener('DOMContentLoaded', async () => {
  const idEl=document.getElementById('adminComplaintId'), statusEl=document.getElementById('adminStatus'), remarkEl=document.getElementById('adminRemark'), out=document.getElementById('adminResult');
  const file=document.getElementById('resolutionFile'), fileName=document.getElementById('resolutionFileName'), preview=document.getElementById('resolutionPreview');
  file?.addEventListener('change',()=>{ if(file.files[0]) { fileName.textContent=file.files[0].name; if(file.files[0].type.startsWith('image/')) { preview.src=URL.createObjectURL(file.files[0]); preview.hidden=false; } else preview.hidden=true; }});
  document.getElementById('loadComplaint')?.addEventListener('click', async()=>{
    const id=idEl.value.trim(); if(!id){out.textContent='Enter a complaint ID.';return;}
    try { const c=await CivicAPI.api('/api/complaints/'+encodeURIComponent(id)); renderCase(c); out.textContent='Complaint loaded.'; out.className='muted success-text'; }
    catch(e){out.textContent='Complaint not found.';out.className='muted error-text';}
  });
  document.getElementById('adminUpdate')?.addEventListener('click', async()=>{
    const id=idEl.value.trim(); if(!id){out.textContent='Enter a complaint ID.';return;}
    try { const c=await CivicAPI.api('/api/complaints/'+encodeURIComponent(id)+'/status',{method:'PATCH',body:JSON.stringify({status:statusEl.value,remark:remarkEl.value.trim()})}); renderCase(c); out.textContent=`Updated ${c.id} → ${c.status}`; out.className='muted success-text'; }
    catch(e){out.textContent='Complaint not found or backend is offline.';out.className='muted error-text';}
  });
  document.getElementById('submitResolution')?.addEventListener('click', async()=>{
    const id=idEl.value.trim(); if(!id){out.textContent='Enter a complaint ID first.';return}
    if(!file?.files?.[0]){out.textContent='Please select a resolution photo or video.';out.className='muted error-text';return}
    const fd=new FormData(); fd.append('resolution_file',file.files[0]); fd.append('resolution_remark',document.getElementById('resolutionRemark').value.trim()); fd.append('resolved_by',document.getElementById('resolvedBy').value.trim()||'Government Officer');
    try { out.textContent='Uploading proof and running AI evidence check...'; const c=await CivicAPI.api('/api/complaints/'+encodeURIComponent(id)+'/resolution',{method:'POST',body:fd}); renderCase(c); out.textContent=`Resolution proof submitted. ${c.id} is waiting for citizen verification.`; out.className='muted success-text'; }
    catch(e){out.textContent=e.message||'Resolution upload failed.';out.className='muted error-text';}
  });
  function renderCase(c){
    const box=document.getElementById('caseSummary'); if(!box)return; box.innerHTML=`<div class="case-head"><div><span class="panel-eyebrow">CASE ${esc(c.id)}</span><h3>${esc(c.title)}</h3><p>${esc(c.description)}</p></div><span class="case-status">${esc(c.status)}</span></div><div class="case-meta"><span><b>Department</b>${esc(c.department)}</span><span><b>Priority</b>${esc(c.priority)}</span><span><b>Category</b>${esc(c.category)}</span><span><b>AI Confidence</b>${c.confidence}%</span></div>${c.resolution_photo||c.resolution_video?`<div class="proof-mini"><strong>Resolution proof already submitted</strong><span>AI evidence relevance: ${c.resolution_confidence||0}%</span></div>`:''}`;
  }
  function esc(v){return String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;' }[m]))}
});
