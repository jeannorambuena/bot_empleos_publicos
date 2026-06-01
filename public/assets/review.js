const STORAGE_KEY = "radar-laboral-publico-feedback-v1";
const OPTIONS = [
  ["useful", "Útil"],
  ["false_positive", "Falso positivo"],
  ["review", "Revisar"],
  ["boost_priority", "Subir prioridad"],
  ["lower_priority", "Bajar prioridad"],
];

function loadFeedback() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
  } catch {
    return {};
  }
}

function saveFeedback(feedback) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(feedback));
}

function isReviewCandidate(item) {
  const reasons = item.alert_reasons || [];
  return ["Alta", "Media"].includes(item.match_level) ||
    reasons.some((reason) => reason.includes("términos ambiguos"));
}

function exportPayload(feedback) {
  return JSON.stringify({
    version: 1,
    exported_at: new Date().toISOString(),
    source: "public-review-panel",
    items: Object.entries(feedback).map(([opportunityId, item]) => ({
      opportunity_id: opportunityId,
      action: item.action || item.label,
      reason: item.reason || undefined,
      created_at: item.created_at || item.updated_at,
      title: item.title || undefined,
      source_url: item.source_url || undefined,
    })),
  }, null, 2);
}

function render(items) {
  const feedback = loadFeedback();
  const list = document.querySelector("#review-list");
  list.replaceChildren();
  document.querySelector("#review-count").textContent = `${items.length} oportunidades para revisión`;

  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "review-card";
    card.innerHTML = `
      <p class="meta">${item.match_level} · ${item.match_score}% · ${item.source}</p>
      <h2></h2>
      <p class="institution"></p>
      <p class="reasons"></p>
      <div class="actions"></div>
    `;
    card.querySelector("h2").textContent = item.title;
    card.querySelector(".institution").textContent = item.institution;
    card.querySelector(".reasons").textContent = `Motivos: ${(item.alert_reasons || []).join(", ") || "-"}`;
    const actions = card.querySelector(".actions");
    OPTIONS.forEach(([value, label]) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = label;
      button.classList.toggle("selected", (feedback[item.id]?.action || feedback[item.id]?.label) === value);
      button.addEventListener("click", () => {
        feedback[item.id] = {
          action: value,
          title: item.title,
          source_url: item.source_url,
          created_at: new Date().toISOString(),
        };
        saveFeedback(feedback);
        render(items);
      });
      actions.append(button);
    });
    list.append(card);
  });
}

async function initialize() {
  const response = await fetch("data/opportunities.json");
  if (!response.ok) throw new Error("No fue posible cargar opportunities.json");
  const opportunities = await response.json();
  render(opportunities.filter(isReviewCandidate));
}

document.querySelector("#copy-feedback").addEventListener("click", async () => {
  await navigator.clipboard.writeText(exportPayload(loadFeedback()));
});

document.querySelector("#download-feedback").addEventListener("click", () => {
  const blob = new Blob([exportPayload(loadFeedback())], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "radar-laboral-feedback.json";
  link.click();
  URL.revokeObjectURL(link.href);
});

initialize().catch((error) => {
  document.querySelector("#review-list").textContent = error.message;
});
