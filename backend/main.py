from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional
import sqlite3, os, re, uuid, shutil
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(os.path.dirname(__file__), 'civicconnect.db')
UPLOAD_ROOT = os.path.join(ROOT, 'uploads')
RESOLUTION_DIR = os.path.join(UPLOAD_ROOT, 'resolution_evidence')
COMPLAINT_DIR = os.path.join(UPLOAD_ROOT, 'complaint_evidence')
os.makedirs(RESOLUTION_DIR, exist_ok=True)
os.makedirs(COMPLAINT_DIR, exist_ok=True)

app = FastAPI(title='CivicConnect AI API', version='3.0.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

ALLOWED_RESOLUTION = {'.jpg', '.jpeg', '.png', '.webp', '.mp4', '.mov'}
MAX_UPLOAD = 15 * 1024 * 1024

class ComplaintIn(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=5)
    location: str = Field(min_length=2)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category: Optional[str] = None
    language: Optional[str] = None
    evidence_name: Optional[str] = None

class StatusIn(BaseModel):
    status: str
    remark: Optional[str] = ''

class CitizenFeedbackIn(BaseModel):
    decision: str
    feedback: Optional[str] = ''
    rating: Optional[int] = None


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    c = db()
    c.execute('''CREATE TABLE IF NOT EXISTS complaints(
      id TEXT PRIMARY KEY,title TEXT,description TEXT,location TEXT,latitude REAL,longitude REAL,
      category TEXT,priority TEXT,department TEXT,confidence INTEGER,status TEXT,language TEXT,
      evidence_name TEXT,created_at TEXT,updated_at TEXT,remark TEXT DEFAULT '',
      resolution_photo TEXT,resolution_video TEXT,resolution_remark TEXT,resolved_by TEXT,
      resolution_date TEXT,resolution_confidence INTEGER DEFAULT 0,citizen_feedback TEXT,
      citizen_rating INTEGER,citizen_decision TEXT,closed_at TEXT,reopened_at TEXT)''')
    cols = {r['name'] for r in c.execute('PRAGMA table_info(complaints)').fetchall()}
    additions = {
      'resolution_photo':'TEXT','resolution_video':'TEXT','resolution_remark':'TEXT','resolved_by':'TEXT',
      'resolution_date':'TEXT','resolution_confidence':'INTEGER DEFAULT 0','citizen_feedback':'TEXT',
      'citizen_rating':'INTEGER','citizen_decision':'TEXT','closed_at':'TEXT','reopened_at':'TEXT'
    }
    for name, typ in additions.items():
        if name not in cols: c.execute(f'ALTER TABLE complaints ADD COLUMN {name} {typ}')
    if c.execute('SELECT COUNT(*) FROM complaints').fetchone()[0] == 0:
        seed = [
          ('CC1028','Road damage near main junction','Large potholes are causing traffic and safety problems.','Central Market Road',20.5937,78.9629,'Infrastructure','Critical','Public Works',94,'In Progress','English',None,'2026-09-05 10:30','2026-09-05 10:30','',None,None,None,None,None,0,None,None,None,None,None),
          ('CC1027','Garbage collection delayed','Garbage has not been collected for two days.','Ward 12',20.595,78.965,'Sanitation','Medium','Sanitation',91,'Resolved','English',None,'2026-09-03 09:20','2026-09-03 09:20','',None,None,None,None,None,0,'Collection completed',4,'confirmed','2026-09-04 15:00',None),
          ('CC1026','Street lights not working','Street lights are not working on Station Road.','Station Road',20.59,78.96,'Electricity','Low','Electricity',89,'Pending','English',None,'2026-09-02 18:10','2026-09-02 18:10','',None,None,None,None,None,0,None,None,None,None,None),
          ('CC1025','Water supply interruption','No water supply since morning in the residential area.','Shivaji Nagar',20.587,78.958,'Water Supply','Critical','Water Department',96,'In Progress','English',None,'2026-09-01 08:45','2026-09-01 08:45','',None,None,None,None,None,0,None,None,None,None,None)
        ]
        c.executemany('INSERT INTO complaints VALUES('+','.join(['?']*27)+')', seed)
    c.commit(); c.close()


def analyze(text, selected=None):
    t=text.lower(); category=selected if selected and 'AI' not in selected else None
    rules=[('Infrastructure',r'pothole|road|street|footpath|bridge|traffic|drainage'),('Water Supply',r'water|leak|pipe|supply'),('Electricity',r'light|electric|power|streetlight|transformer'),('Sanitation',r'garbage|waste|trash|drain|clean'),('Public Safety',r'crime|unsafe|accident|fire|danger|harassment')]
    aliases={'Roads & Infrastructure':'Infrastructure','Roads':'Infrastructure','Water':'Water Supply'}
    category=aliases.get(category,category) if category else category
    if not category: category=next((x for x,p in rules if re.search(p,t)), 'Other')
    priority='Low'
    if re.search(r'emergency|urgent|danger|accident|fire|critical|no water',t): priority='Critical'
    elif re.search(r'broken|damage|leak|garbage|not working|blocked',t): priority='Medium'
    dept={'Infrastructure':'Public Works','Water Supply':'Water Department','Electricity':'Electricity','Sanitation':'Sanitation','Public Safety':'Public Safety'}.get(category,'Municipal Corporation')
    confidence=min(98,84+min(13,len(text)//35))
    return category,priority,dept,confidence


def detect(text): return 'Hindi / Marathi' if re.search(r'[\u0900-\u097F]',text) else 'English'

def row(r): return dict(r)

def get(cid):
    c=db(); r=c.execute('SELECT * FROM complaints WHERE id=?',(cid,)).fetchone(); c.close()
    if not r: raise HTTPException(404,'Complaint not found')
    return row(r)

@app.on_event('startup')
def startup(): init_db()

@app.get('/api/health')
def health(): return {'status':'ok','service':'CivicConnect AI','database':'SQLite','ai':'online','resolution_proof':'online'}

@app.get('/api/complaints')
def complaints():
    c=db(); rows=c.execute('SELECT * FROM complaints ORDER BY created_at DESC').fetchall(); c.close(); return [row(x) for x in rows]

@app.get('/api/complaints/{cid}')
def complaint(cid:str): return get(cid)

@app.post('/api/complaints')
def create(x:ComplaintIn):
    category,priority,dept,conf=analyze(x.title+' '+x.description,x.category)
    lang=x.language or detect(x.title+' '+x.description)
    cid='CC'+datetime.now().strftime('%y%m%d%H%M%S')+uuid.uuid4().hex[:3].upper()
    now=datetime.now().isoformat(timespec='seconds')
    c=db(); c.execute('''INSERT INTO complaints
      (id,title,description,location,latitude,longitude,category,priority,department,confidence,status,language,evidence_name,created_at,updated_at,remark)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
      (cid,x.title,x.description,x.location,x.latitude,x.longitude,category,priority,dept,conf,'Pending',lang,x.evidence_name,now,now,'')); c.commit(); r=c.execute('SELECT * FROM complaints WHERE id=?',(cid,)).fetchone(); c.close(); return row(r)

@app.patch('/api/complaints/{cid}/status')
def status(cid:str,x:StatusIn):
    allowed={'Pending','In Progress','Resolution Submitted','Citizen Verification','Resolved','Closed','Reopened','Rejected'}
    if x.status not in allowed: raise HTTPException(400,'Invalid status')
    c=db(); now=datetime.now().isoformat(timespec='seconds')
    c.execute('UPDATE complaints SET status=?,remark=?,updated_at=? WHERE id=?',(x.status,x.remark,now,cid)); c.commit(); c.close(); return get(cid)

@app.post('/api/complaints/{cid}/resolution')
async def resolution(cid:str, resolution_file: UploadFile = File(...), resolution_remark: str = Form(''), resolved_by: str = Form('Government Officer')):
    get(cid)
    original = resolution_file.filename or ''
    ext = os.path.splitext(original)[1].lower()
    if ext not in ALLOWED_RESOLUTION: raise HTTPException(400,'Unsupported evidence type. Use JPG, PNG, WEBP, MP4 or MOV.')
    data = await resolution_file.read()
    if len(data) > MAX_UPLOAD: raise HTTPException(400,'File is larger than 15 MB.')
    safe = f'{cid}_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{uuid.uuid4().hex[:8]}{ext}'
    path = os.path.join(RESOLUTION_DIR,safe)
    with open(path,'wb') as f: f.write(data)
    confidence = 92 if ext in {'.jpg','.jpeg','.png','.webp'} else 86
    now=datetime.now().isoformat(timespec='seconds')
    c=db()
    if ext in {'.mp4','.mov'}:
        c.execute('''UPDATE complaints SET resolution_video=?,resolution_photo=NULL,resolution_remark=?,resolved_by=?,resolution_date=?,resolution_confidence=?,status='Citizen Verification',updated_at=? WHERE id=?''',
                  (f'/uploads/resolution_evidence/{safe}',resolution_remark,resolved_by,now,confidence,now,cid))
    else:
        c.execute('''UPDATE complaints SET resolution_photo=?,resolution_video=NULL,resolution_remark=?,resolved_by=?,resolution_date=?,resolution_confidence=?,status='Citizen Verification',updated_at=? WHERE id=?''',
                  (f'/uploads/resolution_evidence/{safe}',resolution_remark,resolved_by,now,confidence,now,cid))
    c.commit(); c.close(); return get(cid)

@app.post('/api/complaints/{cid}/citizen-feedback')
def citizen_feedback(cid:str,x:CitizenFeedbackIn):
    if x.decision not in {'confirmed','rejected'}: raise HTTPException(400,'Decision must be confirmed or rejected')
    if x.rating is not None and not 1 <= x.rating <= 5: raise HTTPException(400,'Rating must be between 1 and 5')
    get(cid); now=datetime.now().isoformat(timespec='seconds'); status='Closed' if x.decision=='confirmed' else 'Reopened'
    c=db(); c.execute('''UPDATE complaints SET citizen_decision=?,citizen_feedback=?,citizen_rating=?,status=?,closed_at=?,reopened_at=?,updated_at=? WHERE id=?''',
      (x.decision,x.feedback,x.rating,status,now if status=='Closed' else None,now if status=='Reopened' else None,now,cid)); c.commit(); c.close(); return get(cid)

@app.get('/api/analytics')
def analytics():
    c=db(); rows=[row(x) for x in c.execute('SELECT * FROM complaints')]; c.close()
    total=len(rows); closed=sum(x['status']=='Closed' for x in rows); resolved=sum(x['status'] in {'Resolved','Closed'} for x in rows); critical=sum(x['priority']=='Critical' for x in rows); proof=sum(bool(x['resolution_photo'] or x['resolution_video']) for x in rows); confirmed=sum(x['citizen_decision']=='confirmed' for x in rows); reopened=sum(x['status']=='Reopened' for x in rows)
    def count(k):
        d={}
        for x in rows:d[x[k]]=d.get(x[k],0)+1
        return d
    ratings=[x['citizen_rating'] for x in rows if x['citizen_rating']]
    return {'total':total,'resolved':resolved,'closed':closed,'pending':sum(x['status']=='Pending' for x in rows),'critical':critical,'resolution_rate':round(resolved/total*100,1) if total else 0,'proof_submitted':proof,'citizen_confirmed':confirmed,'reopened':reopened,'avg_rating':round(sum(ratings)/len(ratings),1) if ratings else 0,'categories':count('category'),'priorities':count('priority'),'departments':count('department')}

app.mount('/uploads', StaticFiles(directory=UPLOAD_ROOT), name='uploads')
app.mount('/app', StaticFiles(directory=os.path.join(ROOT, 'fronted'), html=True), name='frontend')
app.mount('/js', StaticFiles(directory=os.path.join(ROOT, 'js')), name='javascript')
app.mount('/css', StaticFiles(directory=os.path.join(ROOT, 'css')), name='stylesheets')

@app.get('/')
def root(): return RedirectResponse('/app/index.html')


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


def _chat_complaint_id(text: str):
    m = re.search(r'\bCC[A-Z0-9]{4,}\b', text.upper())
    return m.group(0) if m else None


def _chat_live_complaint(cid: str):
    c = db()
    row = c.execute('SELECT * FROM complaints WHERE id=?', (cid,)).fetchone()
    c.close()
    return dict(row) if row else None


def _chat_response(message: str):
    q = message.strip()
    low = q.lower()
    cid = _chat_complaint_id(q)

    # Live complaint lookup takes priority over generic wording.
    if cid:
        complaint = _chat_live_complaint(cid)
        if not complaint:
            return {"intent":"complaint_lookup","complaint_id":cid,
                    "response":f"I checked the live CivicConnect database, but complaint {cid} was not found. Please verify the complaint ID."}
        if any(k in low for k in ["resolution","proof","photo","evidence","solved", "fixed"]):
            if complaint.get("resolution_photo") or complaint.get("resolution_video"):
                officer = complaint.get("resolved_by") or "Government officer"
                remark = complaint.get("resolution_remark") or "Resolution evidence has been submitted."
                return {"intent":"resolution","complaint_id":cid,
                        "response":f"Complaint {cid} has resolution proof submitted by {officer}. Status: {complaint.get('status','Unknown')}. {remark} Citizen verification is available on the Tracking page."}
            return {"intent":"resolution","complaint_id":cid,
                    "response":f"Complaint {cid} does not have resolution proof uploaded yet. Current status: {complaint.get('status','Unknown')}. The authority must submit evidence before you can verify the resolution."}
        if any(k in low for k in ["reopen","reject","not resolved","not fixed"]):
            return {"intent":"reopen","complaint_id":cid,
                    "response":f"You can reopen complaint {cid} from the Tracking page if the issue is not actually resolved. The citizen decision is recorded in the live system."}
        return {"intent":"status","complaint_id":cid,
                "response":f"Live status for {cid}: {complaint.get('status','Unknown')}. Department: {complaint.get('department','Not assigned')}. Category: {complaint.get('category','Other')}. Priority: {complaint.get('priority','Low')}. Location: {complaint.get('location','Not provided')}."}

    if any(k in low for k in ["street light","streetlight","street lights","electricity","power cut"]):
        return {"intent":"department","response":"Street-light and electricity-related complaints are routed to the Electricity department."}
    if any(k in low for k in ["pothole","road","garbage","waste","water leak","water supply","drain","sewer","fire","accident"]):
        category = "Infrastructure / Public Works"
        dept = "Public Works"
        if any(k in low for k in ["garbage","waste"]): category,dept="Sanitation","Sanitation"
        elif any(k in low for k in ["water","leak"]): category,dept="Water Supply","Water Department"
        elif any(k in low for k in ["fire","accident"]): category,dept="Public Safety","Public Safety"
        return {"intent":"issue_guidance","response":f"This sounds like a {category} issue. Recommended department: {dept}. You can submit it through Report Issue; CivicConnect will run AI classification and priority detection before routing it."}
    if any(k in low for k in ["analytics","how many","complaints today","total complaints","statistics"]):
        c=db()
        total=c.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
        resolved=c.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('Resolved','Closed')").fetchone()[0]
        critical=c.execute("SELECT COUNT(*) FROM complaints WHERE priority='Critical'").fetchone()[0]
        c.close()
        return {"intent":"analytics","response":f"Live CivicConnect data: {total} total complaints, {resolved} resolved/closed, and {critical} critical-priority cases."}
    if any(k in low for k in ["hello","hi","hey","namaste","नमस्ते","हाय"]):
        return {"intent":"greeting","response":"Hello! I can work with live CivicConnect data. Ask me to track a complaint, check resolution proof, find a department, or describe your civic issue."}
    return {"intent":"general","response":"I’m connected to CivicConnect’s live complaint system. Tell me what you need—for example, give a complaint ID like CC1028, ask which department handles an issue, or describe the civic problem you want to report."}


@app.post('/api/chat')
def chat(req: ChatRequest):
    return _chat_response(req.message)
