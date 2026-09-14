# CivicConnect AI — Multilingual Citizen Complaint & Governance CRM

**Your Voice. Our Action.**

CivicConnect AI is a government-tech grievance management platform that lets citizens report civic problems in English, Hindi, or Marathi, captures GPS location, uses AI-assisted complaint analysis for category/priority/department routing, and provides transparent complaint tracking.

## Faculty-Suggested Upgrade: Resolution Proof & Citizen Verification

The project now follows a complete accountability loop:

```text
Citizen Complaint
      ↓
Language + AI Analysis
      ↓
Category + Priority + Department
      ↓
Government Officer Works on Issue
      ↓
Officer Uploads Resolution Photo / Video
      ↓
AI-Assisted Evidence Relevance Check
      ↓
Citizen Verification
   ↙             ↘
CONFIRM          REJECT
   ↓               ↓
CLOSED          REOPENED
```

### Resolution Proof Center

Government administrators can load a complaint from the **Administration** page and:
- update case status
- enter a resolution remark
- enter the responsible officer/authority
- upload a JPG/PNG/WEBP photo or MP4/MOV video
- submit proof after completing the work
- send the case to **Citizen Verification**

### Citizen Verification

On the **Tracking** page the citizen can see the government resolution evidence, resolution remark, officer, submission time, and evidence relevance score. The citizen can then:
- confirm that the issue is resolved → **Closed**
- reject the resolution → **Reopened**
- provide feedback and an optional 1–5 rating

## Existing Features Preserved

- Premium government-tech dashboard
- Multilingual complaint submission
- Hindi/Marathi/English language detection
- AI-assisted category classification
- AI-assisted priority detection
- Department recommendation
- GPS capture using browser geolocation
- Leaflet + OpenStreetMap complaint map
- Complaint list and filtering
- Citizen complaint tracking timeline
- Government Administration workspace
- Analytics 2.0 dashboard
- Resolution rate, critical cases, department workload and citizen verification metrics
- SQLite database for zero-setup local demonstration
- FastAPI REST backend
- Responsive HTML/CSS/JavaScript frontend

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Backend | Python, FastAPI |
| Database | SQLite |
| AI/NLP | Rule-based AI-assisted classification, priority detection and language detection |
| Maps | Leaflet + OpenStreetMap |
| Location | Browser Geolocation API |
| Evidence | FastAPI multipart upload + local file storage |
| Charts | Chart.js |
| Icons | Font Awesome |

## Project Structure

```text
CivicConnect-AI/
├── backend/
│   ├── main.py
│   ├── civicconnect.db
│   └── requirements.txt
├── fronted/
│   ├── index.html
│   ├── submit.html
│   ├── complaints.html
│   ├── tracking.html
│   ├── analytics.html
│   └── admin.html
├── css/
│   └── style.css
├── js/
│   ├── api.js
│   ├── app.js
│   ├── storage.js
│   ├── gps.js
│   ├── submit.js
│   ├── complaints.js
│   ├── tracking.js
│   ├── analytics.js
│   └── admin.js
├── uploads/
│   ├── complaint_evidence/
│   └── resolution_evidence/
├── run.bat
└── README.md
```

## Run Locally

1. Install Python 3.10+.
2. Open this project folder.
3. Double-click `run.bat`.
4. Open `http://127.0.0.1:8000/` in Chrome.

The first run installs the Python requirements automatically.

## Demo Flow

### Citizen
1. Open **Report Issue**.
2. Enter a civic complaint in English, Hindi, or Marathi.
3. Use **Use My Current Location** if GPS is available.
4. Submit the complaint.
5. Open **Tracking**.

### Government Officer
1. Open **Administration**.
2. Enter the complaint ID.
3. Click **Load Case**.
4. Update the case to **In Progress** while work is being performed.
5. Upload the actual after-resolution photo/video.
6. Enter the repair/resolution remark.
7. Click **Submit Resolution Proof**.

The system moves the case to **Citizen Verification**.

### Citizen
1. Open **Tracking** for the same complaint.
2. Review the resolution proof.
3. Click **Yes, Issue Is Resolved** or **No, Reopen Complaint**.
4. Add optional feedback/rating.

## API Endpoints

```text
GET    /api/health
GET    /api/complaints
GET    /api/complaints/{id}
POST   /api/complaints
PATCH  /api/complaints/{id}/status
POST   /api/complaints/{id}/resolution
POST   /api/complaints/{id}/citizen-feedback
GET    /api/analytics
```

## Evidence Rules

Resolution evidence accepts:
- JPG / JPEG
- PNG
- WEBP
- MP4
- MOV

Maximum file size: **15 MB**.

Files are stored under `uploads/resolution_evidence/` with generated unique names.

## Important AI Note

The current project uses an **AI-assisted rule-based intelligence layer** for classification, priority and department routing. The resolution evidence score is also an AI-assisted relevance indicator for the hackathon/demo workflow; it should not be described as a trained computer-vision model unless a real vision model/API is integrated.

## Future Scope

- Role-based authentication for citizens/officers/admins
- Cloud object storage for evidence
- Real computer-vision evidence verification
- Face/person privacy masking
- Real-time WebSocket notifications
- SLA escalation engine
- PostgreSQL/MongoDB production deployment
- Government identity integration
- Geo-fencing and field-officer verification



## Live AI Chatbot
Every frontend page now includes the **CivicConnect AI** floating assistant. It calls `POST /api/chat` and reads current SQLite complaint data for complaint status, resolution proof, department routing, issue guidance, and analytics.
