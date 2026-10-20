"use strict";
// Only connects to this local HTTP server. Never submits broker orders.
// The dashboard intentionally does not expose a trade button.

const byId = (id) => document.getElementById(id);
const refreshButton = byId("refresh-button");
const number = new Intl.NumberFormat("en-US", {maximumFractionDigits: 6});
const clock = new Intl.DateTimeFormat("en-US", {
  hour: "numeric", minute: "2-digit", second: "2-digit", timeZoneName: "short"
});

function setText(id, value) {
  const node = byId(id);
  if (node) node.textContent = String(value);
}

function qualityLabel(status) {
  const labels = {
    DATA_READY: "Data ready",
    RESEARCH_ONLY: "Research only",
    SYNTHETIC: "Synthetic",
    STALE: "Stale"
  };
  return labels[status] || "Blocked";
}

function stateClass(status) {
  if (status === "DATA_READY") return "state-ready";
  if (status === "RESEARCH_ONLY" || status === "SYNTHETIC") return "state-warning";
  return "state-off";
}

function makeCell(text) {
  const cell = document.createElement("td");
  cell.textContent = String(text);
  return cell;
}

function setQuotes(quotes) {
  const target = byId("quotes-table");
  target.replaceChildren();
  if (!Array.isArray(quotes) || quotes.length === 0) {
    const row = document.createElement("tr");
    const td = makeCell("No trustworthy quote report is connected.");
    td.colSpan = 4;
    td.className = "empty";
    row.appendChild(td);
    target.appendChild(row);
    return;
  }
  for (const quote of quotes) {
    const row = document.createElement("tr");
    const symbol = makeCell(quote.symbol);
    symbol.className = "symbol";
    const source = makeCell(quote.source + " · " + quote.coverage);
    const prices = makeCell(number.format(quote.bid) + " / " + number.format(quote.ask));
    const status = document.createElement("td");
    const badge = document.createElement("span");
    badge.className = "state " + stateClass(quote.data_status);
    badge.textContent = qualityLabel(quote.data_status);
    status.appendChild(badge);
    row.append(symbol, source, prices, status);
    target.appendChild(row);
  }
}

function setComponents(components) {
  const target = byId("components");
  target.replaceChildren();
  if (!Array.isArray(components)) return;
  for (const item of components) {
    const row = document.createElement("div");
    row.className = "component";
    const mark = document.createElement("div");
    mark.className = "component-mark";
    mark.textContent = item.state === "IMPLEMENTED_OFFLINE" ? "✓" : "○";
    const content = document.createElement("div");
    content.className = "component-info";
    const heading = document.createElement("strong");
    heading.textContent = item.name;
    const subtext = document.createElement("p");
    subtext.textContent = item.description;
    content.append(heading, subtext);
    const state = document.createElement("span");
    state.className = "component-status" +
      (item.state === "IMPLEMENTED_OFFLINE" ? " implemented" : "");
    state.textContent = item.state === "IMPLEMENTED_OFFLINE"
      ? "Built · offline" :
      item.state === "DISABLED" ? "Off" : "Not connected";
    row.append(mark, content, state);
    target.appendChild(row);
  }
}

function update(data) {
  const market = data.market || {};
  const execution = data.execution || {};
  const performance = data.performance || {};
  const paperMonitor = data.paper_monitor || {};
  setText("paper-monitor-state", paperMonitor.status || "Not connected");
  setText("paper-monitor-note", paperMonitor.message ||
    "No private paper monitor report available");
  setText("paper-monitor-broker",
    "Brokerage state: " + (paperMonitor.brokerage_state || "UNKNOWN"));
  setText("paper-monitor-time", paperMonitor.checked_at_utc
    ? "Checked " + clock.format(new Date(paperMonitor.checked_at_utc))
    : "No verified heartbeat");
  setText("execution-state", execution.live_enabled ? "On" : "Disabled");
  setText("broker-state", execution.broker_connected ? "Yes" : "No");
  setText("feed-state", ({
    READ_ONLY: "Research",
    SYNTHETIC: "Synthetic",
    STALE: "Stale",
    INVALID: "Invalid",
    NO_FEED: "Disconnected",
  })[market.status] || "Offline");
  setText("market-status", market.status || "No feed");
  setText("feed-note", market.source_status || "No data available");
  setText("market-explainer", market.source_status ||
    "Quote reports are read-only and are never trade instructions.");
  setText("trade-count", performance.validated_trade_count || 0);
  setText("performance-note",
    "No verified forward-trading performance. Simulations and software tests " +
    "are not evidence that the strategy will make money.");
  setText("data-time", market.data_asof_utc
    ? "Data as of " + clock.format(new Date(market.data_asof_utc))
    : "Not connected");
  setText("last-updated", "Local status checked " +
    clock.format(new Date(data.generated_at_utc)));
  setQuotes(market.quotes);
  setComponents(data.components);
}

let active = false;
async function refresh() {
  if (active) return;
  active = true;
  refreshButton.disabled = true;
  try {
    const response = await fetch("/api/status", {cache: "no-store"});
    if (!response.ok) throw new Error("Local dashboard returned " + response.status);
    const status = await response.json();
    if (status.schema_version !== 1 ||
        !status.execution || status.execution.live_enabled !== false) {
      throw new Error("Unexpected or unsafe status payload");
    }
    update(status);
    setText("message", "");
  } catch (_err) {
    setText("message", "Unable to read the local status. No trade will be placed.");
    setText("feed-state", "Unavailable");
    setText("market-status", "Error");
  } finally {
    active = false;
    refreshButton.disabled = false;
  }
}
refreshButton.addEventListener("click", refresh);
refresh();
setInterval(() => {
  if (document.visibilityState === "visible") refresh();
}, 5000);
