# AI-Powered Facial Recognition Attendance Framework

Production-oriented attendance platform for educational institutions with:

- Secure student registration with live biometric enrollment
- Admin-verified onboarding before attendance is enabled
- Facial matching and spoof attempt detection
- GPS-based geofence validation
- Weekly timetable management by admin
- Present/Late attendance classification based on class timing
- Classwise attendance isolation for record integrity
- Analytics dashboard APIs (top students, spoof summaries)
- Hybrid chatbot (rule-based + OpenAI integration)
- Automatic notification center for students/admin
- Cloud-ready Docker deployment

## 0. New Feature Highlights

- Weekly Timetable Management:
	- Admin can create/delete weekly class schedules with date, subject, start, and end time.
	- Attendance can only be marked during scheduled windows.
- Late Attendance Module:
	- At class start time -> `Present`
	- After start and before end -> `Late`
	- After end time -> blocked (operationally absent)
- Notification Module:
	- Student: low attendance and spoof attempt warnings
	- Admin: spoof alerts, suspicious activity alerts, monthly report alerts
- Reports & Dashboard Enhancements:
	- Top regular students sorted by attendance percentage
	- Class-wise reports
	- Spoof reports
	- Monthly email reports with optional automatic scheduler

## 1. Architecture

```text
Student Mobile/Web Client
				|
				v
Nginx Reverse Proxy ---> FastAPI Backend ---> SQLite
															|
															+--> Face Service (embedding + matching)
															+--> Liveness/Spoof Service
															+--> GeoFence Validation
															+--> Analytics Service
															+--> Hybrid Chatbot Service (OpenAI optional)
```

Core backend location: [backend](backend)

## 2. Module Coverage

### Student Registration & Live Capture

- Student provides full profile and live image
- System stores hashed password + generated face embedding
- Account remains pending until admin approval

Endpoint: `POST /api/v1/registration/student`

### Admin Approval

- Admin dashboard exposes a pending approvals list
- Admin can review student profile + captured photo before decision
- Approve: student account is activated for attendance marking
- Reject: student account remains blocked from attendance marking
- Email notification is sent on approval/rejection when SMTP is configured

Endpoint: `POST /api/v1/admin/approve-student`

Supporting endpoints:

- `GET /api/v1/admin/pending-approvals`
- `GET /api/v1/admin/geofence`
- `PUT /api/v1/admin/geofence`

### Attendance Marking (Secure)

- JWT-authenticated student request
- Geofence verification
- Liveness/spoof score check
- Face embedding similarity check
- Classwise duplicate protection (unique per class and date)
- Attendance persisted with timestamp in the attendance table
- Timetable window enforcement: attendance allowed only when class is scheduled for the day and current time is within admin-defined start/end
- Late attendance logic:
	- At class start time: `Present`
	- After start and before end: `Late`
	- After end time: not allowed (can be treated as absent operationally)
- Attendance table status values: `Present`, `Late`, `Absent`

Geofence coordinates are admin-configurable from the dashboard/API.

### Admin Weekly Timetable Management

- Admin can create weekly class schedules with subject, class code, date, start time, and end time
- Schedules are stored in DB and used to gate attendance marking
- Students are blocked from marking attendance outside scheduled windows

Timetable endpoints:

- `POST /api/v1/admin/timetable`
- `GET /api/v1/admin/timetable`
- `DELETE /api/v1/admin/timetable/{schedule_id}`

Endpoint: `POST /api/v1/attendance/mark`

### Spoof Monitoring

- Suspicious events are persisted with image evidence payload
- Admin dashboard can aggregate spoof attempts
- Each spoof attempt records student, class, timestamp, spoof type, and evidence image
- Admin alert feed is available for real-time dashboard review

Table: `spoof_events`

Endpoint: `GET /api/v1/admin/spoof-alerts`

### Dashboard Analytics

- Top regular students sorted by attendance percentage
- Spoof attempt summaries
- Classwise filter support
- Class-wise attendance reports
- Spoof attempt report (who tried, when, class, type)
- Monthly report email dispatch for students/admin

Endpoint: `GET /api/v1/analytics/dashboard`

Additional report endpoints:

- `GET /api/v1/analytics/top-regular`
- `GET /api/v1/analytics/class-wise`
- `GET /api/v1/analytics/spoof-report`
- `GET /api/v1/analytics/student-summary`
- `POST /api/v1/analytics/monthly-email-report`

Automatic monthly email reports:

- Enable with `AUTO_MONTHLY_REPORTS_ENABLED=true`
- Scheduler runs on the 1st day of month at `MONTHLY_REPORT_RUN_HOUR_UTC` and sends reports for previous month

### Hybrid Attendance Chatbot

- Rule-based responses for attendance/shortage queries
- Optional OpenAI response fallback for broader natural language support
- Rule-based answers use real student attendance percentage and shortage threshold checks

Endpoint: `POST /api/v1/chatbot/query`

### Notification Module

- Student alerts:
	- Low attendance warning
	- Spoof attempt warning when attendance is blocked
- Admin alerts:
	- Spoof attempt alerts
	- Suspicious activity alerts (high spoof attempts in 24h)
	- Monthly report generation alerts

Notification endpoints:

- `GET /api/v1/notifications/my`
- `POST /api/v1/notifications/{notification_id}/read`

## 3. Security and Production Controls

- Password hashing with bcrypt (`passlib`)
- JWT auth (`python-jose`)
- Role-based authorization (student/admin)
- Request validation with Pydantic
- Isolated classwise attendance model
- Containerized deployment using Docker Compose
- Nginx reverse proxy in front of API

## 4. Local and Cloud-Ready Setup

### Prerequisites

- Docker + Docker Compose
- Node.js 20+ (for frontend dev server)

### Environment

1. Copy [.env.example](.env.example) to `.env`
2. Set secure values for `SECRET_KEY`, `DATABASE_URL`, and geofence center
3. Optionally set `OPENAI_API_KEY`
4. For emails/alerts, configure SMTP values

### Option A: Run Full Stack with Docker (Backend + Nginx)

```bash
docker compose up --build
```

Backend API health:

```bash
curl http://localhost:8000/api/v1/health
```

Nginx proxy health:

```bash
curl http://localhost/api/v1/health
```

### Option B: Recommended Dev Mode (Docker backend + React frontend)

1. Start backend services:

```bash
docker compose up --build
```

2. In a second terminal, start frontend:

```bash
cd frontend
npm install
npm run dev
```

3. Open frontend:

- `http://localhost:5173`

### First-Time Admin Setup

After backend startup, create admin account:

```bash
docker compose exec api python /app/scripts/bootstrap_admin.py
```

Default login:

- Email: `admin@attendance.local`
- Password: `admin1234`

## 5. Initial Admin Bootstrap

Admin bootstrap steps and default credentials are described in Section 4 under **First-Time Admin Setup**.

## 6. Key API Flows

### Student Registration

```json
{
	"full_name": "Aarav Sharma",
	"email": "aarav@example.edu",
	"password": "StrongPass#123",
	"roll_no": "CSE24-021",
	"class_code": "CSE-A-2026",
	"class_name": "Computer Science A",
	"academic_year": "2025-2026",
	"live_image_b64": "data:image/jpeg;base64,..."
}
```

### Attendance Mark Request

```json
{
	"class_code": "CSE-A-2026",
	"session_date": "2026-03-14",
	"latitude": 12.9716,
	"longitude": 77.5946,
	"live_image_b64": "data:image/jpeg;base64,..."
}
```

## 7. Important Engineering Notes

- Current face embedding module uses a deterministic framework-safe baseline for reproducibility.
- For true production biometric performance, replace embedding logic with ArcFace/FaceNet and maintain a proper model pipeline with calibration.
- Spoof detection is currently heuristic; replace with trained anti-spoof model and challenge-response workflow for higher security.
- Add migrations (Alembic), audit logging, and object storage for encrypted evidence retention before enterprise rollout.

## 8. Testing

Example unit test exists for geofence logic in [backend/tests/test_geofence.py](backend/tests/test_geofence.py).

Run tests:

```bash
docker compose exec api pytest -q
```

## 9. Frontend Application

A complete React frontend is available in [frontend](frontend) with modules for:

- Operator login and session handling
- Student registration with live capture/upload
- Attendance marking with geolocation and live capture
- Admin approval workflow
- Analytics dashboard view
- Hybrid chatbot query interface

### Frontend Run

```bash
cd frontend
npm install
npm run dev
```

Optional frontend env:

- `VITE_API_BASE_URL` default: `http://localhost:8000/api/v1`