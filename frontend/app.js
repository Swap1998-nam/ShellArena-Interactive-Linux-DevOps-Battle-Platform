"use strict";

const $ = (selector, root = document) => root.querySelector(selector);
const app = $("#app");
const modal = $("#modal");
const state = {
  csrf: "",
  data: null,
  lab: null,
  busy: false,
  category: "All",
  difficulty: "All",
  query: "",
  savedOnly: false,
  routeToken: 0,
  historyIndex: 0,
};
const paths = {
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  terminal:
    '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="m7 9 3 3-3 3m6 0h4"/>',
  layers: '<path d="m12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5m-18 5 9 5 9-5"/>',
  trophy:
    '<path d="M8 3h8v6a4 4 0 0 1-8 0V3Zm0 2H4v2a4 4 0 0 0 4 4m8-6h4v2a4 4 0 0 1-4 4m-4 2v5m-4 3h8m-6-3h4"/>',
  chart: '<path d="M4 3v17h17M8 15l4-5 4 2 5-7"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  flame:
    '<path d="M12 3c1 6 7 7 7 12a7 7 0 0 1-14 0c0-3 2-5 4-7 0 3 2 4 3 3 2-2 1-5 0-8Z"/>',
  bolt: '<path d="m13 2-9 12h7l-1 8 10-13h-8l1-7Z"/>',
  arrow: '<path d="M4 12h16m-6-6 6 6-6 6"/>',
  chevron: '<path d="m9 5 7 7-7 7"/>',
  back: '<path d="M20 12H4m6-6-6 6 6 6"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
  settings:
    '<path d="m9 3-.5 3-2 1-3-.5-2 3 2.5 2v2L1.5 16l2 3 3-.5 2 1 .5 3h5l.5-3 2-1 3 .5 2-3-2.5-2.5v-2l2.5-2-2-3-3 .5-2-1L14 3H9Z"/><circle cx="11.5" cy="13" r="3"/>',
  shield:
    '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/>',
  book: '<path d="M4 4h6l2 2 2-2h6v16h-6l-2 1-2-1H4V4Zm8 2v15"/>',
  bookmark: '<path d="M6 3h12v18l-6-4-6 4V3Z"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  checkCircle: '<circle cx="12" cy="12" r="9"/><path d="m7 12 3 3 7-7"/>',
  box: '<path d="m12 3 9 5v9l-9 5-9-5V8l9-5Zm-9 5 9 5 9-5m-9 5v9M7 5.5l10 5.5"/>',
  helm: '<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2"/><path d="M12 2v8m0 4v8M2 12h8m4 0h8M5 5l5 5m4 4 5 5M5 19l5-5m4-4 5-5"/>',
  git: '<circle cx="6" cy="4" r="2"/><circle cx="18" cy="6" r="2"/><circle cx="6" cy="20" r="2"/><path d="M6 6v12m12-10c0 6-12 3-12 8"/>',
  calendar:
    '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4m10-4v4M3 11h18m-13 4h2m4 0h2"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 22v-3a8 8 0 0 1 16 0v3"/>',
  activity: '<path d="M2 12h4l3-8 6 16 3-8h4"/>',
  lock: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V6a4 4 0 0 1 8 0v4m-4 5v2"/>',
  download: '<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
  refresh: '<path d="M20 8a8 8 0 1 0 0 9M20 3v6h-6"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.1"/>',
  x: '<path d="m6 6 12 12M6 18 18 6"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  logout: '<path d="M9 3H4v18h5m5-16 7 7-7 7m-6-7h13"/>',
  spark:
    '<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Z"/>',
};
const icon = (name) =>
  `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${paths[name] || paths.terminal}</svg>`;
const escape = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const categories = {
  Linux: ["terminal", ""],
  Docker: ["box", "blue"],
  Kubernetes: ["helm", "purple"],
  Git: ["git", "red"],
  Security: ["shield", "green"],
  DevOps: ["layers", "blue"],
};
const fmt = new Intl.NumberFormat();
const missionById = (id) => state.data.missions.find((m) => m.id === id);
const isComplete = (id) =>
  state.data.completions.some((c) => c.mission_id === id);
const initials = (name) => name.slice(0, 2).toUpperCase();
const dateLabel = (timestamp) =>
  new Date(timestamp * 1000).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

async function api(path, data) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(`/api${path}`, {
      method: data === undefined ? "GET" : "POST",
      credentials: "same-origin",
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        "X-ShellArena": "1",
        "X-CSRF-Token": state.csrf,
      },
      ...(data === undefined ? {} : { body: JSON.stringify(data) }),
    });
    const result = await response.json();
    if (!response.ok)
      throw new Error(result.error || "The request failed. Please try again.");
    return result;
  } catch (error) {
    if (error.name === "AbortError")
      throw new Error(
        "The request timed out. Check your connection and try again.",
      );
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
function toast(message, error = false) {
  const node = document.createElement("div");
  node.className = `toast${error ? " error" : ""}`;
  node.textContent = message;
  const region = $("#toast-region");
  while (region.children.length >= 2) region.firstElementChild.remove();
  region.append(node);
  setTimeout(() => node.remove(), 5000);
}
async function refresh() {
  state.data = await api("/overview");
}
function navItem(href, label, name, page, count = "") {
  return `<a href="#/${href}" class="${page === href ? "active" : ""}" ${page === href ? 'aria-current="page"' : ""}>${icon(name)}<span>${label}</span>${count ? `<span class="count">${count}</span>` : ""}</a>`;
}
function shell(page, title, content) {
  const { user, stats } = state.data;
  app.innerHTML = `<div class="layout ${user.compact ? "compact" : ""}">
  <aside class="sidebar" aria-label="Main navigation"><a href="#/dashboard" class="brand"><img src="/assets/mark.svg" alt="" width="34" height="34"><span>Shell<span>Arena</span></span></a>
   <div class="workspace-label">YOUR WORKSPACE<span>⌘</span></div>
   <nav class="nav">${navItem("dashboard", "Overview", "grid", page)}${navItem("missions", "Mission library", "layers", page, state.data.missions.length)}${navItem("arena", "Practice arena", "terminal", page)}${navItem("leaderboard", "Leaderboard", "trophy", page)}${navItem("activity", "Your activity", "activity", page)}</nav>
   <div class="workspace-label">PERSONAL</div><nav class="nav">${navItem("profile", "Your progress", "chart", page)}${navItem("settings", "Settings", "settings", page)}</nav>
   <div class="sidebar-bottom"><div class="practice-note">${icon("shield")}<h3>Big skills. Safe experiments.</h3><p>Learn in a simulated workspace.<br>Your real systems stay untouched.</p></div>
   <div class="side-profile"><span class="avatar">${escape(initials(user.name))}</span><div><strong>${escape(user.name)}</strong><small>Level ${stats.level} · ${user.guest ? "Guest explorer" : "Arena member"}</small></div><a href="#/settings" aria-label="Profile settings">${icon("chevron")}</a></div></div>
  </aside>
  <div class="main-wrap"><header class="topbar"><button class="mobile-toggle" data-action="menu" aria-label="Toggle navigation" aria-expanded="false">${icon("menu")}</button><div class="breadcrumb"><span>Workspace</span>${icon("chevron")}<span class="current">${escape(title)}</span></div><div class="top-actions"><button class="search-trigger" data-action="search" aria-label="Search missions">${icon("search")}<span>Search anything...</span><kbd>⌘ K</kbd></button><span class="top-divider"></span><span class="status-dot">Practice mode</span>${user.guest ? '<button class="btn small ghost" data-action="register">Save progress</button>' : `<a class="avatar" href="#/profile" aria-label="Open profile">${escape(initials(user.name))}</a>`}</div></header>
  <main id="main" tabindex="-1">${content}<footer class="page-footer"><span>© ${new Date().getFullYear()} ShellArena. One command closer.</span><span>${icon("shield")} Simulated labs · Real learning</span></footer></main></div></div>`;
  document.title = `${title} · ShellArena`;
}
function intro(eyebrow, title, subtitle, aside = "") {
  return `<div class="page-intro"><div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1><p>${subtitle}</p></div>${aside}</div>`;
}
function statsGrid() {
  const { stats } = state.data;
  return `<div class="stats-grid">${[
    [
      "Total experience",
      fmt.format(stats.xp),
      "XP",
      "bolt",
      "Every mission moves you forward",
      false,
    ],
    [
      "Missions completed",
      String(stats.completed).padStart(2, "0"),
      `/ ${state.data.missions.length}`,
      "checkCircle",
      stats.completed
        ? "Keep the momentum going"
        : "Your first win is one command away",
      true,
    ],
    [
      "Learning streak",
      stats.streak,
      stats.streak === 1 ? "day" : "days",
      "flame",
      "Complete a mission each day · UTC",
      false,
    ],
    [
      "Current level",
      String(stats.level).padStart(2, "0"),
      stats.level < 3 ? "Explorer" : "Operator",
      "trophy",
      `${500 - (stats.xp % 500)} XP to your next level`,
      false,
    ],
  ]
    .map(
      ([label, value, unit, name, caption, positive]) =>
        `<div class="stat"><div class="stat-head">${label}${icon(name)}</div><div class="stat-value"><strong>${value}</strong><span>${unit}</span></div><small class="${positive ? "positive" : ""}">${caption}</small></div>`,
    )
    .join("")}</div>`;
}
function missionCard(m) {
  const [name, color] = categories[m.category],
    completed = isComplete(m.id),
    saved = state.data.bookmarks.includes(m.id);
  return `<article class="mission-card"><div class="mission-top"><span class="category-icon ${color}">${icon(name)}</span><button class="icon-btn ${saved ? "saved" : ""}" data-action="bookmark" data-id="${m.id}" aria-pressed="${saved}" aria-label="${saved ? "Unsave" : "Save"} ${escape(m.title)}">${icon("bookmark")}</button></div><div class="mission-meta"><span>${m.category}</span><span>·</span><span class="difficulty ${m.difficulty.toLowerCase()}">${m.difficulty}</span></div><h3><a href="#/arena/${m.id}">${m.title}</a></h3><p>${m.description}</p><div class="mission-footer"><span class="xp-tag">${icon(completed ? "checkCircle" : "bolt")}${completed ? "Completed" : `${m.xp} XP`}</span><a href="#/arena/${m.id}" aria-label="${completed ? "Replay" : "Start"} ${escape(m.title)}">${m.minutes} min ${icon("arrow")}</a></div></article>`;
}
function skillList() {
  return `<div class="skill-list">${Object.entries(categories)
    .slice(0, 5)
    .map(([category, [name]]) => {
      const missions = state.data.missions.filter(
          (m) => m.category === category,
        ),
        count = missions.filter((m) => isComplete(m.id)).length;
      return `<div><div class="skill-line">${icon(name)}<span>${category}</span><small>${count}/${missions.length}</small></div><div class="progress-track"><progress value="${count}" max="${missions.length}" aria-label="${category} progress"></progress></div></div>`;
    })
    .join("")}</div>`;
}
function weekPanel() {
  const total = state.data.week.reduce((sum, d) => sum + d.count, 0);
  return `<section class="panel"><div class="section-title"><h2>Your week in practice</h2>${icon("activity")}</div><div class="activity-summary"><strong>${total} <small>missions</small></strong><small>Last 7 days</small></div><div class="week-bars">${state.data.week.map((d, i) => `<div class="day-column ${i === 6 ? "today" : ""}" title="${d.date}: ${d.count} missions"><div class="bar-track"><span class="day-bar h-${Math.min(d.count, 5)} ${d.count ? "active" : ""}"></span></div>${new Date(d.date + "T12:00:00Z").toLocaleDateString("en", { weekday: "narrow", timeZone: "UTC" })}<span class="sr-only">: ${d.count} missions</span></div>`).join("")}</div><div class="activity-caption">${total ? "Small steps. Lasting progress." : "A little practice today goes a long way."}</div></section>`;
}
function renderDashboard() {
  const { user, active } = state.data;
  const next = active
    ? missionById(active.mission_id)
    : state.data.missions.find((m) => !isComplete(m.id)) ||
      state.data.missions[0];
  const picks = [
    state.data.missions[0],
    missionById("container-recon"),
    missionById("pod-patrol"),
  ];
  const daily = missionById(state.data.daily_id);
  shell(
    "dashboard",
    "Overview",
    `${intro("YOUR NEXT LEVEL STARTS HERE", `Ready when you are${user.guest ? "." : `, ${escape(user.name)}.`}`, "A little curiosity. A few commands. A better engineer.", `<div class="date-pill">${icon("calendar")}${new Date().toLocaleDateString("en", { month: "short", day: "numeric", year: "numeric" })}</div>`)}${statsGrid()}
 <div class="content-grid"><div class="main-column"><section class="hero"><div class="hero-copy"><div class="eyebrow">${icon("terminal")} LEARN BY DOING</div><h2>Your terminal.<br>Your <em>proving ground.</em></h2><p>Break things. Figure them out. Build the Linux & DevOps skills that stick.</p><a class="btn primary" href="#/arena/${next.id}">${active ? "Continue practising" : "Enter the arena"}${icon("arrow")}</a></div><div class="hero-art" aria-hidden="true"><div class="mini-terminal"><div class="mini-terminal-head"><span></span><span></span><span></span><span class="terminal-label mono">arena@workspace ~</span></div><div class="mini-terminal-body mono"><div><b>❯</b> whoami</div><div>the next great engineer</div><div><b>❯</b> cat your-potential.txt</div><div><i>Curiosity is your superpower.</i></div><div><b>❯</b> <span class="terminal-cursor"></span></div></div><span class="floating-tag">${icon("shield")} A safe place to get good</span></div></div></section>
 <section><div class="section-title"><div><h2>Pick your next challenge</h2><p>Hands on. Heads down. Level up.</p></div><a class="text-link" href="#/missions">All missions ${icon("arrow")}</a></div><div class="mission-grid">${picks.map(missionCard).join("")}</div></section>
 <div class="bottom-strip">${icon("spark")}<div><h3>Consistency beats intensity.</h3><p>Make a little room for learning. Your future self will thank you.</p></div><a class="text-link" href="#/profile">View your journey ${icon("arrow")}</a></div></div>
 <aside class="right-column">${weekPanel()}<section class="panel"><div class="section-title"><h2>Your skill stack</h2><a class="text-link" href="#/profile" aria-label="View all skill progress">${icon("arrow")}</a></div>${skillList()}</section><section class="panel daily-panel"><div class="daily-header"><span class="eyebrow">THE DAILY MISSION</span>${icon("bolt")}</div><h3>${daily.title}</h3><p>${daily.category} · ${daily.minutes} min · ${daily.xp} XP</p><a class="btn small ghost" href="#/arena/${daily.id}">Challenge accepted ${icon("arrow")}</a></section></aside></div>`,
  );
}
function filteredMissions() {
  return state.data.missions.filter(
    (m) =>
      (state.category === "All" || m.category === state.category) &&
      (state.difficulty === "All" || m.difficulty === state.difficulty) &&
      (!state.savedOnly || state.data.bookmarks.includes(m.id)) &&
      `${m.title} ${m.description} ${m.category} ${m.tags.join(" ")}`
        .toLowerCase()
        .includes(state.query.toLowerCase()),
  );
}
function updateMissionResults() {
  const results = filteredMissions();
  $("#mission-results").innerHTML = results.length
    ? results.map(missionCard).join("")
    : `<div class="empty-state">${icon("search")}<h2>No missions found</h2><p>Try a different keyword or clear your filters to explore everything.</p><button class="btn" data-action="clear-filters">Clear filters</button></div>`;
  $("#result-count").textContent = `${results.length} missions to explore`;
}
function renderMissions() {
  shell(
    "missions",
    "Mission library",
    `${intro("LESS SCROLLING. MORE BUILDING.", "Find your next challenge.", "From your first command to deployment day. Pick a skill and get hands-on.")}
 <div class="filters"><div class="filter-tabs" role="group" aria-label="Filter by skill">${["All", ...Object.keys(categories)].map((c) => `<button class="chip ${state.category === c ? "active" : ""}" data-action="category" data-value="${c}" aria-pressed="${state.category === c}">${c === "All" ? "All missions" : c}</button>`).join("")}</div><label class="search-field">${icon("search")}<input id="mission-search" type="search" placeholder="Search missions..." value="${escape(state.query)}" aria-label="Search missions"></label></div>
 <div class="filter-bottom"><span class="result-count" id="result-count"></span><div><button class="chip ${state.savedOnly ? "active" : ""}" data-action="saved-only" aria-pressed="${state.savedOnly}">Saved</button><select class="filter-select" id="difficulty" aria-label="Filter by difficulty">${["All", "Beginner", "Intermediate", "Advanced"].map((d) => `<option ${state.difficulty === d ? "selected" : ""}>${d}</option>`).join("")}</select></div></div><div class="mission-grid library" id="mission-results"></div>`,
  );
  updateMissionResults();
}
function objectivesMarkup() {
  const mission = missionById(state.lab.mission_id);
  return `<div class="section-title"><h2>Your objectives</h2><small>${state.lab.checks.filter(Boolean).length}/${state.lab.checks.length}</small></div><ul class="objectives">${mission.objectives.map((label, i) => `<li class="${state.lab.checks[i] ? "done" : ""}"><span class="objective-check">${state.lab.checks[i] ? icon("check") : ""}</span><span>${escape(label)}</span><span class="sr-only">${state.lab.checks[i] ? "Complete" : "Incomplete"}</span></li>`).join("")}</ul>`;
}
function hintsMarkup() {
  return `<div class="section-title"><h2>A nudge in the right direction</h2>${icon("info")}</div><p class="muted-text">Each hint costs 10 XP from this mission’s first completion. Learning is the goal.</p>${state.lab.hints.map((hint, i) => `<div class="hint-box"><strong>Hint ${i + 1}</strong><br>${escape(hint)}</div>`).join("")}<button class="btn small ghost" data-action="hint" ${state.lab.hints_used >= missionById(state.lab.mission_id).hint_count ? "disabled" : ""}>${icon("spark")}${state.lab.hints_used ? "Next hint" : "Reveal a hint"} · −10 XP</button>`;
}
function terminalEntry(entry) {
  return `<div class="terminal-entry"><div class="terminal-command"><span class="prompt-user">arena</span> <span class="prompt-dir">❯</span> ${escape(entry.command)}</div><div class="terminal-response ${entry.exit_code ? "error" : ""}">${escape(entry.output)}</div></div>`;
}
function completionMarkup() {
  if (!state.lab.checks.every(Boolean)) return "";
  const m = missionById(state.lab.mission_id),
    record = state.data.completions.find((x) => x.mission_id === m.id);
  const next = state.data.missions.find((x) => !isComplete(x.id));
  return `<div class="complete-banner">${icon("trophy")}<div><h3>Mission accomplished.</h3><p>${record ? `${record.xp} XP earned for this mission.` : "All objectives complete."} Replays keep your skills sharp.</p></div><a class="btn small" href="${next ? `#/arena/${next.id}` : "#/missions"}">${next ? "Next mission" : "Mission library"}${icon("arrow")}</a></div>`;
}
async function renderArena(id, token) {
  const missionId = id || state.data.active?.mission_id || "first-contact";
  const mission = missionById(missionId);
  if (!mission) {
    location.hash = "/missions";
    return;
  }
  shell(
    "arena",
    "Practice arena",
    `<div class="loading-block">Preparing your practice workspace…</div>`,
  );
  const lab = await api("/labs", { mission_id: missionId });
  if (token !== state.routeToken) return;
  state.lab = lab;
  state.data.active = { id: lab.id, mission_id: lab.mission_id };
  state.historyIndex = lab.history.length;
  shell(
    "arena",
    "Practice arena",
    `<div class="arena-back"><a class="text-link" href="#/missions">${icon("back")} Mission library</a></div>${intro(`${mission.category.toUpperCase()} / ${mission.difficulty.toUpperCase()}`, mission.title, escape(mission.description), `<button class="btn small ghost" data-action="reset">${icon("refresh")}Restart lab</button>`)}<div class="legend"><span>${icon("bolt")}${mission.xp} XP</span><span>${icon("clock")}${mission.minutes} min</span><span>${icon("shield")}Simulated workspace</span></div>
 <div class="arena-layout"><div><section class="terminal-window" aria-label="Practice terminal"><div class="terminal-toolbar"><div class="terminal-dots" aria-hidden="true"><i></i><i></i><i></i></div><span class="label mono">arena@workspace</span><span class="status-dot">Session ready</span><button class="icon-btn" data-action="clear-terminal" aria-label="Clear terminal display">${icon("x")}</button></div><div class="terminal-output" id="terminal-output" role="log" aria-label="Terminal output" aria-live="polite" tabindex="0"><div class="terminal-welcome"><strong>Welcome to ShellArena.</strong>\nA safe place to experiment. A good place to start.\nType <strong>help</strong> for supported commands. ↑ ↓ for history.\nThis terminal simulates Linux; infrastructure output is practice data.</div>${lab.history.map(terminalEntry).join("")}</div><form class="terminal-input-row" id="command-form"><label for="command-input">arena <span class="prompt-dir">❯</span></label><input id="command-input" name="command" autocomplete="off" autocapitalize="off" spellcheck="false" maxlength="512" placeholder="Type a command..." aria-label="Terminal command"><button class="btn small" type="submit">Run ${icon("arrow")}</button></form><div class="terminal-bottom"><span id="cwd" class="mono">${escape(lab.cwd)}</span><span id="command-count">${lab.commands} commands · saved automatically</span></div></section><div id="completion">${completionMarkup()}</div><details class="arena-help"><summary>Command quick reference</summary><div class="command-reference">${["pwd", "ls -la", "cat FILE", "grep PATTERN FILE", "mkdir DIR", "chmod 600 FILE", "help"].map((x) => `<code>${escape(x)}</code>`).join("")}</div></details></div><aside class="arena-side"><section class="panel" id="objectives">${objectivesMarkup()}</section><section class="panel" id="hints">${hintsMarkup()}</section></aside></div>`,
  );
  const output = $("#terminal-output");
  output.scrollTop = output.scrollHeight;
  $("#command-input").focus({ preventScroll: true });
}
function renderActivity() {
  const { activity } = state.data;
  shell(
    "activity",
    "Your activity",
    `${intro("SMALL STEPS. A BIGGER PICTURE.", "Your work, in motion.", "Every experiment is part of the journey. Here are your latest 50 milestones.")}
 ${activity.length ? `<section class="panel"><ul class="activity-list">${activity.map((a) => `<li><span class="event-icon ${a.kind === "started" ? "started" : ""}">${icon(a.kind === "completed" ? "checkCircle" : a.kind === "account" ? "user" : "terminal")}</span><div><div class="event-title">${escape(a.detail)}</div><div class="event-time">${dateLabel(a.created_at)}</div></div>${a.mission_id ? `<a class="text-link" href="#/arena/${a.mission_id}">Open mission ${icon("arrow")}</a>` : ""}</li>`).join("")}</ul></section>` : `<div class="empty-state">${icon("activity")}<h2>Your story starts here.</h2><p>Start a mission and your learning milestones will appear here.</p><a class="btn primary" href="#/arena/first-contact">Start your first mission ${icon("arrow")}</a></div>`}`,
  );
}
function renderProfile() {
  const { user, stats } = state.data;
  const badges = [
    [
      "First steps",
      "Complete your first mission",
      "terminal",
      stats.completed >= 1,
    ],
    [
      "Finding your flow",
      "Complete 5 different missions",
      "flame",
      stats.completed >= 5,
    ],
    [
      "Double digits",
      "Complete 10 different missions",
      "layers",
      stats.completed >= 10,
    ],
    [
      "Arena graduate",
      "Complete every mission",
      "trophy",
      stats.completed === state.data.missions.length,
    ],
  ];
  shell(
    "profile",
    "Your progress",
    `${intro("PROGRESS YOU CAN BE PROUD OF", "Look how far you can go.", "Build a habit. Expand your skill stack. Earn every milestone.")}<section class="panel profile-hero"><span class="avatar">${escape(initials(user.name))}</span><div><h2>${escape(user.name)}</h2><p>Level ${stats.level} ${stats.level < 3 ? "Explorer" : "Operator"} · ${user.guest ? "Guest progress is saved in this browser session" : "Your progress travels with your account"}</p></div>${user.guest ? '<button class="btn primary" data-action="register">Create an account</button>' : '<button class="btn" data-action="export">Export progress</button>'}</section>${statsGrid()}<div class="section-title"><h2>Your achievements</h2><small>${badges.filter((x) => x[3]).length} of 4 unlocked</small></div><div class="badges-grid">${badges.map(([title, description, name, unlocked]) => `<article class="badge-card ${unlocked ? "" : "locked"}">${icon(name)}<h3>${title}</h3><p>${description}</p><small>${unlocked ? "Unlocked" : "Keep exploring"}</small></article>`).join("")}</div><section class="panel"><div class="section-title"><h2>Your skill stack</h2><a class="text-link" href="#/missions">Keep building ${icon("arrow")}</a></div>${skillList()}</section>`,
  );
}
async function renderLeaderboard(token) {
  shell(
    "leaderboard",
    "Leaderboard",
    `<div class="loading-block">Loading the arena leaderboard…</div>`,
  );
  const { entries } = await api("/leaderboard");
  if (token !== state.routeToken) return;
  shell(
    "leaderboard",
    "Leaderboard",
    `${intro("A LITTLE FRIENDLY COMPETITION", "Earn your place.", "A community leaderboard built on completed missions. No shortcuts. No repeat XP.", '<a class="btn ghost small" href="#/settings">Leaderboard settings</a>')}<div class="notice">Participation is optional. Create an account and enable “Join the leaderboard” in Settings to share your username and score.</div>${entries.length ? `<div class="table-wrap"><table><thead><tr><th>Rank</th><th>Engineer</th><th>Missions</th><th>Total XP</th></tr></thead><tbody>${entries.map((e, i) => `<tr><td class="rank">${String(i + 1).padStart(2, "0")}</td><td><span class="avatar">${escape(initials(e.name))}</span>${escape(e.name)}${e.name === state.data.user.name ? " (you)" : ""}</td><td>${e.completed}</td><td class="xp-tag">${fmt.format(e.xp)} XP</td></tr>`).join("")}</tbody></table></div>` : `<div class="empty-state">${icon("trophy")}<h2>The first spot is still open.</h2><p>No public profiles yet. Complete a mission, then opt in to put your name on the board.</p><a class="btn primary" href="#/settings">Join the leaderboard ${icon("arrow")}</a></div>`}`,
  );
}
function renderSettings() {
  const { user } = state.data;
  shell(
    "settings",
    "Settings",
    `${intro("MAKE YOURSELF AT HOME", "Your arena. Your rules.", "A few preferences to make your learning space feel like yours.")}<div class="settings-grid"><section class="panel"><h2>Profile & preferences</h2><form id="settings-form"><div class="setting-row"><div><h3>${user.guest ? "You’re exploring as a guest" : escape(user.name)}</h3><p>${user.guest ? "Create an account to keep your progress across browsers. Your existing guest achievements will come with you." : "Your progress is saved to your account. Use your username and password to sign in on another device."}</p></div>${icon("user")}</div><label class="setting-row"><div><h3>Join the leaderboard</h3><p>Share your username, completed mission count, and XP with other learners. You can opt out at any time.</p></div><input type="checkbox" id="setting-public" ${user.public ? "checked" : ""} ${user.guest ? "disabled" : ""}></label><label class="setting-row"><div><h3>Compact mission cards</h3><p>Keep the mission library focused with a more compact layout.</p></div><input type="checkbox" id="setting-compact" ${user.compact ? "checked" : ""}></label><div class="settings-actions"><button class="btn primary" type="submit">Save preferences</button>${user.guest ? '<button class="btn" type="button" data-action="register">Create account</button><button class="btn ghost" type="button" data-action="login">Sign in</button>' : `<button class="btn ghost" type="button" data-action="logout">${icon("logout")}Sign out</button>`}</div></form></section><div><section class="panel"><div class="section-title"><h2>Private by default</h2>${icon("shield")}</div><ul class="info-list"><li>${icon("check")}Your learning history belongs to you.</li><li>${icon("check")}Your profile stays off the leaderboard until you opt in.</li><li>${icon("check")}Practice commands run in a simulator, never on the host.</li><li>${icon("check")}No third-party scripts or trackers.</li></ul><div class="settings-actions"><button class="btn small" data-action="export">${icon("download")}Export your progress</button></div></section></div></div>`,
  );
}
function openAuth(mode = "register") {
  const register = mode === "register";
  modal.innerHTML = `<div class="dialog-header"><h2>${register ? "Make your progress yours." : "Welcome back."}</h2><button class="icon-btn" data-action="close-modal" aria-label="Close dialog">${icon("x")}</button></div><p class="auth-copy">${register ? "Create an account. Keep your guest achievements. Pick up where you left off, anywhere." : "Sign in to continue your journey. Current guest progress is not merged into an existing account."}</p><form class="auth-form" id="auth-form" data-mode="${mode}"><label class="form-label" for="auth-username">Username</label><input id="auth-username" name="username" required minlength="3" maxlength="24" pattern="[A-Za-z][A-Za-z0-9_]{2,23}" autocomplete="username" autocapitalize="off" placeholder="e.g. swapnil_dev"><label class="form-label" for="auth-password">Password</label><input id="auth-password" name="password" type="password" required ${register ? 'minlength="12"' : ""} maxlength="128" autocomplete="${register ? "new-password" : "current-password"}" placeholder="${register ? "At least 12 characters" : "Your password"}"><p class="form-error" id="auth-error" role="alert"></p><button class="btn primary" type="submit">${register ? "Create account" : "Sign in"}${icon("arrow")}</button></form><div class="auth-switch">${register ? "Already have an account?" : "New around here?"} <button data-action="${register ? "login" : "register"}">${register ? "Sign in" : "Create an account"}</button></div>`;
  if (!modal.open) modal.showModal();
  $("#auth-username").focus();
}
async function route() {
  if (!state.data) return;
  const token = ++state.routeToken;
  const [page = "dashboard", id] = location.hash
    .replace(/^#\/?/, "")
    .split("/");
  state.busy = false;
  try {
    if (page === "arena") await renderArena(id, token);
    else if (page === "missions") renderMissions();
    else if (page === "activity") {
      await refresh();
      if (token === state.routeToken) renderActivity();
    } else if (page === "profile") renderProfile();
    else if (page === "leaderboard") await renderLeaderboard(token);
    else if (page === "settings") renderSettings();
    else renderDashboard();
    window.scrollTo(0, 0);
  } catch (error) {
    if (token !== state.routeToken) return;
    shell(
      page,
      "Connection interrupted",
      `<div class="empty-state">${icon("info")}<h2>Let’s try that again.</h2><p>${escape(error.message)}</p><button class="btn primary" data-action="retry">Retry</button><a class="btn ghost" href="#/dashboard">Overview</a></div>`,
    );
  }
}
async function submitCommand(form) {
  if (state.busy) return;
  const input = $("#command-input"),
    command = input.value.trim();
  if (!command) return;
  if (command === "clear") {
    $("#terminal-output").replaceChildren();
    input.value = "";
    return;
  }
  const lab = state.lab,
    token = state.routeToken;
  state.busy = true;
  input.disabled = true;
  $("button", form).disabled = true;
  try {
    const result = await api(`/labs/${lab.id}/commands`, { command });
    if (token !== state.routeToken) return;
    Object.assign(lab, {
      checks: result.checks,
      cwd: result.cwd,
      commands: result.commands,
    });
    lab.history.push({
      command,
      output: result.output,
      exit_code: result.exit_code,
    });
    lab.history = lab.history.slice(-40);
    state.historyIndex = lab.history.length;
    input.value = "";
    const output = $("#terminal-output");
    output.insertAdjacentHTML(
      "beforeend",
      terminalEntry({ command, ...result }),
    );
    while (output.children.length > 60) output.firstElementChild.remove();
    output.scrollTop = output.scrollHeight;
    $("#objectives").innerHTML = objectivesMarkup();
    $("#cwd").textContent = result.cwd;
    $("#command-count").textContent =
      `${result.commands} commands · saved automatically`;
    if (result.completed) {
      await refresh();
      if (token !== state.routeToken) return;
      $("#completion").innerHTML = completionMarkup();
      if (result.awarded_xp)
        toast(`Mission accomplished! +${result.awarded_xp} XP. Nicely done.`);
    }
  } catch (error) {
    toast(error.message, true);
  } finally {
    if (token === state.routeToken) {
      state.busy = false;
      input.disabled = false;
      $("button", form).disabled = false;
      input.focus({ preventScroll: true });
    }
  }
}

document.addEventListener("click", async (event) => {
  const target = event.target.closest("[data-action]");
  if (!target) return;
  const action = target.dataset.action;
  try {
    if (action === "menu") {
      const open = $(".sidebar").classList.toggle("open");
      target.setAttribute("aria-expanded", String(open));
    }
    if (action === "register" || action === "login") openAuth(action);
    if (action === "close-modal") modal.close();
    if (action === "retry") {
      await refresh();
      await route();
    }
    if (action === "search") {
      if (!location.hash.startsWith("#/missions")) {
        location.hash = "/missions";
        await new Promise((resolve) => setTimeout(resolve, 80));
      }
      $("#mission-search")?.focus();
    }
    if (action === "category") {
      state.category = target.dataset.value;
      renderMissions();
    }
    if (action === "saved-only") {
      state.savedOnly = !state.savedOnly;
      renderMissions();
    }
    if (action === "clear-filters") {
      Object.assign(state, {
        query: "",
        category: "All",
        difficulty: "All",
        savedOnly: false,
      });
      renderMissions();
    }
    if (action === "bookmark") {
      target.disabled = true;
      const id = target.dataset.id,
        saved = !state.data.bookmarks.includes(id);
      await api(`/bookmarks/${id}`, { saved });
      state.data.bookmarks = saved
        ? [...state.data.bookmarks, id]
        : state.data.bookmarks.filter((x) => x !== id);
      target.classList.toggle("saved", saved);
      target.setAttribute("aria-pressed", String(saved));
      target.setAttribute(
        "aria-label",
        `${saved ? "Unsave" : "Save"} ${missionById(id).title}`,
      );
      if (state.savedOnly && $("#mission-results")) updateMissionResults();
      toast(saved ? "Mission saved for later." : "Mission removed from saved.");
    }
    if (action === "clear-terminal") $("#terminal-output").replaceChildren();
    if (action === "hint") {
      target.disabled = true;
      const token = state.routeToken;
      const result = await api(`/labs/${state.lab.id}/hint`, {});
      if (token === state.routeToken) {
        Object.assign(state.lab, result);
        $("#hints").innerHTML = hintsMarkup();
      }
    }
    if (action === "reset") {
      modal.innerHTML = `<div class="dialog-header"><h2>Restart this practice lab?</h2><button class="icon-btn" data-action="close-modal" aria-label="Close dialog">${icon("x")}</button></div><p class="auth-copy">This clears this lab’s files, command history, and unfinished objectives. XP you already earned is kept.</p><button class="btn primary" data-action="confirm-reset">Restart lab</button> <button class="btn ghost" data-action="close-modal">Keep practising</button>`;
      modal.showModal();
    }
    if (action === "confirm-reset") {
      target.disabled = true;
      await api("/labs", { mission_id: state.lab.mission_id, reset: true });
      modal.close();
      await route();
      toast("Fresh workspace. You’ve got this.");
    }
    if (action === "logout") {
      await api("/auth/logout", {});
      state.csrf = "";
      await boot();
      toast("Signed out. Your account progress is saved.");
    }
    if (action === "export") {
      const data = await api("/export");
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }),
      );
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "shellarena-progress.json";
      anchor.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      toast("Progress exported.");
    }
  } catch (error) {
    toast(error.message, true);
  } finally {
    if (target.isConnected)
      target.disabled =
        action === "hint" &&
        state.lab.hints_used >= missionById(state.lab.mission_id).hint_count;
  }
});
document.addEventListener("input", (event) => {
  if (event.target.id === "mission-search") {
    state.query = event.target.value;
    updateMissionResults();
  }
});
document.addEventListener("change", (event) => {
  if (event.target.id === "difficulty") {
    state.difficulty = event.target.value;
    updateMissionResults();
  }
});
document.addEventListener("keydown", (event) => {
  if (
    (event.metaKey || event.ctrlKey) &&
    event.key.toLowerCase() === "k" &&
    !modal.open
  ) {
    event.preventDefault();
    $('[data-action="search"]')?.click();
  }
  if (event.key === "Escape") {
    $(".sidebar")?.classList.remove("open");
    $(".mobile-toggle")?.setAttribute("aria-expanded", "false");
  }
  if (
    event.target.id === "command-input" &&
    ["ArrowUp", "ArrowDown"].includes(event.key)
  ) {
    event.preventDefault();
    const entries = state.lab.history;
    state.historyIndex = Math.max(
      0,
      Math.min(
        entries.length,
        state.historyIndex + (event.key === "ArrowUp" ? -1 : 1),
      ),
    );
    event.target.value = entries[state.historyIndex]?.command || "";
  }
});
document.addEventListener("submit", async (event) => {
  const form = event.target;
  if (!["command-form", "auth-form", "settings-form"].includes(form.id)) return;
  event.preventDefault();
  if (form.id === "command-form") {
    await submitCommand(form);
    return;
  }
  const button = $('button[type="submit"]', form);
  button.disabled = true;
  try {
    if (form.id === "auth-form") {
      $("#auth-error").textContent = "";
      const data = await api(`/auth/${form.dataset.mode}`, {
        username: $("#auth-username").value,
        password: $("#auth-password").value,
      });
      state.csrf = data.csrf;
      await refresh();
      modal.close();
      await route();
      toast(`Welcome, ${data.user.name}. Your next level is waiting.`);
    } else {
      await api("/settings", {
        public: $("#setting-public").checked,
        compact: $("#setting-compact").checked,
      });
      await refresh();
      renderSettings();
      toast("Your preferences are saved.");
    }
  } catch (error) {
    if (form.id === "auth-form") $("#auth-error").textContent = error.message;
    else toast(error.message, true);
  } finally {
    button.disabled = false;
  }
});
window.addEventListener("hashchange", route);
window.addEventListener("offline", () =>
  toast("You’re offline. Reconnect before running your next command.", true),
);
async function boot() {
  try {
    const session = await api("/session", {});
    state.csrf = session.csrf;
    await refresh();
    await route();
  } catch (error) {
    app.innerHTML = `<div class="boot"><img src="/assets/mark.svg" width="48" height="48" alt=""><h1>Can’t reach your arena.</h1><p>${escape(error.message)}</p><button class="btn primary" id="reconnect">Reconnect</button></div>`;
    $("#reconnect").addEventListener("click", boot);
  }
}
boot();
