const $ = (selector) => document.querySelector(selector);
const formatKm = (meters) => `${(meters / 1000).toLocaleString(undefined, { maximumFractionDigits: 2 })} km`;

function render(record) {
  if (!record) { $("#empty-state").classList.remove("hidden"); $("#dashboard").classList.add("hidden"); return; }
  $("#empty-state").classList.add("hidden"); $("#dashboard").classList.remove("hidden");
  $("#scenario-title").textContent = record.scenario_id.replaceAll("_", " ");
  const badge = $("#validation-badge"); badge.textContent = record.validation_passed ? "VALIDATION PASS" : "VALIDATION FAIL"; badge.className = `badge ${record.validation_passed ? "pass" : "fail"}`;
  [["#orbit-altitude", record.orbit_altitude_m], ["#tether-length", record.tether_length_m], ["#upper-altitude", record.upper_altitude_m], ["#lower-altitude", record.lower_altitude_m]].forEach(([id, value]) => $(id).textContent = formatKm(value));
  $("#upper-label").textContent = formatKm(record.upper_altitude_m); $("#lower-label").textContent = formatKm(record.lower_altitude_m);
  $("#check-count").textContent = `${record.checks.length} CHECKS`;
  $("#checks").innerHTML = record.checks.map(check => `<li><span>${check.name.replaceAll("_", " ")}</span><span><small>residual ${Number(check.residual).toExponential(2)}</small> <b class="check-status">${check.passed ? "PASS" : "FAIL"}</b></span></li>`).join("");
  $("#limitations").innerHTML = record.limitations.map(item => `<li>${item}</li>`).join("");
}
function renderRecords(records) {
  $("#records").innerHTML = records.slice(0, 6).map(record => `<article class="record"><b>${record.scenario_id}</b><span>${formatKm(record.tether_length_m)} tether</span><span><small>${new Date(record.created_at_utc).toLocaleString()}</small></span><span><small>${record.experiment_id.slice(0, 8)}</small></span><span class="status-dot">${record.validation_passed ? "● PASS" : "● FAIL"}</span></article>`).join("");
}
async function load() { const response = await fetch("/api/experiments"); if (!response.ok) throw new Error("Could not load local experiment evidence."); const data = await response.json(); render(data.latest); renderRecords(data.records); }
function toast(message, error = false) { const node = $("#toast"); node.textContent = message; node.className = `toast show${error ? " error" : ""}`; setTimeout(() => node.className = "toast", 3600); }
$("#run-button").addEventListener("click", async () => { const button = $("#run-button"); button.disabled = true; button.querySelector("span").textContent = "Running baseline…"; try { const response = await fetch("/api/run-baseline", { method: "POST" }); const data = await response.json(); if (!response.ok) throw new Error(data.error || "Scenario execution failed."); await load(); toast(`Experiment ${data.record.experiment_id.slice(0, 8)} recorded.`); } catch (error) { toast(error.message, true); } finally { button.disabled = false; button.querySelector("span").textContent = "Run baseline scenario"; } });
$("#refresh-button").addEventListener("click", () => load().then(() => toast("Evidence log refreshed.")).catch(error => toast(error.message, true)));
load().catch(error => toast(error.message, true));
