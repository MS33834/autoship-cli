/* global PLUGIN_REGISTRY */

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function countBy(items) {
  const counts = {};
  items.forEach((item) => {
    counts[item] = (counts[item] || 0) + 1;
  });
  return counts;
}

function renderList(elementId, entries) {
  const list = document.getElementById(elementId);
  list.innerHTML = "";
  entries.forEach(([label, value]) => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${escapeHtml(label)}</span><span>${escapeHtml(String(value))}</span>`;
    list.appendChild(li);
  });
}

function renderDashboard() {
  const plugins = PLUGIN_REGISTRY.plugins;

  document.getElementById("metric-total").textContent = plugins.length;

  const verifiedPublishers = new Set();
  let totalDownloads = 0;
  plugins.forEach((plugin) => {
    totalDownloads += plugin.downloads || 0;
    const publisher = plugin.publisher;
    if (publisher && publisher.verified) {
      verifiedPublishers.add(publisher.id);
    }
  });
  document.getElementById("metric-verified-publishers").textContent = verifiedPublishers.size;
  document.getElementById("metric-downloads").textContent = totalDownloads.toLocaleString();

  const trustLevels = countBy(plugins.map((p) => p.trust_level || "unknown"));
  renderList(
    "trust-distribution",
    Object.entries(trustLevels).sort((a, b) => b[1] - a[1])
  );

  const categories = [];
  plugins.forEach((p) => (p.categories || []).forEach((c) => categories.push(c)));
  renderList(
    "category-distribution",
    Object.entries(countBy(categories)).sort((a, b) => b[1] - a[1])
  );

  const topDownloads = [...plugins]
    .sort((a, b) => (b.downloads || 0) - (a.downloads || 0))
    .slice(0, 5);
  const topDownloadsList = document.getElementById("top-downloads");
  topDownloadsList.innerHTML = "";
  topDownloads.forEach((plugin) => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${escapeHtml(plugin.name)}</span><span>${plugin.downloads || 0}</span>`;
    topDownloadsList.appendChild(li);
  });

  const topRated = plugins
    .filter((p) => p.rating && p.rating.count > 0)
    .sort((a, b) => b.rating.score - a.rating.score)
    .slice(0, 5);
  const topRatedList = document.getElementById("top-rated");
  topRatedList.innerHTML = "";
  topRated.forEach((plugin) => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${escapeHtml(plugin.name)}</span><span>${plugin.rating.score.toFixed(1)} (${plugin.rating.count})</span>`;
    topRatedList.appendChild(li);
  });
}

renderDashboard();
