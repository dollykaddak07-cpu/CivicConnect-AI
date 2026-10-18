let charts = {};
let allComplaints = [];

const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));

function dateOf(c) { const d = new Date(String(c.created_at || '').replace(' ', 'T')); return isNaN(d) ? null : d; }
function filteredComplaints(period) {
  const now = new Date();
  if (period === 'all') return allComplaints;
  const start = new Date(now);
  if (period === 'year') start.setMonth(0, 1), start.setHours(0,0,0,0);
  if (period === 'quarter') start.setMonth(now.getMonth() - 2, 1), start.setHours(0,0,0,0);
  if (period === 'month') start.setDate(now.getDate() - 29), start.setHours(0,0,0,0);
  return allComplaints.filter(c => { const d = dateOf(c); return d && d >= start && d <= now; });
}
function countBy(rows, key) { return rows.reduce((o,c) => { const k = c[key] || 'Other'; o[k] = (o[k]||0)+1; return o; }, {}); }
function pct(a,b) { return b ? Math.round((a/b)*1000)/10 : 0; }
function destroyCharts(){ Object.values(charts).forEach(c => c?.destroy()); charts = {}; }

const palette = ['#2563eb','#16a36a','#f59e0b','#ef4444','#7c3aed','#0891b2','#64748b','#db2777'];
const gridColor = 'rgba(148,163,184,.18)';
const tickColor = '#718096';

function chartDefaults() {
  return { responsive:true, maintainAspectRatio:false, animation:{duration:650}, plugins:{legend:{labels:{usePointStyle:true,boxWidth:8,color:'#536174',font:{size:11,weight:'600'}}}}, scales:{x:{grid:{display:false},ticks:{color:tickColor,font:{size:10}}},y:{grid:{color:gridColor},ticks:{color:tickColor,font:{size:10},precision:0},beginAtZero:true}} };
}

function renderCharts(rows) {
  if (typeof Chart === 'undefined') return;
  destroyCharts();
  const cat = countBy(rows,'category');
  const priority = countBy(rows,'priority');
  const dept = countBy(rows,'department');

  const trend = {};
  const now = new Date();
  for(let i=5;i>=0;i--){ const d=new Date(now.getFullYear(),now.getMonth()-i,1); const key=d.toLocaleString('en-US',{month:'short'}); trend[key]=0; }
  rows.forEach(c=>{const d=dateOf(c); if(!d)return; const key=d.toLocaleString('en-US',{month:'short'}); if(key in trend)trend[key]++;});

  charts.trend = new Chart($('complaintTrendChart'),{type:'line',data:{labels:Object.keys(trend),datasets:[{data:Object.values(trend),borderColor:'#2563eb',backgroundColor:'rgba(37,99,235,.10)',fill:true,tension:.38,pointRadius:4,pointHoverRadius:6,pointBackgroundColor:'#fff',pointBorderWidth:2,pointBorderColor:'#2563eb'}]},options:{...chartDefaults(),plugins:{legend:{display:false}},scales:{x:{grid:{display:false},ticks:{color:tickColor}},y:{grid:{color:gridColor},ticks:{color:tickColor,precision:0},beginAtZero:true}}}});

  charts.category = new Chart($('categoryChart'),{type:'doughnut',data:{labels:Object.keys(cat),datasets:[{data:Object.values(cat),backgroundColor:palette,borderWidth:0,hoverOffset:5}]},options:{responsive:true,maintainAspectRatio:false,cutout:'72%',plugins:{legend:{position:'bottom',labels:{usePointStyle:true,boxWidth:8,padding:12,color:'#536174',font:{size:10,weight:'600'}}}}}});
  charts.priority = new Chart($('priorityChart'),{type:'doughnut',data:{labels:Object.keys(priority),datasets:[{data:Object.values(priority),backgroundColor:['#ef4444','#f59e0b','#22c55e','#94a3b8'],borderWidth:0,hoverOffset:5}]},options:{responsive:true,maintainAspectRatio:false,cutout:'70%',plugins:{legend:{position:'bottom',labels:{usePointStyle:true,boxWidth:8,padding:12,color:'#536174',font:{size:10,weight:'600'}}}}}});

  const depLabels=Object.keys(dept); const depResolved=depLabels.map(d=>rows.filter(c=>(c.department||'Other')===d && c.status==='Resolved').length);
  charts.department = new Chart($('departmentChart'),{type:'bar',data:{labels:depLabels,datasets:[{label:'Total',data:depLabels.map(d=>dept[d]),backgroundColor:'rgba(37,99,235,.82)',borderRadius:6,barThickness:16},{label:'Resolved',data:depResolved,backgroundColor:'rgba(22,163,106,.78)',borderRadius:6,barThickness:16}]},options:{...chartDefaults(),plugins:{legend:{position:'top',align:'end',labels:{usePointStyle:true,boxWidth:8,color:'#536174',font:{size:10,weight:'600'}}}},scales:{x:{grid:{display:false},ticks:{color:tickColor,font:{size:10}}},y:{grid:{color:gridColor},ticks:{color:tickColor,precision:0},beginAtZero:true}}}});
}

function renderTable(rows){
  const zones={};
  rows.forEach(c=>{const z=(c.location||'Unknown location').trim()||'Unknown location'; if(!zones[z])zones[z]={total:0,resolved:0,critical:0}; zones[z].total++; if(c.status==='Resolved')zones[z].resolved++; if(c.priority==='Critical')zones[z].critical++;});
  const data=Object.entries(zones).sort((a,b)=>b[1].total-a[1].total).slice(0,7);
  $('locationTableBody').innerHTML=data.length?data.map(([z,v],i)=>`<tr><td><div class="zone-cell"><span>${i+1}</span><strong>${esc(z)}</strong></div></td><td>${v.total}</td><td>${v.resolved}</td><td><b class="critical-number">${v.critical}</b></td><td><div class="rate-cell"><div><span style="width:${pct(v.resolved,v.total)}%"></span></div><strong>${pct(v.resolved,v.total)}%</strong></div></td></tr>`).join(''):`<tr><td colspan="5" class="empty-row">No location data available for this period.</td></tr>`;
}

function renderTopIssues(rows){
  const cat=countBy(rows,'category'); const entries=Object.entries(cat).sort((a,b)=>b[1]-a[1]); const max=entries[0]?.[1]||1;
  $('topIssues').innerHTML=entries.length?entries.slice(0,6).map(([name,n],i)=>`<div class="issue-row"><div class="issue-meta"><span><b>${i+1}</b>${esc(name)}</span><strong>${n}</strong></div><div class="issue-bar"><span style="width:${Math.max(8,(n/max)*100)}%"></span></div></div>`).join(''):'<div class="empty-row">No complaint data available.</div>';
}

function renderInsights(rows){
  const total=rows.length, resolved=rows.filter(c=>c.status==='Resolved').length, critical=rows.filter(c=>c.priority==='Critical').length;
  const active=rows.filter(c=>c.status==='Pending'||c.status==='In Progress').length;
  const cat=countBy(rows,'category'); const top=Object.entries(cat).sort((a,b)=>b[1]-a[1])[0];
  const gps=rows.filter(c=>c.latitude!=null && c.longitude!=null).length;
  let text='The dashboard is monitoring the latest complaint workload and service-delivery signals.';
  if(total===0) text='No complaints match the selected period. Expand the analysis period to view governance trends.';
  else if(critical>0) text=`${critical} critical ${critical===1?'case requires':'cases require'} priority attention. ${top?`${top[0]} is the most reported issue.`:''}`;
  else if(active>0) text=`${active} active ${active===1?'case is':'cases are'} currently moving through the resolution workflow.`;
  else text='All complaints in the selected period are resolved. Service delivery is currently on track.';
  $('insightText').textContent=text;
  const items=[`Resolution rate: ${pct(resolved,total)}%`,`Top issue: ${top?esc(top[0]):'—'}`,`GPS coverage: ${pct(gps,total)}%`];
  $('insightList').innerHTML=items.map(x=>`<div><span>✓</span>${x}</div>`).join('');
}

function render(rows){
  const total=rows.length, resolved=rows.filter(c=>c.status==='Resolved').length, pending=rows.filter(c=>c.status==='Pending').length, progress=rows.filter(c=>c.status==='In Progress').length, rejected=rows.filter(c=>c.status==='Rejected').length, critical=rows.filter(c=>c.priority==='Critical').length, gps=rows.filter(c=>c.latitude!=null && c.longitude!=null).length;
  $('totalComplaints').textContent=total; $('resolvedComplaints').textContent=resolved; $('pendingComplaints').textContent=pending+progress; $('criticalComplaints').textContent=critical; $('gpsCoverage').textContent=pct(gps,total)+'%'; $('resolutionRate').textContent=pct(resolved,total)+'%'; $('resolutionProgress').style.width=pct(resolved,total)+'%';
  $('resolvedSub').textContent=resolved?`${pct(resolved,total)}% of selected cases`: 'No resolved cases yet';
  $('statusResolved').textContent=resolved; $('statusProgress').textContent=progress; $('statusPending').textContent=pending; $('statusRejected').textContent=rejected;
  $('categoryCount').textContent=total;
  renderCharts(rows); renderTable(rows); renderTopIssues(rows); renderInsights(rows);
}

async function load(){
  try { const data=await CivicAPI.api('/api/complaints'); allComplaints=Array.isArray(data)?data:[]; render(filteredComplaints($('analysisPeriod').value)); toast('Analytics refreshed'); }
  catch(e){ console.error(e); $('insightText').textContent='Unable to load live analytics. Make sure the FastAPI server is running.'; toast('Could not load analytics',true); }
}

function toast(msg,error=false){const t=$('analyticsToast');t.textContent=msg;t.className='cc-toast show'+(error?' error':'');clearTimeout(window._toast);window._toast=setTimeout(()=>t.className='cc-toast',2300);}
function exportReport(){
  const rows=filteredComplaints($('analysisPeriod').value); const head=['ID','Title','Category','Priority','Department','Status','Location','Language','Created At'];
  const body=rows.map(c=>[c.id,c.title,c.category,c.priority,c.department,c.status,c.location,c.language,c.created_at]); const csv=[head,...body].map(r=>r.map(v=>`"${String(v??'').replace(/"/g,'""')}"`).join(',')).join('\n'); const blob=new Blob([csv],{type:'text/csv;charset=utf-8;'}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=`civicconnect-analytics-${new Date().toISOString().slice(0,10)}.csv`; a.click(); URL.revokeObjectURL(a.href); toast('Report exported');
}

document.addEventListener('DOMContentLoaded',()=>{ $('analysisPeriod').addEventListener('change',()=>render(filteredComplaints($('analysisPeriod').value))); $('refreshBtn').addEventListener('click',load); $('exportReportBtn').addEventListener('click',exportReport); load(); });
