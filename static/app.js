const state = {
  projects: [],
  activeProjectId: null,
  activeScanId: null,
};

const el = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

// ---------- Projects ----------

async function loadProjects() {
  state.projects = await api("/api/projects");
  renderProjectList();
  if (state.projects.length && !state.activeProjectId) {
    selectProject(state.projects[0].id);
  } else if (!state.projects.length) {
    showEmptyState();
  }
}

function renderProjectList() {
  const list = el("projectList");
  list.innerHTML = "";
  state.projects.forEach((p) => {
    const li = document.createElement("li");
    li.className = "project-item" + (p.id === state.activeProjectId ? " active" : "");
    li.innerHTML = `<div class="project-item-name">${escapeHtml(p.name)}</div>
                    <div class="project-item-path">${escapeHtml(p.input_path)}</div>`;
    li.onclick = () => selectProject(p.id);
    list.appendChild(li);
  });
}

function showEmptyState() {
  el("emptyState").classList.remove("hidden");
  el("projectView").classList.add("hidden");
}

async function selectProject(projectId) {
  state.activeProjectId = projectId;
  const project = state.projects.find((p) => p.id === projectId);
  if (!project) return;

  el("emptyState").classList.add("hidden");
  el("projectView").classList.remove("hidden");
  el("projectName").textContent = project.name;
  el("projectPath").textContent = project.input_path + "  \u2192  " + project.output_path;

  renderProjectList();
  el("resultsTable").classList.add("hidden");
  el("resultsEmpty").classList.remove("hidden");
  el("scanSummary").classList.add("hidden");

  await loadScanHistory(projectId);
}

// ---------- New project modal ----------

el("newProjectBtn").onclick = () => openProjectModal();
el("emptyAddBtn").onclick = () => openProjectModal();
el("cancelProjectBtn").onclick = () => closeProjectModal();

function openProjectModal() {
  el("projName").value = "";
  el("projInput").value = "";
  el("projOutput").value = "";
  el("projModalError").classList.add("hidden");
  el("projectModalOverlay").classList.remove("hidden");
}
function closeProjectModal() {
  el("projectModalOverlay").classList.add("hidden");
}

el("saveProjectBtn").onclick = async () => {
  const name = el("projName").value.trim();
  const input_path = el("projInput").value.trim();
  const output_path = el("projOutput").value.trim();
  try {
    const project = await api("/api/projects", {
      method: "POST",
      body: JSON.stringify({ name, input_path, output_path }),
    });
    closeProjectModal();
    await loadProjects();
    selectProject(project.id);
  } catch (e) {
    el("projModalError").textContent = e.message;
    el("projModalError").classList.remove("hidden");
  }
};

// ---------- Rules editor ----------

el("editRulesBtn").onclick = async () => {
  const rules = await api(`/api/projects/${state.activeProjectId}/rules`);
  el("rulesKeyPatterns").value = (rules.key_patterns || []).join("\n");
  el("rulesPlaceholders").value = (rules.placeholder_allowlist || []).join("\n");
  el("rulesModalError").classList.add("hidden");
  el("rulesModalOverlay").classList.remove("hidden");
  window._currentRulesFull = rules; // preserve value_patterns/code_patterns untouched
};

el("cancelRulesBtn").onclick = () => el("rulesModalOverlay").classList.add("hidden");

el("saveRulesBtn").onclick = async () => {
  const full = window._currentRulesFull || {};
  full.key_patterns = el("rulesKeyPatterns").value.split("\n").map((s) => s.trim()).filter(Boolean);
  full.placeholder_allowlist = el("rulesPlaceholders").value.split("\n").map((s) => s.trim()).filter(Boolean);
  try {
    await api(`/api/projects/${state.activeProjectId}/rules`, {
      method: "PUT",
      body: JSON.stringify(full),
    });
    el("rulesModalOverlay").classList.add("hidden");
  } catch (e) {
    el("rulesModalError").textContent = e.message;
    el("rulesModalError").classList.remove("hidden");
  }
};

// ---------- Scanning ----------

el("scanBtn").onclick = async () => {
  const btn = el("scanBtn");
  btn.disabled = true;
  btn.textContent = "Scanning\u2026";
  try {
    const result = await api(`/api/projects/${state.activeProjectId}/scan`, { method: "POST" });
    state.activeScanId = result.scan_id;
    renderScanSummary(result);
    await loadReport(result.scan_id, true);
    await loadScanHistory(state.activeProjectId);
  } catch (e) {
    alert("Scan failed: " + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Run scan";
  }
};

function renderScanSummary(result) {
  const box = el("scanSummary");
  box.classList.remove("hidden");
  box.innerHTML = `
    <div><strong>${result.files_scanned}</strong><span>files scanned</span></div>
    <div><strong>${result.total_redactions}</strong><span>redactions</span></div>
  `;
}

// ---------- Report rendering ----------

async function loadReport(scanId, animate) {
  const data = await api(`/api/scans/${scanId}/report`);
  el("resultsEmpty").classList.toggle("hidden", data.entries.length > 0);
  const table = el("resultsTable");
  table.classList.toggle("hidden", data.entries.length === 0);

  if (data.entries.length === 0) {
    table.innerHTML = "";
    return;
  }

  let html = `<div class="results-table-header" style="grid-template-columns: 42px 1fr 100px 90px 160px;">
      <div>Line</div><div>File</div><div>Value</div><div>Rule</div><div>Key / Variable</div>
    </div>`;
  data.entries.forEach((e, i) => {
    html += `<div class="result-row" style="grid-template-columns: 42px 1fr 100px 90px 160px;">
        <div class="result-line-no">${e.line}</div>
        <div class="result-file" title="${escapeHtml(e.file)}">${escapeHtml(e.file)}</div>
        <div><span class="redaction-bar">REDACTED</span></div>
        <div class="result-rule">${escapeHtml(e.rule)}</div>
        <div class="result-key">${escapeHtml(e.key || "\u2014")}</div>
      </div>`;
  });
  html += `<div class="reveal-sensitive-row">
      <button class="btn-secondary" id="revealSensitiveBtn">Reveal original values (sensitive)</button>
    </div>`;
  table.innerHTML = html;

  el("revealSensitiveBtn").onclick = () => openSensitiveModal(scanId);

  if (animate) {
    setTimeout(() => {
      table.querySelectorAll(".redaction-bar").forEach((b, i) => {
        b.classList.add("animate");
        b.style.animationDelay = (i * 30) + "ms";
      });
    }, 30);
  }
}

async function openSensitiveModal(scanId) {
  const data = await api(`/api/scans/${scanId}/sensitive`);
  let html = `<div class="results-table-header">
      <div>Line</div><div>File</div><div>Rule</div><div>Before \u2192 After</div>
    </div>`;
  data.entries.forEach((e) => {
    html += `<div class="result-row" style="grid-template-columns: 42px 1fr 90px 1fr;">
        <div class="result-line-no">${e.line}</div>
        <div class="result-file" title="${escapeHtml(e.file)}">${escapeHtml(e.file)}</div>
        <div class="result-rule">${escapeHtml(e.rule)}</div>
        <div class="result-key">${escapeHtml(e.before || "")} <span class="redaction-bar" style="color:#5B6B66;background:none;">\u2192</span> ${escapeHtml(e.after || "")}</div>
      </div>`;
  });
  el("sensitiveTable").innerHTML = html;
  el("sensitiveModalOverlay").classList.remove("hidden");
}

el("closeSensitiveBtn").onclick = () => el("sensitiveModalOverlay").classList.add("hidden");

// ---------- History ----------

async function loadScanHistory(projectId) {
  const scans = await api(`/api/projects/${projectId}/scans`);
  const list = el("historyList");
  if (!scans.length) {
    list.innerHTML = `<p class="results-empty">No scans yet.</p>`;
    return;
  }
  list.innerHTML = scans.map((s) => `
    <div class="history-row">
      <span>${new Date(s.timestamp).toLocaleString()}</span>
      <span>${s.files_scanned} files</span>
      <span class="history-row-count">${s.total_redactions} redactions</span>
      <button class="btn-secondary" onclick="viewHistoricalScan(${s.id})">View</button>
    </div>
  `).join("");
}

async function viewHistoricalScan(scanId) {
  state.activeScanId = scanId;
  document.querySelector('[data-tab="results"]').click();
  await loadReport(scanId, false);
  el("scanSummary").classList.add("hidden");
}
window.viewHistoricalScan = viewHistoricalScan;

// ---------- Tabs ----------

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.onclick = () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    el("tab-" + btn.dataset.tab).classList.add("active");
  };
});

// ---------- Utilities ----------

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// Render the redaction-bar visual wherever a value equals the mask token
function postProcessMask() {
  document.querySelectorAll(".result-row").forEach((row) => {});
}

loadProjects();
