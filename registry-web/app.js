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

function renderPlugins(plugins) {
  const container = document.getElementById("plugin-grid");
  container.innerHTML = "";
  if (plugins.length === 0) {
    container.innerHTML = '<p class="empty">No plugins match your search.</p>';
    return;
  }
  plugins.forEach((plugin) => {
    const card = document.createElement("article");
    card.className = "card";
    card.tabIndex = 0;
    card.setAttribute("role", "button");
    card.innerHTML = `
      <div class="card-header">
        <h3>${escapeHtml(plugin.name)}</h3>
        <span class="badge trust-${plugin.trust_level}">${plugin.trust_level}</span>
      </div>
      <p class="version">v${escapeHtml(plugin.version || "?")}</p>
      <p class="description">${escapeHtml(plugin.description || "")}</p>
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
        <code>autoship plugin install ${escapeHtml(plugin.name)}</code>
      </div>
    `;
    card.addEventListener("click", () => openModal(plugin));
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openModal(plugin);
      }
    });
    container.appendChild(card);
  });
}

function openModal(plugin) {
  const modal = document.getElementById("plugin-modal");
  const body = document.getElementById("modal-body");
  body.innerHTML = `
    <div class="modal-header">
      <h2>${escapeHtml(plugin.name)} <span class="badge trust-${plugin.trust_level}">${plugin.trust_level}</span></h2>
      <p class="version">v${escapeHtml(plugin.version || "?")}</p>
    </div>
    <p class="modal-description">${escapeHtml(plugin.description || "")}</p>
    <dl class="modal-details">
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
      <code>autoship plugin install ${escapeHtml(plugin.name)}</code>
    </div>
  `;
  modal.showModal();
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
  renderPlugins(filtered);
}

document.getElementById("search").addEventListener("input", filterPlugins);
document.getElementById("filter-trust").addEventListener("change", filterPlugins);
document.getElementById("filter-category").addEventListener("change", filterPlugins);
document.getElementById("modal-close").addEventListener("click", closeModal);
document.getElementById("plugin-modal").addEventListener("click", (event) => {
  if (event.target.id === "plugin-modal") {
    closeModal();
  }
});

populateCategoryFilter();
renderPlugins(PLUGIN_REGISTRY.plugins);
