(function(){
  'use strict';
  if(window.__CIVICCONNECT_CHATBOT__) return;
  window.__CIVICCONNECT_CHATBOT__=true;
  function esc(v){return String(v==null?'':v).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));}
  function mount(){
    if(!document.body || document.getElementById('civicChatbot')) return;
    const w=document.createElement('div'); w.id='civicChatbot';
    w.innerHTML='<button type="button" class="cc-chat-fab" id="ccChatFab" title="CivicConnect AI Assistant" aria-label="Open CivicConnect AI Assistant"><span class="cc-pulse"></span><span class="cc-robot-icon">🤖</span></button>'+
      '<section class="cc-chat-panel" id="ccChatPanel" aria-hidden="true"><div class="cc-chat-head"><div class="cc-bot-avatar"><span class="cc-robot-icon">🤖</span></div><div class="cc-bot-title"><strong>CivicConnect AI</strong><span><i class="fa-solid fa-circle"></i> Live civic assistant</span></div><button type="button" class="cc-close" id="ccChatClose" aria-label="Close">×</button></div><div class="cc-chat-banner"><span class="cc-bolt-icon">⚡</span><div><b>Connected to live civic data</b><small>Ask about complaints, status, resolution proof, departments, or describe an issue.</small></div></div><div class="cc-chat-messages" id="ccChatMessages"><div class="cc-msg cc-bot"><div class="cc-bubble">Hello! 👋 I’m CivicConnect AI. I can check your live complaint data, explain resolution status, identify departments, and help you report an issue.</div></div></div><div class="cc-quick"><button type="button" data-q="Track complaint CC1028">Track complaint</button><button type="button" data-q="Check resolution for CC1028">Resolution proof</button><button type="button" data-q="Which department handles street lights?">Find department</button><button type="button" data-q="I want to report a road problem">Report issue</button></div><form class="cc-chat-input" id="ccChatForm"><input id="ccChatInput" autocomplete="off" placeholder="Ask a civic question..."/><button type="submit" aria-label="Send"><span class="cc-send-icon">➤</span></button></form></section>';
    document.body.appendChild(w);
    const panel=w.querySelector('#ccChatPanel'), fab=w.querySelector('#ccChatFab'), close=w.querySelector('#ccChatClose'), box=w.querySelector('#ccChatMessages'), input=w.querySelector('#ccChatInput');
    const toggle=o=>{panel.classList.toggle('open',o);panel.setAttribute('aria-hidden',String(!o));if(o)setTimeout(()=>input.focus(),80)};
    fab.addEventListener('click',()=>toggle(!panel.classList.contains('open'))); close.addEventListener('click',()=>toggle(false));
    const add=(text,who)=>{const row=document.createElement('div');row.className='cc-msg cc-'+(who||'bot');row.innerHTML='<div class="cc-bubble">'+esc(text).replace(/\n/g,'<br>')+'</div>';box.appendChild(row);box.scrollTop=box.scrollHeight};
    const typing=on=>{let t=w.querySelector('#ccTyping');if(on&&!t){t=document.createElement('div');t.id='ccTyping';t.className='cc-msg cc-bot';t.innerHTML='<div class="cc-bubble cc-typing"><i></i><i></i><i></i><span>Checking live data…</span></div>';box.appendChild(t);box.scrollTop=box.scrollHeight}else if(!on&&t)t.remove()};
    async function ask(q){add(q,'user');typing(true);try{const base=(window.CivicAPI&&typeof window.CivicAPI.base==='string')?window.CivicAPI.base:'';const r=await fetch(base+'/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:q})});const data=await r.json();if(!r.ok)throw Error(data.detail||'Server error');typing(false);add(data.response||'I could not find an answer from the live civic system.')}catch(e){typing(false);add('I could not connect to the live CivicConnect server. Please make sure FastAPI is running at http://127.0.0.1:8000 and refresh the page.');console.error('CivicConnect chatbot:',e)}}
    w.querySelector('#ccChatForm').addEventListener('submit',e=>{e.preventDefault();const q=input.value.trim();if(q){input.value='';ask(q)}});w.querySelectorAll('.cc-quick button').forEach(b=>b.addEventListener('click',()=>ask(b.dataset.q)));
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);else mount();
})();
