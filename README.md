# CivicConnect AI — Multilingual Citizen Complaint & Governance CRM

**Your Voice. Our Action.**

CivicConnect AI is an end-to-end civic governance platform that helps citizens submit complaints in English, Hindi, or Marathi, captures issue location, performs AI-assisted classification and priority analysis, detects related/duplicate reports, routes cases to departments, monitors SLA risk, and supports government resolution evidence with citizen verification.

## Core workflow

Citizen complaint → language detection → AI classification → priority score → department assignment → GPS → duplicate detection → unified issue group → one government action → resolution photo/video → citizen verification → Closed or Reopened → analytics and audit trail.

## Features

- Multilingual complaint submission
- Browser voice complaint input: English, Hindi, Marathi
- Browser OCR for printed complaint images with preprocessing and confidence
- ML-based complaint category classification + AI-assisted priority detection
- Priority score (1–100)
- Department recommendation
- GPS coordinates and issue map
- Automatic duplicate/related complaint detection
- **Unified duplicate issue groups** with a primary case
- **Affected citizen report aggregation** (report count; no personal identity required)
- **One government action across a related complaint group**
- Resolution proof upload: JPG/PNG/WEBP/MP4/MOV
- AI evidence relevance score (file-type based demo heuristic)
- **Shared resolution evidence across related reports**
- **Citizen-by-citizen verification before a group closes**
- Reopen workflow when a citizen rejects resolution
- SLA monitoring and manual escalation
- Live notifications and audit trail
- Civic Intelligence dashboard and heatmap
- Live civic chatbot connected to complaint data
- Responsive government-tech UI
- FastAPI backend + SQLite database
- Render-ready deployment configuration

## Duplicate complaint workflow

When a new complaint is sufficiently similar to an open complaint, CivicConnect automatically creates or joins a **Unified Issue Group**.

Example:

1. Citizen A reports: `Large pothole near Central Market`.
2. Citizen B reports: `Huge road hole beside market`.
3. The system calculates similarity using complaint text, location, category, and civic keywords.
4. Both reports are linked to one primary case.
5. The dashboard shows the number of related citizen reports.
6. A government status update on one grouped case is propagated to the related reports.
7. Resolution proof uploaded by the authority is shared with the related reports.
8. Each citizen can confirm or reject the resolution.
9. The group closes only after all related citizen reports are confirmed.
10. If any citizen rejects the resolution, the group is reopened.

This is a **related-report aggregation model**, not a claim that the platform knows the real-world identity of citizens. The current demo counts complaint reports as affected citizen reports because authentication/unique citizen identity is not implemented.

## Technology

### Frontend
- HTML5
- CSS3
- Vanilla JavaScript
- Chart.js
- Leaflet
- Tesseract.js for browser OCR
- Web Speech API for browser voice input

### Backend
- Python
- FastAPI
- SQLite
- Uvicorn
- Pydantic
- scikit-learn
- joblib

## Project structure

```text
CivicConnect-AI/
├── backend/
│   ├── main.py
│   ├── advanced_patch.py
│   └── requirements.txt
├── fronted/
│   ├── index.html
│   ├── submit.html
│   ├── complaints.html
│   ├── tracking.html
│   ├── analytics.html
│   ├── advanced.html
│   └── admin.html
├── js/
│   ├── api.js
│   ├── submit.js
│   ├── voice-ocr.js
│   ├── gps.js
│   ├── tracking.js
│   ├── advanced.js
│   ├── admin.js
│   ├── analytics.js
│   ├── complaints.js
│   ├── chatbot.js
│   ├── civic-assist.js
│   ├── app.js
│   └── storage.js
├── css/
│   ├── style.css
│   ├── advanced.css
│   └── chatbot.css
├── uploads/
├── run.bat
└── README.md
```

## Run locally — Windows

### Option 1: run.bat

Double-click `run.bat`.

Then open:

`http://127.0.0.1:8000/`

### Option 2: PowerShell

```powershell
python -m pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open:

`http://127.0.0.1:8000/`

## Recommended hackathon demo

### 1. Submit primary pothole complaint

**Title**
```text
Large pothole near central market
```

**Description**
```text
There is a large pothole on the main road near the central market. The road is badly damaged and dangerous for pedestrians and two-wheelers. Please repair it urgently.
```

Use GPS if available.

### 2. Submit a second report about the same issue

**Title**
```text
Huge road hole beside market
```

**Description**
```text
A huge pothole has appeared near the central market road. Many people are facing difficulty because the damaged road is dangerous for bikes and pedestrians. Immediate road repair is required.
```

Use the same/nearby location.

### 3. Open Civic Intelligence

Go to **Civic Intelligence → Duplicate Intelligence**.

You should see a unified issue group with:

- primary complaint ID
- related complaint IDs
- similarity score
- affected citizen reports
- department
- priority
- group status

### 4. Government action

Open **Administration → Government Resolution Center**.

Load either complaint from the duplicate group.

Change status to:

`In Progress`

The status is automatically propagated to the related group.

### 5. Submit resolution proof

Upload a road-repair photo and enter:

**Officer:** `Municipal Officer`

**Remark:**
```text
The damaged road section has been repaired and the pothole has been filled.
```

The proof is shared with related complaints and their status becomes **Citizen Verification**.

### 6. Citizen verification

Open each related complaint in Tracking.

- **Yes, Issue Is Resolved** → confirmation
- **No, Reopen Complaint** → group reopens

The group closes only after all related reports have confirmed the resolution.

## Voice demo

Use Chrome or Edge and click **Start Speaking**.

English example:

```text
There is a large pothole near the central market road. The road is badly damaged and dangerous for pedestrians and two-wheelers. Please repair it urgently.
```

Marathi example:

```text
मुख्य बाजाराजवळील रस्त्यावर मोठा खड्डा पडला आहे. रस्ता खराब झाला असून पादचारी आणि दुचाकीस्वारांसाठी धोकादायक आहे. कृपया या रस्त्याची लवकरात लवकर दुरुस्ती करावी.
```

## OCR demo

Use a high-resolution image containing clear printed text. The browser OCR performs image upscaling, grayscale/contrast processing, two OCR passes, and reports an OCR confidence value.

For production-grade multilingual OCR, a server-side OCR service with maintained language models would be preferable.

## Important implementation notes

- Voice input is browser-side using Web Speech API; browser support varies.
- OCR is browser-side using Tesseract.js.
- The current translation layer is language detection/rule-based complaint understanding, not a cloud translation model.
- Duplicate detection is explainable text/location/category similarity, not an embedding model.
- Evidence relevance is a demo heuristic; it does not authenticate that a photo is genuine or prove physical completion.
- SLA escalation is available as an action/API; this demo does not run a persistent background scheduler.
- Secure government authentication/RBAC is not implemented in this demo version.
- SQLite/local uploads are suitable for a hackathon/demo; production deployment should use PostgreSQL and durable object storage.

## API highlights

```text
GET  /api/health
GET  /api/complaints
POST /api/complaints
GET  /api/complaints/{id}
PATCH /api/complaints/{id}/status
POST /api/complaints/{id}/resolution
POST /api/complaints/{id}/citizen-feedback
GET  /api/advanced/duplicate-feed
GET  /api/advanced/duplicates/{id}
GET  /api/advanced/groups
GET  /api/advanced/groups/{group_id}
POST /api/advanced/groups/{group_id}/status
GET  /api/advanced/sla
POST /api/advanced/escalate/{id}
GET  /api/advanced/audit/{id}
GET  /api/advanced/notifications
GET  /api/advanced/insights
GET  /api/advanced/heatmap
POST /api/chat
```

## Deployment

The application can be deployed as a FastAPI web service. For a demo deployment, use:

**Build command**
```text
pip install -r backend/requirements.txt
```

**Start command**
```text
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

For a production deployment, replace SQLite/local uploads with managed PostgreSQL and durable object storage.

## Developer

**Dolly Kaddak**

Computer Engineering | Full Stack Development | AI/ML | DSA

## AI/ML Module — Supervised Complaint Classification

CivicConnect AI also contains a **real supervised machine-learning component** for the AI/ML academic project requirement.

### ML problem
**Task:** Predict the category of a citizen complaint from its text.

Input:
- complaint title
- complaint description

Output:
- Infrastructure
- Water Supply
- Electricity
- Sanitation
- Public Safety
- Other

### Dataset
The project includes `ml/complaint_dataset.csv`, a **curated civic-domain dataset containing 240 labeled complaint records** (40 examples per category). It is intentionally included with the source code so the complete ML workflow can be demonstrated and retrained locally.

### Model
The classifier uses:

1. **TF-IDF Vectorization** — converts complaint text into numerical features using word unigrams/bigrams.
2. **Logistic Regression** — supervised classification model that predicts the complaint category.
3. **Probability scoring** — the model exposes the predicted category and confidence/probability distribution.

The trained model is stored in `ml/complaint_classifier.joblib`.

### Evaluation
The included training pipeline uses an 80/20 stratified train-test split with `random_state=42`. Current evaluation on the included curated dataset is:

- Training samples: **192**
- Test samples: **48**
- Test accuracy: **100%**
- Weighted F1: **100%**

Because this is a small curated academic dataset, these metrics should **not** be interpreted as production-world performance. A larger real-world labeled dataset would be required for robust deployment.

### Live integration
When a citizen selects **“AI will automatically classify”** and submits an English complaint, the FastAPI backend calls the trained ML model. The predicted category and ML confidence are stored with the complaint and shown in the AI processing result.

API endpoints:

- `GET /api/ml/info` — model, dataset and evaluation information
- `POST /api/ml/predict` — live complaint classification

### Retrain the model
From the project root:

```bash
python ml/train_model.py
```

This reads `ml/complaint_dataset.csv`, retrains the pipeline, evaluates it, and updates `ml/complaint_classifier.joblib` and `ml/metrics.json`.

### Academic ML workflow

```text
Dataset
   ↓
Data Cleaning
   ↓
Train / Test Split
   ↓
TF-IDF Feature Extraction
   ↓
Logistic Regression
   ↓
Model Evaluation
   ↓
Saved ML Model
   ↓
FastAPI Prediction API
   ↓
CivicConnect Complaint Dashboard
```
