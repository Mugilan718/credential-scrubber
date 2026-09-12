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

// ---------- Static icon labels ----------
// Buttons defined in index.html are left as empty shells (id + class only)
// so their icon+label markup lives in one place (icons.js) instead of being
// duplicated as raw inline SVG inside the Jinja template.

function initStaticIcons() {
  el("newProjectBtn").innerHTML = icon("plus", { size: 16 });
  el("editRulesBtn").innerHTML = `${icon("pencil")} Edit rules`;
  el("scanBtn").innerHTML = `${icon("play")} Run scan`;
  el("browseInputBtn").innerHTML = `${icon("folder-open")} Browse&hellip;`;
  el("browseOutputBtn").innerHTML = `${icon("folder-open")} Browse&hellip;`;
  el("saveProjectBtn").innerHTML = `${icon("check")} Create`;
  el("saveRulesBtn").innerHTML = `${icon("check")} Save rules`;
  el("closeSensitiveBtn").innerHTML = `${icon("eye-off")} Close`;
  el("sensitiveWarningHeading").innerHTML = `${icon("alert")} Warning — this view contains real secret values.`;
  el("emptyAddBtn").innerHTML = `${icon("plus")} Add your first project`;
  el("emptyStateIcon").innerHTML = icon("folder-git", { size: 40 });
  el("resultsEmptyIcon").innerHTML = icon("inbox", { size: 30 });
  el("ignoredEmptyIcon").innerHTML = icon("shield", { size: 30 });

  document.querySelector('.tab-btn[data-tab="results"]').innerHTML = `${icon("list")} Results`;
  document.querySelector('.tab-btn[data-tab="history"]').innerHTML = `${icon("clock")} Scan history`;
  document.querySelector('.tab-btn[data-tab="ignored"]').innerHTML = `${icon("shield")} Ignored findings`;
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
    li.innerHTML = `<div class="project-item-main">
                      <div class="project-item-name">${escapeHtml(p.name)}</div>
                      <div class="project-item-path">${escapeHtml(p.input_path)}</div>
                    </div>
                    <button class="btn-icon btn-delete-project" title="Delete project">${icon("trash", { size: 14 })}</button>`;
    li.onclick = () => selectProject(p.id);
    li.querySelector(".btn-delete-project").onclick = (ev) => {
      ev.stopPropagation();
      deleteProject(p.id, p.name);
    };
    list.appendChild(li);
  });
}

async function deleteProject(projectId, name) {
  if (!confirm(`Delete "${name}"? This removes its scan history and ignore list. The scanned folders themselves are untouched.`)) {
    return;
  }
  try {
    await api(`/api/projects/${projectId}`, { method: "DELETE" });
    if (state.activeProjectId === projectId) {
      state.activeProjectId = null;
    }
    await loadProjects();
    showToast("Project deleted.");
  } catch (e) {
    showToast("Failed to delete project: " + e.message, true);
  }
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
  el("resultsLoading").classList.add("hidden");
  el("resultsEmpty").classList.remove("hidden");
  el("scanSummary").classList.add("hidden");
  el("partialOutputWarning").classList.add("hidden");
  el("changedOnlyToggle").checked = false;

  await loadScanHistory(projectId);
  await loadIgnores(projectId);
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

// Native folder-browse buttons - the text field stays editable either way,
// so a picked path can still be tweaked, or typed/pasted directly if the
// dialog isn't wanted.
async function browseForFolder(inputId, btnId) {
  const btn = el(btnId);
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `${icon("spinner", { class: "spin" })} Waiting&hellip;`;
  try {
    const result = await api("/api/browse-folder", { method: "POST" });
    if (result.path) {
      el(inputId).value = result.path;
    }
  } catch (e) {
    el("projModalError").textContent = "Folder browser failed: " + e.message;
    el("projModalError").classList.remove("hidden");
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHtml;
  }
}

el("browseInputBtn").onclick = () => browseForFolder("projInput", "browseInputBtn");
el("browseOutputBtn").onclick = () => browseForFolder("projOutput", "browseOutputBtn");

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
  const changedOnly = el("changedOnlyToggle").checked;
  btn.disabled = true;
  btn.innerHTML = `${icon("spinner", { class: "spin" })} Scanning&hellip;`;
  el("resultsEmpty").classList.add("hidden");
  el("resultsTable").classList.add("hidden");
  el("resultsLoading").classList.remove("hidden");
  try {
    const result = await api(`/api/projects/${state.activeProjectId}/scan`, {
      method: "POST",
      body: JSON.stringify({ changed_only: changedOnly }),
    });
    state.activeScanId = result.scan_id;
    renderScanSummary(result);
    await loadReport(result.scan_id, true);
    el("resultsLoading").classList.add("hidden");
    await loadScanHistory(state.activeProjectId);
  } catch (e) {
    el("resultsLoading").classList.add("hidden");
    alert("Scan failed: " + e.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `${icon("play")} Run scan`;
  }
};

function renderScanSummary(result) {
  const box = el("scanSummary");
  box.classList.remove("hidden");
  box.innerHTML = `
    <div><strong>${result.files_scanned}</strong><span>files scanned</span></div>
    <div><strong>${result.total_redactions}</strong><span>redactions</span></div>
    ${result.changed_only ? '<div class="scan-mode-badge">changed files only (git)</div>' : ""}
  `;

  const warningBox = el("partialOutputWarning");
  if (result.partial_output) {
    warningBox.innerHTML = `<strong>Partial output</strong><p>${escapeHtml(result.partial_output_warning)}</p>`;
    warningBox.classList.remove("hidden");
  } else {
    warningBox.classList.add("hidden");
    warningBox.innerHTML = "";
  }
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

  const cols = "42px 1fr 100px 90px 160px 74px";
  let html = `<div class="results-table-header" style="grid-template-columns: ${cols};">
      <div>Line</div><div>File</div><div>Value</div><div>Rule</div><div>Key / Variable</div><div></div>
    </div>`;
  data.entries.forEach((e) => {
    const flagged = e.previously_ignored_value_changed;
    const ruleTitle = flagged
      ? `${e.rule} \u2014 previously ignored, but the value changed since; please review`
      : e.rule;
    html += `<div class="result-row${flagged ? " flagged-changed" : ""}" data-file="${escapeHtml(e.file)}" data-key="${escapeHtml(e.key || "")}" data-rule="${escapeHtml(e.rule)}" style="grid-template-columns: ${cols};">
        <div class="result-line-no">${e.line}</div>
        <div class="result-file" title="${escapeHtml(e.file)}">${escapeHtml(e.file)}</div>
        <div><span class="redaction-bar">REDACTED</span></div>
        <div class="result-rule" title="${escapeHtml(ruleTitle)}">${escapeHtml(e.rule)}${flagged ? ' <span class="changed-badge">\u26a0 changed</span>' : ""}</div>
        <div class="result-key">${escapeHtml(e.key || "\u2014")}</div>
        <div><button class="btn-ignore" title="Ignore this finding">${icon("x", { size: 14 })}</button></div>
      </div>`;
  });
  html += `<div class="reveal-sensitive-row">
      <button class="btn-secondary" id="revealSensitiveBtn">${icon("eye")} Reveal original values (sensitive)</button>
    </div>`;
  table.innerHTML = html;

  wireIgnoreButtons(table, data.entries);

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
  const cols = "42px 1fr 90px 1fr 74px";
  let html = `<div class="results-table-header" style="grid-template-columns: ${cols};">
      <div>Line</div><div>File</div><div>Rule</div><div>Before \u2192 After</div><div></div>
    </div>`;
  data.entries.forEach((e) => {
    const flagged = e.previously_ignored_value_changed;
    const ruleTitle = flagged
      ? `${e.rule} \u2014 previously ignored, but the value changed since; please review`
      : e.rule;
    html += `<div class="result-row${flagged ? " flagged-changed" : ""}" data-file="${escapeHtml(e.file)}" data-key="${escapeHtml(e.key || "")}" data-rule="${escapeHtml(e.rule)}" style="grid-template-columns: ${cols};">
        <div class="result-line-no">${e.line}</div>
        <div class="result-file" title="${escapeHtml(e.file)}">${escapeHtml(e.file)}</div>
        <div class="result-rule" title="${escapeHtml(ruleTitle)}">${escapeHtml(e.rule)}${flagged ? ' <span class="changed-badge">\u26a0 changed</span>' : ""}</div>
        <div class="sensitive-value">${escapeHtml(e.before || "")} <span class="redaction-bar" style="color:#5B6B66;background:none;">\u2192</span> ${escapeHtml(e.after || "")}</div>
        <div><button class="btn-ignore" title="Ignore this finding">${icon("x", { size: 14 })}</button></div>
      </div>`;
  });
  const sensitiveTable = el("sensitiveTable");
  sensitiveTable.innerHTML = html;
  wireIgnoreButtons(sensitiveTable, data.entries);
  el("sensitiveModalOverlay").classList.remove("hidden");
}

el("closeSensitiveBtn").onclick = () => el("sensitiveModalOverlay").classList.add("hidden");

// ---------- Ignored findings ----------

function wireIgnoreButtons(container, entries) {
  [...container.querySelectorAll(".result-row")].forEach((row, i) => {
    const entry = entries[i];
    const btn = row.querySelector(".btn-ignore");
    if (btn) btn.onclick = () => ignoreFinding(entry);
  });
}

async function ignoreFinding(entry) {
  try {
    await api(`/api/projects/${state.activeProjectId}/ignore`, {
      method: "POST",
      body: JSON.stringify({ file: entry.file, key: entry.key ?? null, rule: entry.rule }),
    });
    removeMatchingRows(entry);
    showToast("Finding ignored \u2014 won't reappear on the next scan.");
    await loadIgnores(state.activeProjectId);
  } catch (e) {
    showToast("Failed to ignore: " + e.message, true);
  }
}

function removeMatchingRows(entry) {
  const keyVal = entry.key || "";
  ["resultsTable", "sensitiveTable"].forEach((tableId) => {
    const table = el(tableId);
    if (!table) return;
    table.querySelectorAll(".result-row").forEach((row) => {
      if (row.dataset.file === entry.file && row.dataset.key === keyVal && row.dataset.rule === entry.rule) {
        row.remove();
      }
    });
  });
}

async function loadIgnores(projectId) {
  const ignores = await api(`/api/projects/${projectId}/ignore`);
  const list = el("ignoredList");
  el("ignoredEmpty").classList.toggle("hidden", ignores.length > 0);
  list.classList.toggle("hidden", ignores.length === 0);

  if (!ignores.length) {
    list.innerHTML = "";
    return;
  }

  const cols = "1fr 160px 180px 100px 110px 90px";
  let html = `<div class="results-table-header" style="grid-template-columns: ${cols};">
      <div>File</div><div>Key / Variable</div><div>Rule</div><div>Value tracked</div><div>Ignored on</div><div></div>
    </div>`;
  ignores.forEach((ig) => {
    const tracked = !!ig.value_hash;
    html += `<div class="result-row" style="grid-template-columns: ${cols};">
        <div class="result-file" title="${escapeHtml(ig.file)}">${escapeHtml(ig.file)}</div>
        <div class="result-key">${escapeHtml(ig.key || "\u2014")}</div>
        <div class="result-rule">${escapeHtml(ig.rule)}</div>
        <div class="result-key" title="${tracked ? "Will re-flag for review if the value changes" : "No value on record \u2014 will always re-flag for review, since a change can't be detected"}">${tracked ? "Yes" : "No"}</div>
        <div class="result-line-no">${new Date(ig.created_at).toLocaleDateString()}</div>
        <div><button class="btn-secondary btn-restore" data-id="${ig.id}" title="Restore this finding">${icon("undo", { size: 14 })}</button></div>
      </div>`;
  });
  list.innerHTML = html;

  list.querySelectorAll(".btn-restore").forEach((btn) => {
    btn.onclick = () => restoreIgnore(Number(btn.dataset.id));
  });
}

async function restoreIgnore(ignoreId) {
  try {
    await api(`/api/projects/${state.activeProjectId}/ignore/${ignoreId}`, { method: "DELETE" });
    showToast("Finding restored \u2014 will reappear on the next scan.");
    await loadIgnores(state.activeProjectId);
  } catch (e) {
    showToast("Failed to restore: " + e.message, true);
  }
}

function showToast(message, isError) {
  let toast = el("toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.className = "toast visible" + (isError ? " toast-error" : "");
  clearTimeout(window._toastTimer);
  window._toastTimer = setTimeout(() => toast.classList.remove("visible"), 2500);
}

// ---------- History ----------

async function loadScanHistory(projectId) {
  const scans = await api(`/api/projects/${projectId}/scans`);
  const list = el("historyList");
  if (!scans.length) {
    list.innerHTML = `<div class="results-empty"><div class="results-empty-icon">${icon("clock", { size: 30 })}</div><p>No scans yet.</p></div>`;
    return;
  }
  list.innerHTML = scans.map((s) => `
    <div class="history-row">
      <span>${new Date(s.timestamp).toLocaleString()}</span>
      <span>${s.files_scanned} files</span>
      <span class="history-row-count">${s.total_redactions} redactions</span>
      <button class="btn-secondary" onclick="viewHistoricalScan(${s.id})">View ${icon("chevron-right", { size: 14 })}</button>
    </div>
  `).join("");
}

async function viewHistoricalScan(scanId) {
  state.activeScanId = scanId;
  document.querySelector('[data-tab="results"]').click();
  await loadReport(scanId, false);
  el("scanSummary").classList.add("hidden");
  el("partialOutputWarning").classList.add("hidden");
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

initStaticIcons();
loadProjects();
