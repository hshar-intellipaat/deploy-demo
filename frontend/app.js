// ---------- config ----------
// Base URL of the backend API. Empty string = same origin (when Flask serves this page).
// On Vercel, set this to your Render URL, e.g. "https://deploy-demo.onrender.com".
const API_BASE = "https://deploy-demo-ooaw.onrender.com";

// ---------- state ----------
let currentUser = null;   // the id of the user chosen in the dropdown
let users = [];           // used to show who is the organiser

// ---------- helpers ----------
function headers(json = false) {
  const h = { "X-User-Id": currentUser };
  if (json) h["Content-Type"] = "application/json";
  return h;
}

function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className = isError ? "error" : "";
  toast.hidden = false;
  setTimeout(() => (toast.hidden = true), 2500);
}

function userById(id) {
  return users.find(u => u.id === id);
}

// ---------- API calls, one per route ----------
async function loadUsers() {
  const res = await fetch(`${API_BASE}/api/users`);
  users = await res.json();

  const select = document.getElementById("user-select");
  select.innerHTML = users
    .map(u => `<option value="${u.id}">${u.email} (${u.role})</option>`)
    .join("");
  currentUser = select.value;
  select.addEventListener("change", () => {
    currentUser = select.value;
    refresh();
  });
}

async function loadEvents() {
  const res = await fetch(`${API_BASE}/api/events`);
  const events = await res.json();

  const me = userById(currentUser);
  document.getElementById("events").innerHTML = events.map(ev => {
    const isOrganiser = ev.organiser_id === currentUser;
    const organiser = userById(ev.organiser_id);
    return `
      <div class="card">
        <h3>${ev.title}</h3>
        <p><span class="badge ${ev.status}">${ev.status}</span></p>
        <p>Capacity: ${ev.capacity}</p>
        <p>Organiser: ${organiser ? organiser.email : ev.organiser_id}</p>
        <div class="actions">
          <button class="primary" onclick="register('${ev.id}')"
                  ${ev.status !== "active" ? "disabled" : ""}>Register</button>
          ${isOrganiser ? `<button onclick="loadAttendees('${ev.id}', '${ev.title}')">Attendees</button>` : ""}
        </div>
      </div>`;
  }).join("");
}

async function register(eventId) {
  const res = await fetch(`${API_BASE}/api/registrations`, {
    method: "POST",
    headers: headers(true),
    body: JSON.stringify({ event_id: eventId })
  });
  const data = await res.json();

  if (res.status === 201) {
    showToast("Registered!");
    loadMyRegistrations();
  } else {
    showToast(data.error, true);   // 409 cases land here
  }
}

async function loadMyRegistrations() {
  const res = await fetch(`${API_BASE}/api/me/registrations`, { headers: headers() });
  const regs = await res.json();

  const list = document.getElementById("my-registrations");
  list.innerHTML = regs.length
    ? regs.map(r => `<li>${r.events.title} <span class="badge ${r.events.status}">${r.events.status}</span></li>`).join("")
    : "<li>No registrations yet.</li>";
}

async function loadAttendees(eventId, title) {
  const res = await fetch(`${API_BASE}/api/events/${eventId}/registrations`, { headers: headers() });
  const data = await res.json();

  if (!res.ok) {
    showToast(data.error, true);   // 403 if not the organiser
    return;
  }
  document.getElementById("attendees-title").textContent = title;
  document.getElementById("attendees").innerHTML = data.length
    ? data.map(r => `<li>${r.users.email}</li>`).join("")
    : "<li>Nobody registered yet.</li>";
  document.getElementById("attendees-section").hidden = false;
}

// ---------- start ----------
function refresh() {
  document.getElementById("attendees-section").hidden = true;
  loadEvents();
  loadMyRegistrations();
}

loadUsers().then(refresh);
