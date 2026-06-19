/* global PLUGIN_REGISTRY */

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
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
    card.innerHTML = `
      <div class="card-header">
        <h3>${escapeHtml(plugin.name)}</h3>
        <span class="badge trust-${plugin.trust_level}">${plugin.trust_level}</span>
      </div>
      <p class="version">v${escapeHtml(plugin.version || "?")}</p>
      <p class="description">${escapeHtml(plugin.description || "")}</p>
      <div class="card-footer">
        <code>autoship plugin install ${escapeHtml(plugin.name)}</code>
      </div>
    `;
    container.appendChild(card);
  });
}

function filterPlugins() {
  const keyword = document.getElementById("search").value.toLowerCase();
  const level = document.getElementById("filter-trust").value;
  const filtered = PLUGIN_REGISTRY.plugins.filter((plugin) => {
    const matchesKeyword =
      !keyword ||
      (plugin.name && plugin.name.toLowerCase().includes(keyword)) ||
      (plugin.description && plugin.description.toLowerCase().includes(keyword));
    const matchesLevel = !level || plugin.trust_level === level;
    return matchesKeyword && matchesLevel;
  });
  renderPlugins(filtered);
}

document.getElementById("search").addEventListener("input", filterPlugins);
document.getElementById("filter-trust").addEventListener("change", filterPlugins);

renderPlugins(PLUGIN_REGISTRY.plugins);
