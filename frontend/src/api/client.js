const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

async function request(path, { method = "GET", token, body } = {}) {
  const headers = {
    "Content-Type": "application/json"
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

export const api = {
  health: () => request("/health"),
  login: (payload) => request("/auth/login", { method: "POST", body: payload }),
  registerStudent: (payload) => request("/registration/student", { method: "POST", body: payload }),
  markAttendance: (payload, token) =>
    request("/attendance/mark", { method: "POST", body: payload, token }),
  approveStudent: (payload, token) =>
    request("/admin/approve-student", { method: "POST", body: payload, token }),
  pendingApprovals: (token) => request("/admin/pending-approvals", { token }),
  spoofAlerts: (token, limit = 20) => request(`/admin/spoof-alerts?limit=${encodeURIComponent(limit)}`, { token }),
  getGeofence: (token) => request("/admin/geofence", { token }),
  updateGeofence: (payload, token) =>
    request("/admin/geofence", { method: "PUT", body: payload, token }),
  createTimetable: (payload, token) =>
    request("/admin/timetable", { method: "POST", body: payload, token }),
  listTimetable: (token, classCode, scheduleDate) => {
    const classQuery = classCode ? `class_code=${encodeURIComponent(classCode)}&` : "";
    const dateQuery = scheduleDate ? `schedule_date=${encodeURIComponent(scheduleDate)}&` : "";
    return request(`/admin/timetable?${classQuery}${dateQuery}`, { token });
  },
  deleteTimetable: (scheduleId, token) =>
    request(`/admin/timetable/${scheduleId}`, { method: "DELETE", token }),
  dashboard: (token, classroomId) => {
    const query = classroomId ? `?classroom_id=${encodeURIComponent(classroomId)}` : "";
    return request(`/analytics/dashboard${query}`, { token });
  },
  classWiseReport: (token, classroomId, month) => {
    const monthQuery = month ? `&month=${encodeURIComponent(month)}` : "";
    return request(`/analytics/class-wise?classroom_id=${encodeURIComponent(classroomId)}${monthQuery}`, {
      token
    });
  },
  spoofReport: (token, classroomId, month) => {
    const classQuery = classroomId ? `classroom_id=${encodeURIComponent(classroomId)}&` : "";
    const monthQuery = month ? `month=${encodeURIComponent(month)}&` : "";
    return request(`/analytics/spoof-report?${classQuery}${monthQuery}limit=100`, { token });
  },
  studentSummary: (token, month) => {
    const query = month ? `?month=${encodeURIComponent(month)}` : "";
    return request(`/analytics/student-summary${query}`, { token });
  },
  sendMonthlyReportEmails: (token, month) => {
    const query = month ? `?month=${encodeURIComponent(month)}` : "";
    return request(`/analytics/monthly-email-report${query}`, { method: "POST", token });
  },
  myNotifications: (token, unreadOnly = false, limit = 30) =>
    request(
      `/notifications/my?limit=${encodeURIComponent(limit)}&unread_only=${encodeURIComponent(unreadOnly)}`,
      { token }
    ),
  markNotificationRead: (token, notificationId) =>
    request(`/notifications/${notificationId}/read`, { method: "POST", token }),
  chatbot: (payload, token) => request("/chatbot/query", { method: "POST", body: payload, token })
};
