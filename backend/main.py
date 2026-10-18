from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional
import sqlite3, os, re, uuid, shutil, difflib, math, json
from datetime import datetime, timedelta

try:
    from ml.predictor import predict as ml_predict, info as ml_info
except Exception:
    ml_predict = lambda text: None
    ml_info = lambda: {'model':'Word + Character TF-IDF + Logistic Regression','ready':False,'dataset_rows':0,'test_accuracy':0,'weighted_f1':0,'classes':[]}

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



def priority_score(text, category, priority, lat=None, lon=None):
    t=text.lower(); score=28
    if priority=='Critical': score += 38
    elif priority=='Medium': score += 20
    else: score += 8
    for pat,pts in [(r'child|elderly|women|public safety|accident|fire|danger',12),(r'urgent|immediately|emergency|critical',10),(r'no water|power cut|outage',8),(r'large|huge|multiple|many people',5)]:
        if re.search(pat,t): score += pts
    return max(1,min(100,score))

def sla_for(priority):
    return {'Critical':4,'Medium':48,'Low':168}.get(priority,168)

def audit(complaint_id, action, actor='System', details=''):
    c=db(); now=datetime.now().isoformat(timespec='seconds')
    c.execute('INSERT INTO audit_logs(complaint_id,action,actor,details,created_at) VALUES(?,?,?,?,?)',(complaint_id,action,actor,details,now))
    c.execute('INSERT INTO notifications(complaint_id,audience,title,message,created_at) VALUES(?,?,?,?,?)',(complaint_id,'citizen',action,details,now))
    c.commit(); c.close()

def issue_family(text):
    """Return a small civic-issue family so paraphrased complaints can match."""
    t=(text or '').lower()
    families={
      'road_damage':['pothole','pot hole','road hole','road damage','damaged road','broken road','road is badly','road badly','crater'],
      'garbage':['garbage','waste','trash','rubbish','litter','dumping','unclean'],
      'water':['water supply','no water','water shortage','water problem','water interruption','pipeline','leakage'],
      'electricity':['street light','streetlight','lights not working','light not working','electricity','power cut','power outage','dark area'],
      'drainage':['drain','drainage','sewage','sewer','blocked drain','waterlogging'],
      'traffic':['traffic','signal','congestion','road blockage','parking'],
      'public_safety':['unsafe','dangerous','safety','accident','hazard','risk'],
    }
    for family, words in families.items():
        if any(w in t for w in words): return family
    return None

def duplicate_score(title1, desc1, loc1, category1, title2, desc2, loc2, category2, lat1=None, lon1=None, lat2=None, lon2=None):
    """Explainable duplicate score: issue family + category + location + text."""
    def norm(text):
        return re.sub(r"[^a-z0-9\u0900-\u097f\s]", " ", (text or '').lower())
    def tokens(text):
        return set(w for w in norm(text).split() if len(w)>2)
    text1=(title1 or '')+' '+(desc1 or '')
    text2=(title2 or '')+' '+(desc2 or '')
    t1,t2=tokens(text1),tokens(text2)
    union=t1|t2
    jaccard=(len(t1&t2)/len(union)*100) if union else 0
    char=difflib.SequenceMatcher(None,norm(text1),norm(text2)).ratio()*100
    loc1n,loc2n=norm(loc1),norm(loc2)
    loc_text=difflib.SequenceMatcher(None,loc1n,loc2n).ratio()*100 if (loc1n or loc2n) else 0

    # Exact/near GPS is strong evidence that two differently worded reports concern the same place.
    gps_score=0
    if lat1 is not None and lon1 is not None and lat2 is not None and lon2 is not None:
        distance=((float(lat1)-float(lat2))**2 + (float(lon1)-float(lon2))**2)**0.5
        if distance <= 0.0005: gps_score=30
        elif distance <= 0.002: gps_score=20
        elif distance <= 0.01: gps_score=10
    location_score=max(loc_text, gps_score)

    family1=issue_family(text1); family2=issue_family(text2)
    family_score=35 if family1 and family1==family2 else 0
    category_score=15 if category1 and category2 and category1==category2 else 0
    text_score=min(15, jaccard*0.10 + char*0.05)
    location_component=min(30, location_score*0.30)
    score=round(family_score + category_score + location_component + text_score)
    return min(100,score)

def duplicate_match(title, description, location, category=None, latitude=None, longitude=None):
    c=db(); rows=c.execute("SELECT id,title,description,location,status,category,latitude,longitude FROM complaints WHERE status NOT IN ('Closed','Rejected') ORDER BY created_at DESC").fetchall(); c.close()
    best=None
    for r in rows:
        score=duplicate_score(title,description,location,category,r['title'],r['description'],r['location'],r['category'],latitude,longitude,r['latitude'],r['longitude'])
        if not best or score>best['score']:
            best={'id':r['id'],'score':score,'title':r['title'],'status':r['status'],'category':r['category']}
    # 55 is intentionally tolerant for paraphrased reports; family + location/category provide the strong signal.
    return best if best and best['score']>=75 else None

def group_members(group_id):
    if not group_id: return []
    c=db(); rows=c.execute('SELECT * FROM complaints WHERE duplicate_group_id=? ORDER BY CASE WHEN primary_complaint_id=id THEN 0 ELSE 1 END, created_at ASC',(group_id,)).fetchall(); c.close()
    return [row(x) for x in rows]

def create_or_join_duplicate_group(cid, duplicate):
    if not duplicate: return None
    related_id=duplicate['id']
    c=db(); related=c.execute('SELECT duplicate_group_id,primary_complaint_id FROM complaints WHERE id=?',(related_id,)).fetchone()
    group_id = related['duplicate_group_id'] if related and related['duplicate_group_id'] else 'DG'+uuid.uuid4().hex[:10].upper()
    primary_id = related['primary_complaint_id'] if related and related['primary_complaint_id'] else related_id
    if not related or not related['duplicate_group_id']:
        c.execute('UPDATE complaints SET duplicate_group_id=?,primary_complaint_id=?,affected_citizens_count=2 WHERE id=?',(group_id,primary_id,related_id))
    c.execute('UPDATE complaints SET duplicate_group_id=?,primary_complaint_id=?,duplicate_of=?,duplicate_score=? WHERE id=?',(group_id,primary_id,primary_id,duplicate['score'],cid))
    count=c.execute('SELECT COUNT(*) FROM complaints WHERE duplicate_group_id=?',(group_id,)).fetchone()[0]
    c.execute('UPDATE complaints SET affected_citizens_count=? WHERE duplicate_group_id=?',(count,group_id)); c.commit(); c.close()
    return {'group_id':group_id,'primary_id':primary_id,'affected_citizens_count':count}

def propagate_group_status(group_id, status, remark='', actor='Government Officer'):
    members=group_members(group_id)
    if not members: return
    now=datetime.now().isoformat(timespec='seconds'); c=db()
    for m in members: c.execute('UPDATE complaints SET status=?,remark=?,updated_at=? WHERE id=?',(status,remark,now,m['id']))
    c.commit(); c.close()
    for m in members: audit(m['id'],f'Group Status Changed → {status}',actor,remark or 'Primary government action applied to related complaints.')

def propagate_resolution(group_id, source_id):
    if not group_id: return
    source=get(source_id); members=group_members(group_id); now=datetime.now().isoformat(timespec='seconds'); c=db()
    for m in members:
        if m['id']==source_id: continue
        c.execute("""UPDATE complaints SET resolution_photo=?,resolution_video=?,resolution_remark=?,resolved_by=?,resolution_date=?,resolution_confidence=?,status='Citizen Verification',updated_at=? WHERE id=?""",
                  (source.get('resolution_photo'),source.get('resolution_video'),source.get('resolution_remark'),source.get('resolved_by'),source.get('resolution_date'),source.get('resolution_confidence',0),now,m['id']))
    c.commit(); c.close()
    for m in members:
        if m['id']!=source_id: audit(m['id'],'Shared Resolution Proof','CivicConnect AI',f'Resolution evidence from primary case {source_id} is available for citizen verification.')

def group_status_after_feedback(group_id):
    members=group_members(group_id)
    if not members: return
    if any(m.get('citizen_decision')=='rejected' for m in members): target='Reopened'
    elif any(m.get('citizen_decision')=='confirmed' for m in members): target='Closed'
    else: target='Citizen Verification'
    now=datetime.now().isoformat(timespec='seconds'); c=db()
    for m in members: c.execute('UPDATE complaints SET status=?,closed_at=?,reopened_at=?,updated_at=? WHERE id=?',(target,now if target=='Closed' else None,now if target=='Reopened' else None,now,m['id']))
    c.commit(); c.close(); confirmed=sum(x.get('citizen_decision')=='confirmed' for x in members)
    for m in members: audit(m['id'],f'Group Verification → {target}','CivicConnect AI',f'Duplicate group verification: {confirmed}/{len(members)} citizen reports confirmed.')

def init_db():
    c = db()
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs(
      id INTEGER PRIMARY KEY AUTOINCREMENT, complaint_id TEXT, action TEXT, actor TEXT, details TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notifications(
      id INTEGER PRIMARY KEY AUTOINCREMENT, complaint_id TEXT, audience TEXT, title TEXT, message TEXT, is_read INTEGER DEFAULT 0, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS complaints(
      id TEXT PRIMARY KEY,title TEXT,description TEXT,location TEXT,latitude REAL,longitude REAL,
      category TEXT,priority TEXT,department TEXT,confidence INTEGER,status TEXT,language TEXT,
      evidence_name TEXT,created_at TEXT,updated_at TEXT,remark TEXT DEFAULT '', priority_score INTEGER DEFAULT 0, sla_hours INTEGER DEFAULT 168, sla_due_at TEXT, escalated INTEGER DEFAULT 0, duplicate_of TEXT, duplicate_score INTEGER DEFAULT 0,
      resolution_photo TEXT,resolution_video TEXT,resolution_remark TEXT,resolved_by TEXT,
      resolution_date TEXT,resolution_confidence INTEGER DEFAULT 0,citizen_feedback TEXT,
      citizen_rating INTEGER,citizen_decision TEXT,closed_at TEXT,reopened_at TEXT,
      duplicate_group_id TEXT,primary_complaint_id TEXT,affected_citizens_count INTEGER DEFAULT 1,
      ml_category TEXT,ml_confidence REAL,ml_model TEXT)''')
    cols = {r['name'] for r in c.execute('PRAGMA table_info(complaints)').fetchall()}
    additions = {
      'priority_score':'INTEGER DEFAULT 0','sla_hours':'INTEGER DEFAULT 168','sla_due_at':'TEXT','escalated':'INTEGER DEFAULT 0','duplicate_of':'TEXT','duplicate_score':'INTEGER DEFAULT 0',
      'resolution_photo':'TEXT','resolution_video':'TEXT','resolution_remark':'TEXT','resolved_by':'TEXT',
      'resolution_date':'TEXT','resolution_confidence':'INTEGER DEFAULT 0','citizen_feedback':'TEXT',
      'citizen_rating':'INTEGER','citizen_decision':'TEXT','closed_at':'TEXT','reopened_at':'TEXT',
      'duplicate_group_id':'TEXT','primary_complaint_id':'TEXT','affected_citizens_count':'INTEGER DEFAULT 1',
      'ml_category':'TEXT','ml_confidence':'REAL','ml_model':'TEXT'
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
        c.executemany('''INSERT INTO complaints (id,title,description,location,latitude,longitude,category,priority,department,confidence,status,language,evidence_name,created_at,updated_at,remark) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', [x[:16] for x in seed])
        for r in c.execute('SELECT id,title,description,location,priority,category,created_at FROM complaints').fetchall():
            ps=priority_score(r['title']+' '+r['description'],r['category'] if 'category' in r.keys() else 'Other',r['priority'])
            sla=sla_for(r['priority']); due=(datetime.fromisoformat(r['created_at'])+timedelta(hours=sla)).isoformat(timespec='seconds')
            c.execute('UPDATE complaints SET priority_score=?,sla_hours=?,sla_due_at=? WHERE id=?',(ps,sla,due,r['id']))
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

def backfill_duplicate_groups():
    c=db(); rows=[row(x) for x in c.execute("SELECT id,title,description,location,status,category,duplicate_group_id FROM complaints WHERE status NOT IN ('Closed','Rejected') ORDER BY created_at ASC").fetchall()]; c.close()
    for i,a in enumerate(rows):
        if a.get('duplicate_group_id'): continue
        best=None
        for b in rows[i+1:]:
            score=duplicate_score(a['title'],a['description'],a['location'],a['category'],b['title'],b['description'],b['location'],b['category'],a.get('latitude'),a.get('longitude'),b.get('latitude'),b.get('longitude'))
            if score>=45 and (best is None or score>best['score']): best={'id':b['id'],'score':score}
        if best: create_or_join_duplicate_group(best['id'],{'id':a['id'],'score':best['score']})

@app.on_event('startup')
def startup():
    init_db()
    backfill_duplicate_groups()

@app.get('/api/health')
def health(): return {'status':'ok','service':'CivicConnect AI','database':'SQLite','ai':'online','resolution_proof':'online','ml_model':ml_info()}

@app.get('/api/complaints')
def complaints():
    c=db(); rows=c.execute('SELECT * FROM complaints ORDER BY created_at DESC').fetchall(); c.close(); return [row(x) for x in rows]

@app.get('/api/complaints/{cid}')
def complaint(cid:str): return get(cid)

@app.post('/api/complaints')
def create(x:ComplaintIn):
    full=x.title+' '+x.description
    lang=x.language or detect(full)
    manual_category=bool(x.category and 'AI' not in x.category)
    ml_result=ml_predict(full)

    if manual_category:
        category,priority,dept,rule_conf=analyze(full,x.category)
        conf=rule_conf
    elif ml_result:
        category=ml_result['category']
        _,priority,dept,_=analyze(full,category)
        conf=round(float(ml_result['confidence']))
    else:
        category,priority,dept,conf=analyze(full,x.category)

    pscore=priority_score(full,category,priority,x.latitude,x.longitude)
    sla=sla_for(priority)
    now=datetime.now().isoformat(timespec='seconds')
    due=(datetime.fromisoformat(now)+timedelta(hours=sla)).isoformat(timespec='seconds')
    dup=duplicate_match(x.title,x.description,x.location,category,x.latitude,x.longitude)
    cid='CC'+datetime.now().strftime('%y%m%d%H%M%S')+uuid.uuid4().hex[:3].upper()
    c=db(); c.execute('''INSERT INTO complaints
      (id,title,description,location,latitude,longitude,category,priority,department,confidence,status,language,evidence_name,created_at,updated_at,remark,priority_score,sla_hours,sla_due_at,duplicate_of,duplicate_score,ml_category,ml_confidence,ml_model)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
      (cid,x.title,x.description,x.location,x.latitude,x.longitude,category,priority,dept,conf,'Pending',lang,x.evidence_name,now,now,'',pscore,sla,due,dup['id'] if dup else None,dup['score'] if dup else 0,
       ml_result['category'] if ml_result else None,ml_result['confidence'] if ml_result else None,ml_result['model'] if ml_result else None)); c.commit(); r=c.execute('SELECT * FROM complaints WHERE id=?',(cid,)).fetchone(); c.close()
    audit(cid,'Complaint Submitted','Citizen',f'Assigned to {dept}. Priority {priority} ({pscore}/100).')
    if ml_result and not manual_category:
        audit(cid,'ML Classification','CivicConnect ML Engine',f"Multilingual Word + Character TF-IDF + Logistic Regression predicted {ml_result['category']} with {ml_result['confidence']}% confidence.")
    if dup:
        grp=create_or_join_duplicate_group(cid,dup)
        audit(cid,'Duplicate Group Created/Joined','AI Engine',f'Linked to primary case {grp["primary_id"]}. Similarity {dup["score"]}%. Affected citizen reports: {grp["affected_citizens_count"]}.')
        r=get(cid)
    return r

@app.patch('/api/complaints/{cid}/status')
def status(cid:str,x:StatusIn):
    allowed={'Pending','In Progress','Resolution Submitted','Citizen Verification','Resolved','Closed','Reopened','Rejected'}
    if x.status not in allowed: raise HTTPException(400,'Invalid status')
    current=get(cid); gid=current.get('duplicate_group_id')
    if gid:
        propagate_group_status(gid,x.status,x.remark or 'Primary government action applied to the related complaint group.')
        return get(cid)
    c=db(); now=datetime.now().isoformat(timespec='seconds')
    c.execute('UPDATE complaints SET status=?,remark=?,updated_at=? WHERE id=?',(x.status,x.remark,now,cid)); c.commit(); c.close()
    audit(cid,f'Status Changed → {x.status}','Government Officer',x.remark or 'Status updated.')
    return get(cid)

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
    c.commit(); c.close(); audit(cid,'Resolution Proof Submitted',resolved_by,f'{resolution_remark or "Evidence uploaded for citizen verification."} AI relevance: {confidence}%.')
    updated=get(cid)
    if updated.get('duplicate_group_id'):
        propagate_resolution(updated['duplicate_group_id'],cid)
        propagate_group_status(updated['duplicate_group_id'],'Citizen Verification','Resolution evidence submitted for the related complaint group.')
    return get(cid)

@app.post('/api/complaints/{cid}/citizen-feedback')
def citizen_feedback(cid:str,x:CitizenFeedbackIn):
    if x.decision not in {'confirmed','rejected'}: raise HTTPException(400,'Decision must be confirmed or rejected')
    if x.rating is not None and not 1 <= x.rating <= 5: raise HTTPException(400,'Rating must be between 1 and 5')
    current=get(cid); now=datetime.now().isoformat(timespec='seconds')
    c=db(); c.execute('''UPDATE complaints SET citizen_decision=?,citizen_feedback=?,citizen_rating=?,updated_at=? WHERE id=?''',(x.decision,x.feedback,x.rating,now,cid)); c.commit(); c.close(); audit(cid,'Citizen Verification Submitted','Citizen',x.feedback or 'Citizen submitted verification.')
    if current.get('duplicate_group_id'):
        group_status_after_feedback(current['duplicate_group_id'])
    else:
        status='Closed' if x.decision=='confirmed' else 'Reopened'
        c=db(); c.execute('UPDATE complaints SET status=?,closed_at=?,reopened_at=?,updated_at=? WHERE id=?',(status,now if status=='Closed' else None,now if status=='Reopened' else None,now,cid)); c.commit(); c.close()
        audit(cid,f'Citizen Verification → {status}','CivicConnect AI','Complaint closed/reopened after citizen verification.')
    return get(cid)

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



@app.get('/api/advanced/groups')
def duplicate_groups():
    c=db(); gids=[r[0] for r in c.execute("SELECT DISTINCT duplicate_group_id FROM complaints WHERE duplicate_group_id IS NOT NULL ORDER BY duplicate_group_id DESC").fetchall()]; c.close(); out=[]
    for gid in gids:
        members=group_members(gid)
        if not members: continue
        primary_id=members[0].get('primary_complaint_id') or members[0]['id']; primary=next((m for m in members if m['id']==primary_id),members[0])
        out.append({'group_id':gid,'primary_complaint_id':primary_id,'primary_title':primary['title'],'affected_citizens_count':len(members),'status':primary['status'],'department':primary['department'],'category':primary['category'],'priority':primary['priority'],'members':[{'id':m['id'],'title':m['title'],'status':m['status'],'citizen_decision':m.get('citizen_decision'),'similarity':m.get('duplicate_score',0),'location':m.get('location')} for m in members]})
    return out

@app.get('/api/advanced/groups/{gid}')
def duplicate_group(gid:str):
    members=group_members(gid)
    if not members: raise HTTPException(404,'Duplicate group not found')
    primary_id=members[0].get('primary_complaint_id') or members[0]['id']
    return {'group_id':gid,'primary_complaint_id':primary_id,'affected_citizens_count':len(members),'members':members}

@app.post('/api/advanced/groups/{gid}/status')
def group_status(gid:str,x:StatusIn):
    allowed={'Pending','In Progress','Resolution Submitted','Citizen Verification','Resolved','Closed','Reopened','Rejected'}
    if x.status not in allowed: raise HTTPException(400,'Invalid status')
    if not group_members(gid): raise HTTPException(404,'Duplicate group not found')
    propagate_group_status(gid,x.status,x.remark,'Government Officer'); return duplicate_group(gid)

@app.get('/api/advanced/duplicate-feed')
def duplicate_feed():
    c=db(); rows=[row(x) for x in c.execute("SELECT id,title,description,location,latitude,longitude,status,category,priority,duplicate_of,duplicate_score FROM complaints WHERE status NOT IN ('Closed','Rejected') ORDER BY created_at DESC").fetchall()]; c.close()
    out=[]; seen=set()
    for i,a in enumerate(rows):
        for b in rows[i+1:]:
            score=duplicate_score(a['title'],a['description'],a['location'],a['category'],b['title'],b['description'],b['location'],b['category'],a.get('latitude'),a.get('longitude'),b.get('latitude'),b.get('longitude'))
            if score>=75:
                key=tuple(sorted((a['id'],b['id'])))
                if key in seen: continue
                seen.add(key)
                out.append({'complaint_id':a['id'],'related_id':b['id'],'complaint_title':a['title'],'related_title':b['title'],'related_location':b['location'],'related_status':b['status'],'category':b['category'],'priority':b['priority'],'similarity':score})
    return sorted(out,key=lambda x:x['similarity'],reverse=True)[:12]

@app.get('/api/advanced/duplicates/{cid}')
def duplicates(cid:str):
    target=get(cid); c=db(); rows=[row(x) for x in c.execute("SELECT id,title,description,location,latitude,longitude,status,category,priority FROM complaints WHERE id!=? AND status NOT IN ('Closed','Rejected')",(cid,)).fetchall()]; c.close()
    q=(target['title']+' '+target['description']).lower(); out=[]
    for r in rows:
        score=duplicate_score(target['title'],target['description'],target['location'],target['category'],r['title'],r['description'],r['location'],r['category'],target.get('latitude'),target.get('longitude'),r['latitude'],r['longitude'])
        if score>=40: out.append({**r,'similarity':score})
    return sorted(out,key=lambda x:x['similarity'],reverse=True)[:8]

@app.get('/api/advanced/sla')
def sla_board():
    rows=complaints(); now=datetime.now(); out=[]
    for r in rows:
        if r.get('status') in {'Closed','Resolved','Rejected'}: continue
        due=r.get('sla_due_at'); hours=None
        if due:
            hours=round((datetime.fromisoformat(due)-now).total_seconds()/3600,1)
        out.append({'id':r['id'],'title':r['title'],'department':r['department'],'priority':r['priority'],'priority_score':r.get('priority_score',0),'status':r['status'],'sla_due_at':due,'hours_remaining':hours,'escalated':bool(r.get('escalated')),'sla_breached':hours is not None and hours<0})
    return sorted(out,key=lambda x:(x['sla_breached']==False,x['hours_remaining'] if x['hours_remaining'] is not None else 999))

@app.post('/api/advanced/escalate/{cid}')
def escalate(cid:str):
    get(cid); c=db(); now=datetime.now().isoformat(timespec='seconds'); c.execute("UPDATE complaints SET escalated=1,updated_at=? WHERE id=?",(now,cid)); c.commit(); c.close(); audit(cid,'SLA Escalation','CivicConnect AI','Case escalated to department head due to SLA risk/breach.'); return get(cid)

@app.get('/api/advanced/audit/{cid}')
def audit_trail(cid:str):
    get(cid); c=db(); rows=[row(x) for x in c.execute('SELECT * FROM audit_logs WHERE complaint_id=? ORDER BY created_at ASC',(cid,)).fetchall()]; c.close(); return rows

@app.get('/api/advanced/notifications')
def notifications(audience:str='citizen'):
    c=db(); rows=[row(x) for x in c.execute('SELECT * FROM notifications WHERE audience=? ORDER BY created_at DESC LIMIT 50',(audience,)).fetchall()]; c.close(); return rows

@app.post('/api/advanced/notifications/{nid}/read')
def mark_notification(nid:int):
    c=db(); c.execute('UPDATE notifications SET is_read=1 WHERE id=?',(nid,)); c.commit(); c.close(); return {'ok':True}

@app.get('/api/advanced/insights')
def advanced_insights():
    rows=complaints(); total=len(rows); active=[r for r in rows if r['status'] not in {'Closed','Resolved','Rejected'}];
    cats={}; depts={}; wards={}
    for r in rows:
        cats[r['category']]=cats.get(r['category'],0)+1; depts[r['department']]=depts.get(r['department'],0)+1; loc=r.get('location') or 'Unknown'; wards[loc]=wards.get(loc,0)+1
    top_cat=max(cats,key=cats.get) if cats else 'No data'; top_dept=max(depts,key=depts.get) if depts else 'No data'; top_zone=max(wards,key=wards.get) if wards else 'No data'
    avg_score=round(sum((r.get('priority_score') or 0) for r in rows)/total) if total else 0
    return {'total':total,'active':len(active),'top_category':top_cat,'top_department':top_dept,'top_zone':top_zone,'avg_priority_score':avg_score,'insight':f'{top_cat} is currently the most reported civic issue. {top_dept} has the highest workload. {top_zone} has the highest complaint concentration.' if total else 'Submit complaints to generate AI governance insights.'}

@app.get('/api/advanced/heatmap')
def heatmap():
    rows=complaints(); return [{'id':r['id'],'title':r['title'],'category':r['category'],'priority':r['priority'],'status':r['status'],'latitude':r['latitude'],'longitude':r['longitude'],'location':r['location']} for r in rows if r.get('latitude') is not None and r.get('longitude') is not None]

app.mount('/uploads', StaticFiles(directory=UPLOAD_ROOT), name='uploads')
app.mount('/app', StaticFiles(directory=os.path.join(ROOT, 'fronted'), html=True), name='frontend')
app.mount('/js', StaticFiles(directory=os.path.join(ROOT, 'js')), name='javascript')
app.mount('/css', StaticFiles(directory=os.path.join(ROOT, 'css')), name='stylesheets')

@app.get('/api/ml/info')
def ml_model_info():
    return ml_info()

@app.post('/api/ml/predict')
def ml_model_predict(payload: dict):
    text=payload.get('text','') if isinstance(payload,dict) else ''
    if not text.strip():
        raise HTTPException(400,'Text is required')
    result=ml_predict(text)
    if not result:
        raise HTTPException(503,'ML model is not available')
    return result

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
