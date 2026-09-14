# 🏛️ CivicConnect AI

### Multilingual Citizen Complaint & Governance CRM

> **Your Voice. Our Action.**

CivicConnect AI is a modern government-technology platform designed to make civic complaint reporting, tracking, departmental routing, resolution verification, and governance analytics more transparent and accessible.

The platform connects **citizens, AI-assisted complaint processing, government departments, and resolution verification** through a single web application.

---

## 🚀 Why CivicConnect AI?

Citizens often face challenges when reporting civic problems:

- Language barriers
- Difficulty identifying the correct government department
- Slow complaint processing
- Lack of complaint-status visibility
- No clear proof that a reported issue was actually resolved
- Limited visibility into recurring civic problems

CivicConnect AI addresses these problems through a centralized digital governance workflow.

---

## 🎯 Core Workflow

```text
Citizen
   ↓
Submit Complaint
   ↓
AI-Assisted Analysis
   ↓
Priority Detection
   ↓
Department Assignment
   ↓
Government Action
   ↓
Resolution Evidence
   ↓
Citizen Verification
   ↓
Closed / Reopened
   ↓
Governance Analytics
✨ Key Features
👤 Citizen Complaint Submission

Citizens can submit civic complaints with:

Complaint title
Detailed description
Category
Location
GPS coordinates
Supporting evidence
Multilingual text

Every complaint receives a unique complaint ID for tracking.

🌐 Multilingual Support

Citizens can submit complaints using:

🇮🇳 English
🇮🇳 Hindi
🇮🇳 Marathi

The backend detects the language of the submitted complaint and processes it through the civic complaint workflow.

Example
मुख्य बाजाराजवळील रस्त्यावर मोठा खड्डा पडला आहे.
कृपया हा रस्ता लवकरात लवकर दुरुस्त करावा.
🤖 AI-Assisted Complaint Processing

CivicConnect analyzes complaint descriptions to determine:

Complaint category
Priority
Responsible department
Language
AI confidence information
Example
Citizen:
"There is a large pothole near the main market."

AI Processing:
Category    → Infrastructure
Priority    → Based on detected severity
Department  → Public Works

The current hackathon implementation uses backend rule-based AI-style classification logic optimized for the civic-domain MVP.

⚠️ Intelligent Priority Detection

Complaints are automatically assigned a priority according to detected severity.

Priority Levels

🔴 Critical

🟠 Medium

🟢 Low

This helps government teams identify complaints that may require faster attention.

🏢 Automatic Department Assignment

CivicConnect maps complaint categories to responsible departments.

Complaint Category	Responsible Department
Infrastructure	Public Works
Water Supply	Water Department
Electricity	Electricity
Sanitation	Sanitation
Public Safety	Public Safety
Other	Municipal Corporation
📍 GPS & Location Support

Citizens can use:

Use My Current Location

The application can capture:

Latitude
Longitude
Location accuracy
Detected address
Map position

The captured location is attached to the complaint when it is submitted.

Technologies
Browser Geolocation API
Leaflet
OpenStreetMap
Reverse Geocoding

GPS functionality depends on browser permission and the device/network's location services.

🔎 Complaint Tracking

Every complaint receives a unique ID.

Example:

CC1028

Citizens can use the Tracking module to view:

Complaint ID
Complaint title
Category
Priority
Department
Location
Current status
Processing timeline
Resolution information
Map location
👨‍💼 Government Administration

Government officers can manage complaints through the Administration module.

Complaint lifecycle
Pending
   ↓
In Progress
   ↓
Resolution Submitted
   ↓
Citizen Verification
   ↓
Resolved / Closed

A complaint can also be:

Reopened

when the citizen reports that the issue has not actually been resolved.

📸 Resolution Proof

One of CivicConnect AI's key features is resolution evidence.

Instead of simply changing:

Pending → Resolved

the government officer can provide evidence of the completed work.

The resolution module supports:

📷 Resolution photo
🎥 Resolution video
📝 Resolution remark
👨‍💼 Officer name
📅 Resolution date
🤖 Evidence confidence/relevance information

This creates greater transparency between government departments and citizens.

✅ Citizen Verification

After a department submits resolution evidence, the citizen can review the proof.

The citizen can choose:

✅ Issue Resolved

or

❌ Reopen Complaint
Successful resolution
Resolution Submitted
        ↓
Citizen Verification
        ↓
Closed
Unsuccessful resolution
Resolution Submitted
        ↓
Citizen Verification
        ↓
Reopened

This creates a complete citizen-government feedback loop.

🤖 CivicConnect AI Chatbot

CivicConnect includes a floating AI chatbot available throughout the application.

The chatbot is connected to the application backend and can query the current complaint data stored in SQLite.

Web Interface
      ↓
FastAPI /api/chat
      ↓
CivicConnect Backend
      ↓
SQLite
      ↓
Live Complaint Information

The chatbot is designed as an application-connected civic assistant, rather than a static FAQ page.

Example questions
What is the status of complaint CC1028?
Which department is handling CC1028?
Has CC1028 been resolved?
Is there resolution proof for CC1028?
How many complaints are currently registered?
Which department has the most complaints?

It can also process natural civic issue descriptions:

There is a large pothole near the market and it is
dangerous for pedestrians. What should I do?
📊 Governance Analytics

The Analytics dashboard provides a visual overview of complaint data.

KPI Dashboard
Total Complaints
Resolved Complaints
Active Cases
Critical Complaints
GPS Coverage
Analytics
Complaint volume
Category distribution
Priority distribution
Department workload
Resolution performance
Geographic information
Top issue categories

The dashboard derives its statistics from the application's complaint data.

🎨 Professional Government UI

The interface follows a modern government-service design approach.

Design principles
🏛️ Government-style visual identity
🔵 Professional blue/navy color palette
⚪ Clean white and soft-gray surfaces
🟢 Resolution status indicators
🟠 Pending/attention indicators
🔴 Critical issue indicators
✨ Smooth animations
🎯 Clear call-to-action buttons
📱 Responsive layouts
🤖 Persistent AI assistant
📊 Modern analytics cards and charts

The goal is to combine:

Trust of public services + usability of modern digital platforms

🧩 System Architecture
┌───────────────────────────────────────┐
│           Citizen Web UI              │
│                                       │
│     HTML + CSS + Vanilla JavaScript  │
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│              FastAPI                  │
│           Python Backend              │
│                                       │
│ Complaints │ AI │ Chatbot │ GPS      │
│ Tracking   │ Admin │ Analytics        │
└───────────────────┬───────────────────┘
                    │
                    ▼
┌───────────────────────────────────────┐
│                SQLite                 │
│        CivicConnect Complaint Data    │
└───────────────────────────────────────┘
🛠️ Technology Stack
Frontend
HTML5
CSS3
Vanilla JavaScript
Chart.js
Leaflet
OpenStreetMap
Backend
Python
FastAPI
Uvicorn
Pydantic
Database
SQLite
Browser Technologies
Geolocation API
Fetch API
FormData
Local browser storage
📁 Project Structure
CivicConnect-AI/
│
├── backend/
│   ├── main.py
│   └── requirements.txt
│
├── css/
│   ├── style.css
│   └── chatbot.css
│
├── fronted/
│   ├── index.html
│   ├── submit.html
│   ├── complaints.html
│   ├── tracking.html
│   ├── analytics.html
│   └── admin.html
│
├── js/
│   ├── api.js
│   ├── app.js
│   ├── chatbot.js
│   ├── submit.js
│   ├── complaints.js
│   ├── tracking.js
│   ├── analytics.js
│   ├── admin.js
│   ├── gps.js
│   └── storage.js
│
├── uploads/
│   └── resolution_evidence/
│
├── README.md
└── run.bat
⚙️ Installation
Requirements
Python 3.10+
Modern web browser
Git
1. Clone the repository
git clone https://github.com/dollykaddak07-cpu/CivicConnect-AI.git
cd CivicConnect-AI
2. Install dependencies
python -m pip install -r backend/requirements.txt
3. Start the application
Windows

You can simply run:

run.bat

Or manually:

python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
4. Open CivicConnect

Visit:

http://127.0.0.1:8000/
🧪 Complete Demo
1️⃣ Submit a complaint
Title
Large pothole near the main market
Description
There is a large pothole on the main road near the market.
The road is badly damaged and dangerous for pedestrians and
two-wheelers. Please repair the road as soon as possible.

Click:

Use My Current Location

Then submit.

2️⃣ AI Processing

The system identifies:

Category    → Infrastructure
Priority    → Based on severity
Department  → Public Works
Language    → English
3️⃣ Government Processing

Open:

Administration

Load the generated complaint ID.

Change:

Pending → In Progress
4️⃣ Resolution

Upload a resolution image/video and add a remark.

Example:

The damaged road section has been repaired and inspected
after completion.
5️⃣ Citizen Verification

The citizen reviews the resolution evidence.

Choose:

Yes, Issue Is Resolved

or:

No, Reopen Complaint
6️⃣ Analytics

Open:

Analytics

View updated:

Complaint statistics
Priority distribution
Category distribution
Department workload
Resolution performance
7️⃣ Chatbot

Try:

What is the latest status of my complaint?

or use a real complaint ID:

What is the status of complaint CC1028?
💬 Chatbot Demo Questions
Complaint Tracking
What is the status of complaint CC1028?
Track complaint CC1028.
Which department is handling CC1028?
Resolution
Has CC1028 been resolved?
Is there resolution proof for CC1028?
Who resolved CC1028?
Departments
Which department handles street lights?
Which department handles water supply complaints?
Who handles garbage collection?
Analytics
How many complaints are currently registered?
How many complaints are resolved?
Which department has the most complaints?
Natural civic issue
There is a dangerous pothole near the market.
What should I do?
Marathi
माझ्या भागात रस्त्यावर मोठा खड्डा आहे.
यासाठी कोणता विभाग जबाबदार आहे?
🔐 Production Considerations

This project is designed as a hackathon/academic prototype.

A production government deployment should additionally implement:

Secure authentication
Role-based authorization
Encryption
Secure file storage
Audit logs
Production database infrastructure
API security
Backup and recovery
Government identity integration
Data retention policies
Monitoring and alerting
🚀 Future Enhancements

Potential future improvements:

🔐 Citizen/officer authentication
🪪 Government identity integration
🌍 Additional Indian languages
🧠 Production-grade NLP/LLM integration
🔎 Advanced duplicate complaint detection
🗺️ GIS-based civic issue mapping
📱 Mobile/PWA application
🔔 SMS, email and WhatsApp notifications
⏱️ SLA monitoring and automatic escalation
📈 Predictive civic analytics
🏙️ Ward-level dashboards
☁️ Cloud deployment
🔒 Enterprise security and audit trails
🏆 Project Highlights

CivicConnect AI brings together:

Citizen Reporting + AI-Assisted Processing + GPS + Government Routing + Resolution Evidence + Citizen Verification + Analytics + Live Civic Chatbot

The central idea is:

Don't just record a complaint. Close the loop.
REPORT
   ↓
UNDERSTAND
   ↓
ROUTE
   ↓
ACT
   ↓
PROVE
   ↓
VERIFY
   ↓
CLOSE
👩‍💻 Developer
Dolly Kaddak

Computer Engineering Student

Skills: C++ • Python • Full Stack Development • DSA • Machine Learning

GitHub

https://github.com/dollykaddak07-cpu

Project

https://github.com/dollykaddak07-cpu/CivicConnect-AI