/* global PLUGIN_REGISTRY */

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function formatRating(rating) {
  if (!rating || !rating.count) return "No ratings";
  return `${rating.score.toFixed(1)} / 5 (${rating.count} ratings)`;
}

function publisherBadge(plugin) {
  const publisher = plugin.publisher;
  if (!publisher) return "";
  const verifiedClass = publisher.verified ? "verified" : "unverified";
  const label = publisher.verified ? "verified" : "unverified";
  return `<span class="publisher-badge ${verifiedClass}">${escapeHtml(publisher.id)} (${label})</span>`;
}

function auditStatusBadge(plugin) {
  const status = plugin.audit_status || "pending";
  return `<span class="audit-badge audit-${status}">${escapeHtml(status)}</span>`;
}

function renderTags(tags) {
  if (!Array.isArray(tags) || tags.length === 0) return "";
  return tags
    .map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`)
    .join("");
}

function renderCategories(categories) {
  if (!Array.isArray(categories) || categories.length === 0) return "";
  return categories
    .map((cat) => `<span class="category">${escapeHtml(cat)}</span>`)
    .join("");
}

function installCommand(plugin) {
  return `autoship plugin install ${escapeHtml(plugin.name)}`;
}

function renderPlugins(plugins) {
  const container = document.getElementById("plugin-grid");
  container.innerHTML = "";
  if (plugins.length === 0) {
    container.innerHTML = '<p class="empty">No plugins match your search.</p>';
    return;
  }
  plugins.forEach((plugin) => {
    const cmd = installCommand(plugin);
    const card = document.createElement("article");
    card.className = "card";
    card.tabIndex = 0;
    card.setAttribute("role", "button");
    card.innerHTML = `
      <div class="card-header">
        <h3>${escapeHtml(plugin.name)}</h3>
        <div class="badges">
          <span class="badge trust-${plugin.trust_level}">${plugin.trust_level}</span>
          ${auditStatusBadge(plugin)}
        </div>
      </div>
      <p class="version">v${escapeHtml(plugin.version || "?")}</p>
      <p class="description">${escapeHtml(plugin.description || "")}</p>
      <div class="card-meta">
        ${publisherBadge(plugin)}
      </div>
      <div class="card-meta">
        ${renderCategories(plugin.categories)}
      </div>
      <div class="card-meta">
        ${renderTags(plugin.tags)}
      </div>
      <div class="card-stats">
        <span title="Downloads">${plugin.downloads || 0} downloads</span>
        <span title="Rating">${formatRating(plugin.rating)}</span>
      </div>
      <div class="card-footer">
        <code id="cmd-${plugin.name}">${cmd}</code>
        <button class="copy-btn" data-cmd="${escapeHtml(plugin.name)}" aria-label="Copy install command">Copy</button>
      </div>
    `;
    card.addEventListener("click", (event) => {
      if (event.target.closest(".copy-btn")) {
        return;
      }
      openModal(plugin);
    });
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openModal(plugin);
      }
    });
    container.appendChild(card);
  });

  document.querySelectorAll(".copy-btn").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      const pluginName = button.dataset.cmd;
      const code = document.getElementById(`cmd-${pluginName}`).textContent;
      navigator.clipboard.writeText(code).then(() => {
        const original = button.textContent;
        button.textContent = "Copied!";
        setTimeout(() => (button.textContent = original), 1500);
      });
    });
  });
}

function openModal(plugin) {
  const modal = document.getElementById("plugin-modal");
  const body = document.getElementById("modal-body");
  body.innerHTML = `
    <div class="modal-header">
      <h2>${escapeHtml(plugin.name)} <span class="badge trust-${plugin.trust_level}">${plugin.trust_level}</span> ${auditStatusBadge(plugin)}</h2>
      <p class="version">v${escapeHtml(plugin.version || "?")}</p>
    </div>
    <p class="modal-description">${escapeHtml(plugin.description || "")}</p>
    <dl class="modal-details">
      <dt>Publisher</dt><dd>${publisherBadge(plugin) || "Unknown"}</dd>
      <dt>Audit status</dt><dd>${auditStatusBadge(plugin)}</dd>
      <dt>Maintainer</dt><dd>${escapeHtml(plugin.maintainer || "Unknown")}</dd>
      <dt>License</dt><dd>${escapeHtml(plugin.license || "Unknown")}</dd>
      <dt>Categories</dt><dd>${renderCategories(plugin.categories) || "—"}</dd>
      <dt>Tags</dt><dd>${renderTags(plugin.tags) || "—"}</dd>
      <dt>Downloads</dt><dd>${plugin.downloads || 0}</dd>
      <dt>Rating</dt><dd>${formatRating(plugin.rating)}</dd>
      ${plugin.homepage ? `<dt>Homepage</dt><dd><a href="${escapeHtml(plugin.homepage)}" target="_blank" rel="noopener">${escapeHtml(plugin.homepage)}</a></dd>` : ""}
      ${plugin.source_url ? `<dt>Source</dt><dd><a href="${escapeHtml(plugin.source_url)}" target="_blank" rel="noopener">${escapeHtml(plugin.source_url)}</a></dd>` : ""}
    </dl>
    <div class="modal-install">
      <code id="modal-cmd">${installCommand(plugin)}</code>
      <button class="copy-btn" id="modal-copy" aria-label="Copy install command">Copy</button>
    </div>
  `;
  modal.showModal();

  document.getElementById("modal-copy").addEventListener("click", () => {
    const code = document.getElementById("modal-cmd").textContent;
    navigator.clipboard.writeText(code).then(() => {
      const button = document.getElementById("modal-copy");
      const original = button.textContent;
      button.textContent = "Copied!";
      setTimeout(() => (button.textContent = original), 1500);
    });
  });
}

function closeModal() {
  const modal = document.getElementById("plugin-modal");
  modal.close();
}

function collectCategories() {
  const categories = new Set();
  PLUGIN_REGISTRY.plugins.forEach((plugin) => {
    (plugin.categories || []).forEach((cat) => categories.add(cat));
  });
  return Array.from(categories).sort();
}

function populateCategoryFilter() {
  const select = document.getElementById("filter-category");
  collectCategories().forEach((cat) => {
    const option = document.createElement("option");
    option.value = cat;
    option.textContent = cat;
    select.appendChild(option);
  });
}

function currentSort() {
  return document.getElementById("sort-by").value;
}

function sortPlugins(plugins) {
  const sort = currentSort();
  const sorted = [...plugins];
  if (sort === "downloads") {
    sorted.sort((a, b) => (b.downloads || 0) - (a.downloads || 0));
  } else if (sort === "rating") {
    sorted.sort((a, b) => {
      const ra = a.rating && a.rating.count ? a.rating.score : 0;
      const rb = b.rating && b.rating.count ? b.rating.score : 0;
      return rb - ra;
    });
  } else if (sort === "name") {
    sorted.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
  }
  return sorted;
}

function filterPlugins() {
  const keyword = document.getElementById("search").value.toLowerCase();
  const level = document.getElementById("filter-trust").value;
  const category = document.getElementById("filter-category").value;
  const filtered = PLUGIN_REGISTRY.plugins.filter((plugin) => {
    const matchesKeyword =
      !keyword ||
      (plugin.name && plugin.name.toLowerCase().includes(keyword)) ||
      (plugin.description && plugin.description.toLowerCase().includes(keyword)) ||
      (plugin.tags || []).some((tag) => tag.toLowerCase().includes(keyword));
    const matchesLevel = !level || plugin.trust_level === level;
    const matchesCategory = !category || (plugin.categories || []).includes(category);
    return matchesKeyword && matchesLevel && matchesCategory;
  });
  renderPlugins(sortPlugins(filtered));
}

document.getElementById("search").addEventListener("input", filterPlugins);
document.getElementById("filter-trust").addEventListener("change", filterPlugins);
document.getElementById("filter-category").addEventListener("change", filterPlugins);
document.getElementById("sort-by").addEventListener("change", filterPlugins);
document.getElementById("modal-close").addEventListener("click", closeModal);
document.getElementById("plugin-modal").addEventListener("click", (event) => {
  if (event.target.id === "plugin-modal") {
    closeModal();
  }
});

populateCategoryFilter();
filterPlugins();
