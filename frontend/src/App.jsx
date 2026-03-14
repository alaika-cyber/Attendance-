import { useEffect, useMemo, useState } from "react";
import { api } from "./api/client";
import ImageCapture from "./components/ImageCapture";

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "register", label: "Student Registration" },
  { id: "attendance", label: "Mark Attendance" },
  { id: "admin", label: "Admin Controls" },
  { id: "chatbot", label: "Chatbot" }
];

const emptyRegistration = {
  full_name: "",
  email: "",
  password: "",
  roll_no: "",
  class_code: "",
  class_name: "",
  academic_year: "",
  live_image_b64: ""
};

const emptyAttendance = {
  class_code: "",
  session_date: new Date().toISOString().slice(0, 10),
  latitude: "",
  longitude: "",
  live_image_b64: ""
};

export default function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const [token, setToken] = useState(localStorage.getItem("attendance_token") || "");
  const [health, setHealth] = useState("checking");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [auth, setAuth] = useState({ email: "", password: "" });
  const [registration, setRegistration] = useState(emptyRegistration);
  const [attendance, setAttendance] = useState(emptyAttendance);

  const [approval, setApproval] = useState({ student_id: "", approve: true, reason: "" });
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [spoofAlerts, setSpoofAlerts] = useState([]);
  const [geofence, setGeofence] = useState({ latitude: "", longitude: "", radius_meters: "" });
  const [dashboardFilter, setDashboardFilter] = useState("");
  const [dashboard, setDashboard] = useState({ top_students: [], spoof_summary: { total_attempts: 0 } });
  const [reportMonth, setReportMonth] = useState(new Date().toISOString().slice(0, 7));
  const [classWiseRows, setClassWiseRows] = useState([]);
  const [spoofReportRows, setSpoofReportRows] = useState([]);
  const [studentSummary, setStudentSummary] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [timetableRows, setTimetableRows] = useState([]);
  const [timetableForm, setTimetableForm] = useState({
    subject_name: "",
    class_code: "",
    class_name: "",
    academic_year: "",
    schedule_date: new Date().toISOString().slice(0, 10),
    start_time: "09:00",
    end_time: "10:00"
  });

  const [chatQuery, setChatQuery] = useState("");
  const [chatAnswer, setChatAnswer] = useState("");

  useEffect(() => {
    api
      .health()
      .then(() => setHealth("online"))
      .catch(() => setHealth("offline"));
  }, []);

  useEffect(() => {
    if (!token || activeTab !== "admin") return;
    loadPendingApprovals();
    loadGeofence();
    loadSpoofAlerts();
    loadTimetable();

    const intervalId = setInterval(() => {
      loadSpoofAlerts();
    }, 20000);

    return () => clearInterval(intervalId);
  }, [activeTab, token]);

  useEffect(() => {
    if (!token) return;
    loadNotifications();
    const intervalId = setInterval(() => {
      loadNotifications();
    }, 25000);
    return () => clearInterval(intervalId);
  }, [token]);

  const isLoggedIn = useMemo(() => Boolean(token), [token]);

  function clearAlerts() {
    setMessage("");
    setError("");
  }

  async function handleLogin(event) {
    event.preventDefault();
    clearAlerts();
    try {
      const response = await api.login(auth);
      setToken(response.access_token);
      localStorage.setItem("attendance_token", response.access_token);
      try {
        const summary = await api.studentSummary(response.access_token);
        setStudentSummary(summary);
      } catch {
        setStudentSummary(null);
      }
      try {
        const inbox = await api.myNotifications(response.access_token, false, 20);
        setNotifications(inbox);
      } catch {
        setNotifications([]);
      }
      setMessage("Login successful.");
    } catch (err) {
      setError(err.message);
    }
  }

  function logout() {
    setToken("");
    localStorage.removeItem("attendance_token");
    setStudentSummary(null);
    setNotifications([]);
    setMessage("Logged out.");
  }

  async function submitRegistration(event) {
    event.preventDefault();
    clearAlerts();
    try {
      const response = await api.registerStudent(registration);
      setMessage(`Student registered with ID ${response.student_id}. Waiting admin approval.`);
      setRegistration(emptyRegistration);
    } catch (err) {
      setError(err.message);
    }
  }

  async function markAttendance(event) {
    event.preventDefault();
    clearAlerts();
    try {
      const payload = {
        ...attendance,
        latitude: Number(attendance.latitude),
        longitude: Number(attendance.longitude)
      };
      const response = await api.markAttendance(payload, token);
      setMessage(`Attendance marked. Record ID ${response.attendance_id}.`);
      setAttendance({ ...emptyAttendance, class_code: attendance.class_code });
    } catch (err) {
      setError(err.message);
    }
  }

  async function useCurrentLocation() {
    clearAlerts();
    if (!navigator.geolocation) {
      setError("Geolocation is not supported in this browser.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setAttendance((prev) => ({
          ...prev,
          latitude: position.coords.latitude.toFixed(6),
          longitude: position.coords.longitude.toFixed(6)
        }));
      },
      () => setError("Unable to fetch location.")
    );
  }

  async function submitApproval(event) {
    event.preventDefault();
    clearAlerts();
    try {
      const payload = {
        student_id: Number(approval.student_id),
        approve: approval.approve,
        reason: approval.reason || null
      };
      const response = await api.approveStudent(payload, token);
      setMessage(
        `Student ${response.student_id} marked ${response.status}. Email notification ${response.email_notification_sent ? "sent" : "not sent"}.`
      );
      setApproval({ student_id: "", approve: true, reason: "" });
      await loadPendingApprovals();
    } catch (err) {
      setError(err.message);
    }
  }

  async function approveFromCard(studentId, approve) {
    clearAlerts();
    try {
      const response = await api.approveStudent(
        {
          student_id: studentId,
          approve,
          reason: approve ? null : "Rejected by admin review"
        },
        token
      );
      setMessage(
        `Student ${response.student_id} marked ${response.status}. Email notification ${response.email_notification_sent ? "sent" : "not sent"}.`
      );
      await loadPendingApprovals();
    } catch (err) {
      setError(err.message);
    }
  }

  async function loadPendingApprovals() {
    try {
      const response = await api.pendingApprovals(token);
      setPendingApprovals(response);
    } catch (err) {
      setError(err.message);
    }
  }

  async function loadSpoofAlerts() {
    try {
      const response = await api.spoofAlerts(token, 24);
      setSpoofAlerts(response);
    } catch (err) {
      setError(err.message);
    }
  }

  async function loadNotifications() {
    try {
      const inbox = await api.myNotifications(token, false, 20);
      setNotifications(inbox);
    } catch (err) {
      setError(err.message);
    }
  }

  async function markNotificationRead(notificationId) {
    try {
      await api.markNotificationRead(token, notificationId);
      await loadNotifications();
    } catch (err) {
      setError(err.message);
    }
  }

  async function loadGeofence() {
    try {
      const response = await api.getGeofence(token);
      setGeofence({
        latitude: String(response.latitude),
        longitude: String(response.longitude),
        radius_meters: String(response.radius_meters)
      });
    } catch (err) {
      setError(err.message);
    }
  }

  async function loadTimetable() {
    try {
      const rows = await api.listTimetable(
        token,
        timetableForm.class_code || undefined,
        timetableForm.schedule_date || undefined
      );
      setTimetableRows(rows);
    } catch (err) {
      setError(err.message);
    }
  }

  async function createTimetable(event) {
    event.preventDefault();
    clearAlerts();
    try {
      await api.createTimetable(timetableForm, token);
      setMessage("Weekly class schedule saved.");
      await loadTimetable();
    } catch (err) {
      setError(err.message);
    }
  }

  async function removeTimetable(scheduleId) {
    clearAlerts();
    try {
      await api.deleteTimetable(scheduleId, token);
      setMessage("Schedule removed.");
      await loadTimetable();
    } catch (err) {
      setError(err.message);
    }
  }

  async function saveGeofence(event) {
    event.preventDefault();
    clearAlerts();
    try {
      const payload = {
        latitude: Number(geofence.latitude),
        longitude: Number(geofence.longitude),
        radius_meters: Number(geofence.radius_meters)
      };
      await api.updateGeofence(payload, token);
      setMessage("Campus geofence updated.");
    } catch (err) {
      setError(err.message);
    }
  }

  async function loadDashboard() {
    clearAlerts();
    try {
      const response = await api.dashboard(token, dashboardFilter || undefined);
      setDashboard(response);
      setMessage("Dashboard loaded.");
    } catch (err) {
      setError(err.message);
    }
  }

  async function loadClassWiseReport() {
    clearAlerts();
    try {
      if (!dashboardFilter) {
        throw new Error("Enter classroom ID to load class-wise report.");
      }
      const rows = await api.classWiseReport(token, dashboardFilter, reportMonth || undefined);
      setClassWiseRows(rows);
      setMessage("Class-wise attendance report loaded.");
    } catch (err) {
      setError(err.message);
    }
  }

  async function loadSpoofReport() {
    clearAlerts();
    try {
      const rows = await api.spoofReport(token, dashboardFilter || undefined, reportMonth || undefined);
      setSpoofReportRows(rows);
      setMessage("Spoof attempt report loaded.");
    } catch (err) {
      setError(err.message);
    }
  }

  async function sendMonthlyEmails() {
    clearAlerts();
    try {
      const result = await api.sendMonthlyReportEmails(token, reportMonth || undefined);
      setMessage(
        `Monthly reports sent for ${result.month}. Student emails: ${result.student_emails_sent}, admin emails: ${result.admin_emails_sent}.`
      );
    } catch (err) {
      setError(err.message);
    }
  }

  async function askChatbot(event) {
    event.preventDefault();
    clearAlerts();
    try {
      const response = await api.chatbot({ query: chatQuery }, token);
      setChatAnswer(response.answer);
      setMessage("Chatbot response generated.");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="app-shell">
      <div className="bg-orb bg-orb-one" />
      <div className="bg-orb bg-orb-two" />

      <header className="topbar">
        <div>
          <p className="kicker">AI Attendance Framework</p>
          <h1>Facial Recognition Command Center</h1>
          <p className="subtext">Real-time biometric attendance with geofence, anti-spoofing, analytics, and chatbot support.</p>
        </div>

        <div className="status-panel">
          <span className={`status-chip ${health === "online" ? "ok" : health === "offline" ? "bad" : "idle"}`}>
            API {health}
          </span>
          {isLoggedIn ? (
            <button className="btn ghost" onClick={logout}>Log out</button>
          ) : null}
        </div>
      </header>

      <nav className="tabbar">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`tab-btn ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {message ? <div className="alert ok">{message}</div> : null}
      {error ? <div className="alert bad">{error}</div> : null}

      {activeTab === "overview" ? (
        <section className="grid two-col">
          <article className="card">
            <h2>Operator Login</h2>
            <p className="muted">Use student or admin credentials to unlock protected modules.</p>
            <form onSubmit={handleLogin} className="form">
              <label>
                Email
                <input
                  type="email"
                  value={auth.email}
                  onChange={(e) => setAuth((prev) => ({ ...prev, email: e.target.value }))}
                  required
                />
              </label>
              <label>
                Password
                <input
                  type="password"
                  value={auth.password}
                  onChange={(e) => setAuth((prev) => ({ ...prev, password: e.target.value }))}
                  required
                />
              </label>
              <button className="btn" type="submit">Login</button>
            </form>
          </article>

          <article className="card metric-panel">
            <h2>System Snapshot</h2>
            <div className="metrics">
              <div>
                <p className="metric-value">{isLoggedIn ? "Authorized" : "Guest"}</p>
                <p className="metric-label">Session</p>
              </div>
              <div>
                <p className="metric-value">{dashboard.spoof_summary.total_attempts || 0}</p>
                <p className="metric-label">Spoof Attempts</p>
              </div>
              <div>
                <p className="metric-value">{dashboard.top_students.length}</p>
                <p className="metric-label">Top Students Loaded</p>
              </div>
            </div>
            <button className="btn ghost" type="button" onClick={loadDashboard} disabled={!isLoggedIn}>
              Refresh Dashboard Data
            </button>

            {studentSummary ? (
              <div className="chat-answer" style={{ marginTop: "0.8rem" }}>
                <p className="field-label">My Attendance Summary</p>
                <p>
                  {studentSummary.attendance_percentage.toFixed(2)}% ({studentSummary.present_count}/
                  {studentSummary.total_sessions})
                  {studentSummary.shortage ? " - shortage alert" : " - healthy"}
                </p>
              </div>
            ) : null}

            <div style={{ marginTop: "0.9rem" }}>
              <div className="toolbar">
                <h2>Notifications</h2>
                <button className="btn ghost" type="button" onClick={loadNotifications} disabled={!isLoggedIn}>
                  Refresh
                </button>
              </div>
              {notifications.length === 0 ? (
                <p className="muted">No notifications.</p>
              ) : (
                <div className="notification-list">
                  {notifications.map((item) => (
                    <article className={`notification-item ${item.is_read ? "" : "unread"}`} key={item.id}>
                      <div>
                        <p className="field-label">{item.severity.toUpperCase()} - {item.notification_type}</p>
                        <p><strong>{item.title}</strong></p>
                        <p>{item.message}</p>
                        <p className="muted">{new Date(item.created_at).toLocaleString()}</p>
                      </div>
                      {!item.is_read ? (
                        <button className="btn ghost" type="button" onClick={() => markNotificationRead(item.id)}>
                          Mark Read
                        </button>
                      ) : null}
                    </article>
                  ))}
                </div>
              )}
            </div>
          </article>
        </section>
      ) : null}

      {activeTab === "register" ? (
        <section className="card">
          <h2>Student Registration and Live Capture</h2>
          <form onSubmit={submitRegistration} className="grid form-grid">
            <label>
              Full Name
              <input
                value={registration.full_name}
                onChange={(e) => setRegistration((prev) => ({ ...prev, full_name: e.target.value }))}
                required
              />
            </label>
            <label>
              Email
              <input
                type="email"
                value={registration.email}
                onChange={(e) => setRegistration((prev) => ({ ...prev, email: e.target.value }))}
                required
              />
            </label>
            <label>
              Password
              <input
                type="password"
                value={registration.password}
                onChange={(e) => setRegistration((prev) => ({ ...prev, password: e.target.value }))}
                required
              />
            </label>
            <label>
              Roll Number
              <input
                value={registration.roll_no}
                onChange={(e) => setRegistration((prev) => ({ ...prev, roll_no: e.target.value }))}
                required
              />
            </label>
            <label>
              Class Code
              <input
                value={registration.class_code}
                onChange={(e) => setRegistration((prev) => ({ ...prev, class_code: e.target.value }))}
                required
              />
            </label>
            <label>
              Class Name
              <input
                value={registration.class_name}
                onChange={(e) => setRegistration((prev) => ({ ...prev, class_name: e.target.value }))}
                required
              />
            </label>
            <label>
              Academic Year
              <input
                value={registration.academic_year}
                onChange={(e) => setRegistration((prev) => ({ ...prev, academic_year: e.target.value }))}
                required
              />
            </label>

            <ImageCapture
              label="Live Face Capture"
              onChange={(base64) => setRegistration((prev) => ({ ...prev, live_image_b64: base64 }))}
            />

            <button className="btn" type="submit">Submit Registration</button>
          </form>
        </section>
      ) : null}

      {activeTab === "attendance" ? (
        <section className="card">
          <h2>Mark Attendance</h2>
          <p className="muted">Requires approved student account and active login token.</p>
          <form onSubmit={markAttendance} className="grid form-grid">
            <label>
              Class Code
              <input
                value={attendance.class_code}
                onChange={(e) => setAttendance((prev) => ({ ...prev, class_code: e.target.value }))}
                required
              />
            </label>
            <label>
              Session Date
              <input
                type="date"
                value={attendance.session_date}
                onChange={(e) => setAttendance((prev) => ({ ...prev, session_date: e.target.value }))}
                required
              />
            </label>
            <label>
              Latitude
              <input
                value={attendance.latitude}
                onChange={(e) => setAttendance((prev) => ({ ...prev, latitude: e.target.value }))}
                required
              />
            </label>
            <label>
              Longitude
              <input
                value={attendance.longitude}
                onChange={(e) => setAttendance((prev) => ({ ...prev, longitude: e.target.value }))}
                required
              />
            </label>

            <button type="button" className="btn ghost" onClick={useCurrentLocation}>
              Use Current Location
            </button>

            <ImageCapture
              label="Live Attendance Capture"
              onChange={(base64) => setAttendance((prev) => ({ ...prev, live_image_b64: base64 }))}
            />

            <button className="btn" type="submit" disabled={!isLoggedIn}>Mark Present</button>
          </form>
        </section>
      ) : null}

      {activeTab === "admin" ? (
        <section className="grid two-col">
          <article className="card">
            <h2>Approve or Reject Student</h2>
            <form onSubmit={submitApproval} className="form">
              <label>
                Student ID
                <input
                  type="number"
                  value={approval.student_id}
                  onChange={(e) => setApproval((prev) => ({ ...prev, student_id: e.target.value }))}
                  required
                />
              </label>
              <label className="inline-control">
                <input
                  type="checkbox"
                  checked={approval.approve}
                  onChange={(e) => setApproval((prev) => ({ ...prev, approve: e.target.checked }))}
                />
                Approve Student
              </label>
              <label>
                Decision Reason (optional)
                <input
                  value={approval.reason}
                  onChange={(e) => setApproval((prev) => ({ ...prev, reason: e.target.value }))}
                  placeholder="Example: Face quality mismatch during review"
                />
              </label>
              <button className="btn" type="submit" disabled={!isLoggedIn}>Submit Decision</button>
            </form>
          </article>

          <article className="card">
            <h2>Campus Geofence</h2>
            <form className="form" onSubmit={saveGeofence}>
              <label>
                Latitude
                <input
                  value={geofence.latitude}
                  onChange={(e) => setGeofence((prev) => ({ ...prev, latitude: e.target.value }))}
                  required
                />
              </label>
              <label>
                Longitude
                <input
                  value={geofence.longitude}
                  onChange={(e) => setGeofence((prev) => ({ ...prev, longitude: e.target.value }))}
                  required
                />
              </label>
              <label>
                Radius (meters)
                <input
                  type="number"
                  min="1"
                  value={geofence.radius_meters}
                  onChange={(e) => setGeofence((prev) => ({ ...prev, radius_meters: e.target.value }))}
                  required
                />
              </label>
              <button className="btn" type="submit" disabled={!isLoggedIn}>Update Geofence</button>
            </form>
          </article>

          <article className="card" style={{ gridColumn: "1 / -1" }}>
            <h2>Timetable Management</h2>
            <form className="grid form-grid" onSubmit={createTimetable}>
              <label>
                Subject / Course Name
                <input
                  value={timetableForm.subject_name}
                  onChange={(e) => setTimetableForm((prev) => ({ ...prev, subject_name: e.target.value }))}
                  required
                />
              </label>
              <label>
                Class / Section Code
                <input
                  value={timetableForm.class_code}
                  onChange={(e) => setTimetableForm((prev) => ({ ...prev, class_code: e.target.value }))}
                  required
                />
              </label>
              <label>
                Class Name (optional)
                <input
                  value={timetableForm.class_name}
                  onChange={(e) => setTimetableForm((prev) => ({ ...prev, class_name: e.target.value }))}
                />
              </label>
              <label>
                Academic Year (optional)
                <input
                  value={timetableForm.academic_year}
                  onChange={(e) => setTimetableForm((prev) => ({ ...prev, academic_year: e.target.value }))}
                />
              </label>
              <label>
                Date
                <input
                  type="date"
                  value={timetableForm.schedule_date}
                  onChange={(e) => setTimetableForm((prev) => ({ ...prev, schedule_date: e.target.value }))}
                  required
                />
              </label>
              <label>
                Start Time
                <input
                  type="time"
                  value={timetableForm.start_time}
                  onChange={(e) => setTimetableForm((prev) => ({ ...prev, start_time: e.target.value }))}
                  required
                />
              </label>
              <label>
                End Time
                <input
                  type="time"
                  value={timetableForm.end_time}
                  onChange={(e) => setTimetableForm((prev) => ({ ...prev, end_time: e.target.value }))}
                  required
                />
              </label>
              <button className="btn" type="submit" disabled={!isLoggedIn}>Save Weekly Schedule</button>
            </form>

            <div className="toolbar" style={{ marginTop: "0.85rem" }}>
              <button className="btn ghost" type="button" onClick={loadTimetable} disabled={!isLoggedIn}>
                Refresh Timetable
              </button>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Subject</th>
                    <th>Class</th>
                    <th>Date</th>
                    <th>Start</th>
                    <th>End</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {timetableRows.length === 0 ? (
                    <tr>
                      <td colSpan="7">No schedules found.</td>
                    </tr>
                  ) : (
                    timetableRows.map((row) => (
                      <tr key={row.schedule_id}>
                        <td>{row.schedule_id}</td>
                        <td>{row.subject_name}</td>
                        <td>{row.class_code}</td>
                        <td>{row.schedule_date}</td>
                        <td>{row.start_time}</td>
                        <td>{row.end_time}</td>
                        <td>
                          <button
                            className="btn ghost"
                            type="button"
                            onClick={() => removeTimetable(row.schedule_id)}
                            disabled={!isLoggedIn}
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </article>

          <article className="card" style={{ gridColumn: "1 / -1" }}>
            <div className="toolbar">
              <h2>Pending Approval List</h2>
              <button className="btn ghost" type="button" onClick={loadPendingApprovals} disabled={!isLoggedIn}>
                Refresh Pending
              </button>
            </div>

            {pendingApprovals.length === 0 ? (
              <p className="muted">No pending students.</p>
            ) : (
              <div className="pending-grid">
                {pendingApprovals.map((student) => (
                  <article className="pending-card" key={student.student_id}>
                    <img
                      src={student.captured_image_b64}
                      alt={`Captured face of ${student.full_name}`}
                      className="pending-image"
                    />
                    <div>
                      <p><strong>ID:</strong> {student.student_id}</p>
                      <p><strong>Name:</strong> {student.full_name}</p>
                      <p><strong>Email:</strong> {student.email}</p>
                      <p><strong>Roll:</strong> {student.roll_no}</p>
                      <p><strong>Class:</strong> {student.class_name} ({student.class_code})</p>
                      <p><strong>Year:</strong> {student.academic_year}</p>
                    </div>
                    <div className="capture-actions">
                      <button
                        type="button"
                        className="btn"
                        onClick={() => approveFromCard(student.student_id, true)}
                        disabled={!isLoggedIn}
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        className="btn ghost"
                        onClick={() => approveFromCard(student.student_id, false)}
                        disabled={!isLoggedIn}
                      >
                        Reject
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </article>

          <article className="card" style={{ gridColumn: "1 / -1" }}>
            <div className="toolbar">
              <h2>Spoof Alerts and Evidence</h2>
              <button className="btn ghost" type="button" onClick={loadSpoofAlerts} disabled={!isLoggedIn}>
                Refresh Alerts
              </button>
            </div>

            {spoofAlerts.length === 0 ? (
              <p className="muted">No spoof alerts detected.</p>
            ) : (
              <div className="pending-grid">
                {spoofAlerts.map((alert) => (
                  <article className="pending-card" key={alert.event_id}>
                    <img
                      src={alert.evidence_image_b64}
                      alt={`Spoof evidence ${alert.event_id}`}
                      className="pending-image"
                    />
                    <div>
                      <p><strong>Alert ID:</strong> {alert.event_id}</p>
                      <p><strong>Student:</strong> {alert.student_name || "Unknown"} ({alert.student_id || "-"})</p>
                      <p><strong>Roll:</strong> {alert.roll_no || "-"}</p>
                      <p><strong>Class:</strong> {alert.class_name || "-"} ({alert.class_code || "-"})</p>
                      <p><strong>Type:</strong> {alert.spoof_type}</p>
                      <p><strong>Reason:</strong> {alert.reason}</p>
                      <p><strong>Status:</strong> {alert.alert_status}</p>
                      <p><strong>Timestamp:</strong> {new Date(alert.timestamp).toLocaleString()}</p>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </article>

          <article className="card" style={{ gridColumn: "1 / -1" }}>
            <h2>Analytics Dashboard</h2>
            <div className="toolbar">
              <input
                placeholder="Optional classroom ID"
                value={dashboardFilter}
                onChange={(e) => setDashboardFilter(e.target.value)}
              />
              <input
                type="month"
                value={reportMonth}
                onChange={(e) => setReportMonth(e.target.value)}
              />
              <button className="btn ghost" type="button" onClick={loadDashboard} disabled={!isLoggedIn}>
                Load Data
              </button>
              <button className="btn ghost" type="button" onClick={loadClassWiseReport} disabled={!isLoggedIn}>
                Class-Wise Report
              </button>
              <button className="btn ghost" type="button" onClick={loadSpoofReport} disabled={!isLoggedIn}>
                Spoof Report
              </button>
              <button className="btn" type="button" onClick={sendMonthlyEmails} disabled={!isLoggedIn}>
                Send Monthly Emails
              </button>
            </div>

            <p className="muted">Spoof Attempts: {dashboard.spoof_summary.total_attempts || 0}</p>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Student ID</th>
                    <th>Name</th>
                    <th>Roll No</th>
                    <th>Class</th>
                    <th>Present Count</th>
                    <th>Total Sessions</th>
                    <th>Attendance %</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboard.top_students.length === 0 ? (
                    <tr>
                      <td colSpan="7">No records loaded.</td>
                    </tr>
                  ) : (
                    dashboard.top_students.map((row) => (
                      <tr key={row.student_id}>
                        <td>{row.student_id}</td>
                        <td>{row.full_name}</td>
                        <td>{row.roll_no}</td>
                        <td>{row.class_code}</td>
                        <td>{row.present_count}</td>
                        <td>{row.total_sessions}</td>
                        <td>{row.attendance_percentage.toFixed(2)}%</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <h2 style={{ marginTop: "1rem" }}>Class-Wise Attendance Report</h2>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Student ID</th>
                    <th>Name</th>
                    <th>Roll</th>
                    <th>Class</th>
                    <th>Present</th>
                    <th>Total</th>
                    <th>Attendance %</th>
                  </tr>
                </thead>
                <tbody>
                  {classWiseRows.length === 0 ? (
                    <tr>
                      <td colSpan="7">No class-wise report loaded.</td>
                    </tr>
                  ) : (
                    classWiseRows.map((row) => (
                      <tr key={row.student_id}>
                        <td>{row.student_id}</td>
                        <td>{row.full_name}</td>
                        <td>{row.roll_no}</td>
                        <td>{row.class_code}</td>
                        <td>{row.present_count}</td>
                        <td>{row.total_sessions}</td>
                        <td>{row.attendance_percentage.toFixed(2)}%</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <h2 style={{ marginTop: "1rem" }}>Spoof Attempt Report</h2>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Event</th>
                    <th>Student</th>
                    <th>Roll</th>
                    <th>Class</th>
                    <th>Type</th>
                    <th>When</th>
                  </tr>
                </thead>
                <tbody>
                  {spoofReportRows.length === 0 ? (
                    <tr>
                      <td colSpan="6">No spoof report loaded.</td>
                    </tr>
                  ) : (
                    spoofReportRows.map((row) => (
                      <tr key={row.event_id}>
                        <td>{row.event_id}</td>
                        <td>{row.student_name || "Unknown"}</td>
                        <td>{row.roll_no || "-"}</td>
                        <td>{row.class_code || "-"}</td>
                        <td>{row.spoof_type}</td>
                        <td>{new Date(row.timestamp).toLocaleString()}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </article>
        </section>
      ) : null}

      {activeTab === "chatbot" ? (
        <section className="card">
          <h2>Hybrid Attendance Chatbot</h2>
          <p className="muted">Ask questions such as attendance percentage or shortage alerts.</p>
          <form onSubmit={askChatbot} className="form">
            <label>
              Query
              <textarea
                rows="4"
                value={chatQuery}
                onChange={(e) => setChatQuery(e.target.value)}
                placeholder="Example: Am I below 75 percent attendance?"
                required
              />
            </label>
            <button className="btn" type="submit" disabled={!isLoggedIn}>Ask Assistant</button>
          </form>

          {chatAnswer ? (
            <div className="chat-answer">
              <p className="field-label">Assistant Response</p>
              <p>{chatAnswer}</p>
            </div>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
