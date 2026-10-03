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

// ---------- Theme (dark mode) ----------
// Session-only by design (sessionStorage, not localStorage) - the toggle
// doesn't need to survive a full app restart, just page reloads.

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  const btn = el("themeToggleBtn");
  if (btn) {
    btn.innerHTML = icon(theme === "dark" ? "sun" : "moon", { size: 16 });
    btn.title = theme === "dark" ? "Switch to light mode" : "Switch to dark mode";
  }
}

function initTheme() {
  // index.html's inline head script already set data-theme before first
  // paint (avoiding a flash of the wrong theme) - just sync the button.
  const current = document.documentElement.getAttribute("data-theme") || "light";
  applyTheme(current);
  el("themeToggleBtn").onclick = () => {
    const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
    sessionStorage.setItem("theme", next);
    applyTheme(next);
  };
}

// ---------- Static icon labels ----------
// Buttons defined in index.html are left as empty shells (id + class only)
// so their icon+label markup lives in one place (icons.js) instead of being
// duplicated as raw inline SVG inside the Jinja template.

function initStaticIcons() {
  el("newProjectBtn").innerHTML = icon("plus", { size: 16 });
  el("editFoldersBtn").innerHTML = `${icon("folder-open")} Edit folders`;
  el("editRulesBtn").innerHTML = `${icon("pencil")} Edit rules`;
  el("scanBtn").innerHTML = `${icon("play")} Run scan`;
  el("browseInputBtn").innerHTML = `${icon("folder-open")} Browse&hellip;`;
  el("browseOutputBtn").innerHTML = `${icon("folder-open")} Browse&hellip;`;
  el("saveProjectBtn").innerHTML = `${icon("check")} Create`;
  el("saveRulesBtn").innerHTML = `${icon("check")} Save rules`;
  el("loadTreeBtn").innerHTML = `${icon("folder-open")} Choose files to include`;
  el("saveFolderFilterBtn").innerHTML = `${icon("check")} Save`;
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
  addProjectTree.reset();
  el("fileTreeContainer").classList.add("hidden");
  const loadBtn = el("loadTreeBtn");
  loadBtn.classList.remove("hidden");
  loadBtn.disabled = false;
  loadBtn.innerHTML = `${icon("folder-open")} Choose files to include`;
  el("projectModalOverlay").classList.remove("hidden");
}
function closeProjectModal() {
  el("projectModalOverlay").classList.add("hidden");
}

el("saveProjectBtn").onclick = async () => {
  const name = el("projName").value.trim();
  const input_path = el("projInput").value.trim();
  const output_path = el("projOutput").value.trim();
  // If the tree was never opened, nothing is excluded - every file is
  // included, identical to today's default (scan everything).
  const excluded_paths = addProjectTree.isLoaded() ? addProjectTree.getExcludedPaths() : [];
  try {
    const project = await api("/api/projects", {
      method: "POST",
      body: JSON.stringify({ name, input_path, output_path, excluded_paths }),
    });
    closeProjectModal();
    await loadProjects();
    selectProject(project.id);
  } catch (e) {
    el("projModalError").textContent = e.message;
    el("projModalError").classList.remove("hidden");
  }
};

// ---------- Edit folders (Phase 2) ----------

el("editFoldersBtn").onclick = async () => {
  const project = state.projects.find((p) => p.id === state.activeProjectId);
  if (!project) return;
  el("folderFilterModalError").classList.add("hidden");
  try {
    const [treeResult, excludedResult] = await Promise.all([
      api(`/api/file-tree?path=${encodeURIComponent(project.input_path)}`),
      api(`/api/projects/${project.id}/excluded-paths`),
    ]);
    const excluded = new Set(excludedResult.excluded_paths);
    const checked = treeResult.files.filter((p) => !isPathExcluded(p, excluded));
    editFoldersTree.load(treeResult.files, checked);
    el("folderFilterModalOverlay").classList.remove("hidden");
  } catch (e) {
    showToast("Failed to load folder list: " + e.message, true);
  }
};

el("cancelFolderFilterBtn").onclick = () => el("folderFilterModalOverlay").classList.add("hidden");

el("saveFolderFilterBtn").onclick = async () => {
  const excluded_paths = editFoldersTree.getExcludedPaths();
  try {
    await api(`/api/projects/${state.activeProjectId}/excluded-paths`, {
      method: "PUT",
      body: JSON.stringify({ excluded_paths }),
    });
    el("folderFilterModalOverlay").classList.add("hidden");
    showToast("Folder selection saved — applies on the next scan.");
  } catch (e) {
    el("folderFilterModalError").textContent = e.message;
    el("folderFilterModalError").classList.remove("hidden");
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

// ---------- Folder-filter tree (Phase 2) ----------
// Pure tree-building/checkbox-propagation logic, then a small reusable
// widget factory so the same code backs both the "add project" modal's
// tree and the "Edit folders" modal's tree, each with its own independent
// state (only one is ever open at a time, but keeping them separate
// avoids any chance of one bleeding into the other).

function buildFileTree(paths) {
  const root = { type: "folder", name: "", path: "", children: [] };
  paths.forEach((filePath) => {
    const parts = filePath.split("/");
    let node = root;
    let acc = "";
    parts.forEach((part, i) => {
      acc = acc ? `${acc}/${part}` : part;
      if (i === parts.length - 1) {
        node.children.push({ type: "file", name: part, path: acc });
      } else {
        let child = node.children.find((c) => c.type === "folder" && c.name === part);
        if (!child) {
          child = { type: "folder", name: part, path: acc, children: [] };
          node.children.push(child);
        }
        node = child;
      }
    });
  });
  sortTreeChildren(root);
  return root;
}

function sortTreeChildren(node) {
  node.children.sort((a, b) => {
    if (a.type !== b.type) return a.type === "folder" ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
  node.children.forEach((c) => { if (c.type === "folder") sortTreeChildren(c); });
}

function collectFilePaths(node, out = []) {
  if (node.type === "file") { out.push(node.path); return out; }
  node.children.forEach((c) => collectFilePaths(c, out));
  return out;
}

/**
 * Mirrors engine.scan_project()'s own exclusion check: a stored entry may
 * be an exact file path, OR a collapsed FOLDER path (see
 * computeExcludedPaths() above) - any file under that folder is excluded
 * too, by prefix, not just an exact match.
 */
function isPathExcluded(filePath, excludedSet) {
  if (excludedSet.has(filePath)) return true;
  for (const ex of excludedSet) {
    if (filePath.startsWith(ex + "/")) return true;
  }
  return false;
}

function findNodeByPath(node, path) {
  if (node.path === path) return node;
  for (const c of node.children) {
    const found = findNodeByPath(c, path);
    if (found) return found;
  }
  return null;
}

function getNodeCheckState(node, checkedPaths) {
  if (node.type === "file") return checkedPaths.has(node.path) ? "checked" : "unchecked";
  const paths = collectFilePaths(node);
  const checkedCount = paths.filter((p) => checkedPaths.has(p)).length;
  if (checkedCount === 0) return "unchecked";
  if (checkedCount === paths.length) return "checked";
  return "indeterminate";
}

function setNodeChecked(node, checked, checkedPaths) {
  const next = new Set(checkedPaths);
  const paths = node.type === "file" ? [node.path] : collectFilePaths(node);
  paths.forEach((p) => { if (checked) next.add(p); else next.delete(p); });
  return next;
}

/**
 * The exclusion list actually sent to the backend: a fully-unchecked
 * folder contributes just its OWN path (not every file inside it) - this
 * is what lets engine.scan_project() prune that whole directory from the
 * walk entirely (see its `dirs[:] = ...` filtering), rather than still
 * walking into a huge excluded folder and checking every individual file
 * against the set. An indeterminate folder recurses into its children
 * instead, since some of them are still included.
 */
function computeExcludedPaths(node, checkedPaths, out = []) {
  if (node.type === "file") {
    if (!checkedPaths.has(node.path)) out.push(node.path);
    return out;
  }
  const state = getNodeCheckState(node, checkedPaths);
  if (state === "unchecked") {
    out.push(node.path);
  } else if (state === "indeterminate") {
    node.children.forEach((c) => computeExcludedPaths(c, checkedPaths, out));
  }
  return out;
}

function createFileTreeWidget({ listId, summaryId, selectAllId, deselectAllId }) {
  let tree = null;
  let checkedPaths = new Set();
  let expanded = new Set();

  function render() {
    const list = el(listId);
    if (!list) return;
    if (!tree) { list.innerHTML = ""; return; }
    let html = "";
    tree.children.forEach((c) => { html += rowHtml(c, 0); });
    list.innerHTML = html || `<p class="modal-hint" style="padding: var(--space-3) 0 0;">No files found.</p>`;
    list.querySelectorAll('[data-indeterminate="true"]').forEach((cb) => { cb.indeterminate = true; });
    updateSummary();
  }

  function rowHtml(node, depth) {
    const state = getNodeCheckState(node, checkedPaths);
    const indent = `padding-left:${depth * 16 + 12}px`;
    if (node.type === "file") {
      return `<div class="tree-row tree-file" style="${indent}">
        <span class="tree-toggle-spacer"></span>
        <input type="checkbox" class="tree-checkbox" data-path="${escapeHtml(node.path)}" ${state === "checked" ? "checked" : ""} />
        ${icon("file", { size: 13, class: "tree-icon" })}
        <span class="tree-name" title="${escapeHtml(node.name)}">${escapeHtml(node.name)}</span>
      </div>`;
    }
    const isExpanded = expanded.has(node.path);
    const fileCount = collectFilePaths(node).length;
    let html = `<div class="tree-row tree-folder" style="${indent}">
      <button type="button" class="tree-toggle" data-path="${escapeHtml(node.path)}" aria-expanded="${isExpanded}" aria-label="${isExpanded ? "Collapse" : "Expand"} ${escapeHtml(node.name)}">
        ${icon("chevron-right", { size: 13 })}
      </button>
      <input type="checkbox" class="tree-checkbox" data-path="${escapeHtml(node.path)}" ${state === "checked" ? "checked" : ""} ${state === "indeterminate" ? 'data-indeterminate="true"' : ""} />
      ${icon("folder-open", { size: 13, class: "tree-icon" })}
      <span class="tree-name" title="${escapeHtml(node.name)}">${escapeHtml(node.name)}</span>
      <span class="tree-count">${fileCount} file${fileCount === 1 ? "" : "s"}</span>
    </div>`;
    if (isExpanded) {
      node.children.forEach((c) => { html += rowHtml(c, depth + 1); });
    }
    return html;
  }

  function updateSummary() {
    const summaryEl = el(summaryId);
    if (!summaryEl) return;
    if (!tree) { summaryEl.textContent = ""; return; }
    const total = collectFilePaths(tree).length;
    summaryEl.textContent = `${checkedPaths.size} of ${total} files selected`;
  }

  const listEl = el(listId);
  listEl.addEventListener("click", (e) => {
    const toggleBtn = e.target.closest(".tree-toggle");
    if (!toggleBtn) return;
    const path = toggleBtn.dataset.path;
    if (expanded.has(path)) expanded.delete(path);
    else expanded.add(path);
    render();
  });
  listEl.addEventListener("change", (e) => {
    const checkbox = e.target.closest(".tree-checkbox");
    if (!checkbox || !tree) return;
    const node = findNodeByPath(tree, checkbox.dataset.path);
    if (!node) return;
    checkedPaths = setNodeChecked(node, checkbox.checked, checkedPaths);
    render();
  });
  if (selectAllId) {
    el(selectAllId).onclick = () => {
      if (!tree) return;
      checkedPaths = setNodeChecked(tree, true, checkedPaths);
      render();
    };
  }
  if (deselectAllId) {
    el(deselectAllId).onclick = () => {
      if (!tree) return;
      checkedPaths = setNodeChecked(tree, false, checkedPaths);
      render();
    };
  }

  return {
    load(allPaths, initialCheckedPaths) {
      tree = buildFileTree(allPaths);
      checkedPaths = new Set(initialCheckedPaths);
      expanded = new Set();
      render();
    },
    reset() {
      tree = null;
      checkedPaths = new Set();
      expanded = new Set();
      render();
    },
    isLoaded: () => !!tree,
    getAllPaths: () => (tree ? collectFilePaths(tree) : []),
    getCheckedPaths: () => new Set(checkedPaths),
    getExcludedPaths: () => {
      if (!tree) return [];
      const out = [];
      tree.children.forEach((c) => computeExcludedPaths(c, checkedPaths, out));
      return out;
    },
  };
}

const addProjectTree = createFileTreeWidget({
  listId: "fileTreeList", summaryId: "fileTreeSummary",
  selectAllId: "treeSelectAllBtn", deselectAllId: "treeDeselectAllBtn",
});
const editFoldersTree = createFileTreeWidget({
  listId: "editFileTreeList", summaryId: "editFileTreeSummary",
  selectAllId: "editTreeSelectAllBtn", deselectAllId: "editTreeDeselectAllBtn",
});

el("loadTreeBtn").onclick = async () => {
  const inputPath = el("projInput").value.trim();
  if (!inputPath) {
    el("projModalError").textContent = "Enter the folder to scan first.";
    el("projModalError").classList.remove("hidden");
    return;
  }
  const btn = el("loadTreeBtn");
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `${icon("spinner", { class: "spin" })} Loading&hellip;`;
  try {
    const result = await api(`/api/file-tree?path=${encodeURIComponent(inputPath)}`);
    addProjectTree.load(result.files, result.files); // everything checked by default
    el("fileTreeContainer").classList.remove("hidden");
    btn.classList.add("hidden"); // the tree's own Select/Deselect all take over from here
  } catch (e) {
    el("projModalError").textContent = e.message;
    el("projModalError").classList.remove("hidden");
    btn.disabled = false;
    btn.innerHTML = originalHtml;
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
  if (data.unavailable) {
    el("sensitiveTable").innerHTML = `<div class="results-empty"><p>${escapeHtml(data.warning)}</p></div>`;
    el("sensitiveModalOverlay").classList.remove("hidden");
    return;
  }
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
        <div class="sensitive-value">${escapeHtml(e.before || "")} <span class="redaction-arrow">\u2192</span> ${escapeHtml(e.after || "")}</div>
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
  if (!confirm("This will restore the original, unmasked value the next time this project is scanned. Only do this if you're certain this is NOT a real secret.")) {
    return;
  }
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
        <div><button class="btn-secondary btn-restore" data-id="${ig.id}" title="Restore redaction — re-masks this value on the next scan">${icon("undo", { size: 14 })}</button></div>
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

initTheme();
initStaticIcons();
loadProjects();
