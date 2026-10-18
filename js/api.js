const API_BASE = window.location.origin.includes(':8000') ? '' : 'http://127.0.0.1:8000';
async function api(path, options={}){
  const request = {...options};
  const isFormData = request.body instanceof FormData;
  request.headers = {...(options.headers || {})};
  // Do not set Content-Type for FormData: the browser must add the multipart boundary.
  if (!isFormData && request.body !== undefined && !request.headers['Content-Type']) {
    request.headers['Content-Type'] = 'application/json';
  }
  const r = await fetch(API_BASE + path, request);
  if(!r.ok) throw new Error(await r.text() || `HTTP ${r.status}`);
  return r.json();
}
window.CivicAPI={api,base:API_BASE};
