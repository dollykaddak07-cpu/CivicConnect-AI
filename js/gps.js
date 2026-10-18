(function(){
'use strict';
let map=null, marker=null, accuracyCircle=null, watchId=null;
const $=id=>document.getElementById(id);
function setStatus(text,kind){const e=$('gpsStatus');if(e){e.textContent=text;e.className='gps-status-box '+(kind||'');}}
function set(id,text){const e=$(id);if(e)e.textContent=text;}
function coords(lat,lon){set('gpsCoords',`Latitude ${lat.toFixed(6)} | Longitude ${lon.toFixed(6)}`);}
function update(lat,lon,acc){
  if(!Number.isFinite(lat)||!Number.isFinite(lon))return;
  $('complaintLatitude').value=lat;$('complaintLongitude').value=lon;
  coords(lat,lon);set('gpsAccuracy',`${Math.round(acc||0)} m accuracy`);
  setStatus('GPS location captured successfully ✓','success');
  const input=$('complaintLocation'); if(input && !input.value) input.value=`${lat.toFixed(6)}, ${lon.toFixed(6)}`;
  if(map&&window.L){const p=[lat,lon];map.setView(p,17);if(!marker){marker=L.marker(p).addTo(map).bindPopup('Your current location').openPopup();}else marker.setLatLng(p);if(!accuracyCircle)accuracyCircle=L.circle(p,{radius:Math.max(acc||20,5)}).addTo(map);else accuracyCircle.setLatLng(p).setRadius(Math.max(acc||20,5));}
}
async function reverse(lat,lon){
 try{const r=await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}`,{headers:{Accept:'application/json'}});if(!r.ok)throw new Error();const d=await r.json();return d.display_name||`${lat.toFixed(6)}, ${lon.toFixed(6)}`;}catch(e){return `${lat.toFixed(6)}, ${lon.toFixed(6)}`;}
}
function explainError(e){if(e&&e.code===1)return 'Location permission denied. In Chrome click the site icon beside the address → Location → Allow, then refresh.';if(e&&e.code===2)return 'Location unavailable. Turn ON Windows Settings → Privacy & security → Location, then try again.';if(e&&e.code===3)return 'Location request timed out. Keep Wi‑Fi ON, allow Windows location, and try again.';return 'Unable to get your location. Check Chrome and Windows location permissions.';}
function locate(){
 const b=$('useMyLocation');
 if(!navigator.geolocation){setStatus('❌ Geolocation is not supported by this browser.','error');return;}
 if(b){b.disabled=true;b.innerHTML='<i class="fa-solid fa-spinner fa-spin"></i> Getting Location...';}
 setStatus('📡 Requesting your location... Please click Allow if Chrome asks.','loading');
 navigator.geolocation.getCurrentPosition(async p=>{
   update(p.coords.latitude,p.coords.longitude,p.coords.accuracy);
   const input=$('complaintLocation'); if(input){input.value=await reverse(p.coords.latitude,p.coords.longitude);}
   if(b){b.disabled=false;b.innerHTML='<i class="fa-solid fa-location-crosshairs"></i> Location Captured ✓';}
   startWatch();
 },e=>{
   setStatus('❌ '+explainError(e),'error');
   if(b){b.disabled=false;b.innerHTML='<i class="fa-solid fa-location-crosshairs"></i> Try Location Again';}
   console.warn('CivicConnect GPS error',e);
 },{enableHighAccuracy:true,timeout:30000,maximumAge:0});
}
function startWatch(){if(!navigator.geolocation||watchId!==null)return;watchId=navigator.geolocation.watchPosition(p=>update(p.coords.latitude,p.coords.longitude,p.coords.accuracy),e=>console.warn('GPS watch error',e),{enableHighAccuracy:true,maximumAge:5000,timeout:30000});}
function initMap(){const el=$('gpsMap');if(!el||!window.L)return;try{map=L.map(el).setView([20.5937,78.9629],5);L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap contributors'}).addTo(map);}catch(e){console.warn('Map initialization failed',e);}}
window.CivicGPS={locate,startWatch,initMap};
document.addEventListener('DOMContentLoaded',function(){initMap();const b=$('useMyLocation');if(b){b.addEventListener('click',function(ev){ev.preventDefault();locate();});}});
})();
