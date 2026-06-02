const state = {
  opportunities: [],
};

const filters = {
  area: document.querySelector("#area-filter"),
  region: document.querySelector("#region-filter"),
  commune: document.querySelector("#commune-filter"),
  source: document.querySelector("#source-filter"),
  urgency: document.querySelector("#urgency-filter"),
};
const relevanceFilter = document.querySelector("#relevance-filter");
const textFilter = document.querySelector("#text-filter");
const sortFilter = document.querySelector("#sort-filter");
const RELEVANT_LEVELS = new Set(["Alta", "Media", "Baja"]);

function formatDate(value) {
  if (!value) return "No disponible";
  return new Intl.DateTimeFormat("es-CL", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function fillSelect(select, values) {
  [...new Set(values.filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, "es"))
    .forEach((value) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.append(option);
    });
}

function scoreClass(score) {
  if (score >= 80) return "high";
  if (score >= 60) return "medium";
  if (score >= 35) return "low";
  return "discarded";
}

function hasValidSourceUrl(opportunity) {
  if (opportunity.is_demo || !opportunity.source_url) return false;
  try {
    const url = new URL(opportunity.source_url);
    return url.protocol === "https:" || url.protocol === "http:";
  } catch {
    return false;
  }
}

function sourceKind(opportunity) {
  if (opportunity.source === "Municipalidad de Rancagua") return ["Municipal controlada", "controlled"];
  return ["Fuente pública activa", ""];
}

function operationalBadges(opportunity) {
  const badges = [[opportunity.match_level || "Sin nivel", scoreClass(opportunity.match_score)]];
  if (opportunity.is_new_since_last_run === true) badges.push(["NUEVA", "new"]);
  if (opportunity.urgency === "proximo") badges.push(["CIERRE PRÓXIMO", "closing"]);
  if (opportunity.human_feedback_action === "false_positive") {
    badges.push(["FALSO POSITIVO", "false-positive"]);
  } else if (opportunity.human_reviewed === true) {
    badges.push(["REVISADA", "reviewed"]);
  }
  if (opportunity.manual_review === true || opportunity.human_feedback_action === "review") {
    badges.push(["REVISAR", "review"]);
  }
  return badges;
}

function matchExplanation(opportunity) {
  const messages = [];
  if (opportunity.human_feedback_action === "false_positive") messages.push("Descartada por revisión humana.");
  else if (opportunity.human_feedback_action === "useful") messages.push("Marcada como útil por revisión humana.");
  else if (opportunity.human_feedback_action === "boost_priority") messages.push("Prioridad aumentada por feedback.");
  else if (opportunity.human_feedback_action === "lower_priority") messages.push("Prioridad reducida por feedback.");
  if (!messages.length && opportunity.match_level === "Alta") messages.push("Alta coincidencia con el perfil.");
  if (opportunity.urgency === "proximo") messages.push("Revisar pronto: cierre próximo.");
  return messages.join(" ");
}

function matchesRelevance(opportunity, relevance) {
  if (relevance === "all") return true;
  if (relevance === "discarded") return opportunity.match_level === "Descartada";
  if (relevance === "relevant") {
    return RELEVANT_LEVELS.has(opportunity.match_level) || opportunity.is_alertable === true;
  }
  return opportunity.match_level === relevance;
}

function matchesText(opportunity, query) {
  if (!query) return true;
  const searchable = [
    opportunity.title,
    opportunity.institution,
    opportunity.description,
    opportunity.source,
    opportunity.region,
    opportunity.commune,
    ...(opportunity.tags || []),
  ].join(" ").toLocaleLowerCase("es");
  return searchable.includes(query.toLocaleLowerCase("es").trim());
}

function sortedOpportunities(opportunities) {
  const items = [...opportunities];
  if (sortFilter.value === "closing") {
    return items.sort((a, b) => (a.closing_date || "9999-12-31").localeCompare(b.closing_date || "9999-12-31"));
  }
  if (sortFilter.value === "newest") {
    return items.sort((a, b) => String(b.detected_at || "").localeCompare(String(a.detected_at || "")));
  }
  return items.sort((a, b) => (b.match_score || 0) - (a.match_score || 0));
}

function renderEmptyState(list) {
  const emptyState = document.createElement("div");
  emptyState.className = "empty-state";
  emptyState.innerHTML = `
    <strong>No hay oportunidades recomendadas para este filtro.</strong>
    <span>Prueba limpiar los filtros o ver todas las oportunidades públicas.</span>
  `;
  list.append(emptyState);
}

function renderOpportunities() {
  const selected = Object.fromEntries(Object.entries(filters).map(([key, select]) => [key, select.value]));
  const filtered = sortedOpportunities(
    state.opportunities.filter((opportunity) =>
      matchesRelevance(opportunity, relevanceFilter.value) &&
      matchesText(opportunity, textFilter.value) &&
      Object.entries(selected).every(([key, value]) => !value || opportunity[key] === value),
    ),
  );
  const list = document.querySelector("#opportunities-list");
  const template = document.querySelector("#opportunity-template");
  list.replaceChildren();
  document.querySelector("#results-count").textContent =
    `${filtered.length} de ${state.opportunities.length} oportunidades visibles`;
  if (!filtered.length) {
    renderEmptyState(list);
    return;
  }

  filtered.forEach((opportunity) => {
    const card = template.content.cloneNode(true);
    const urgency = card.querySelector(".urgency-tag");
    const score = card.querySelector(".score-value");
    const [sourceLabel, sourceClass] = sourceKind(opportunity);
    const sourceBadge = card.querySelector(".source-kind-badge");
    sourceBadge.textContent = sourceLabel;
    sourceBadge.classList.toggle("controlled", sourceClass === "controlled");
    urgency.textContent = opportunity.urgency === "proximo" ? "Cierre próximo" : "Plazo normal";
    urgency.classList.toggle("normal", opportunity.urgency !== "proximo");
    card.querySelector(".opportunity-title").textContent = opportunity.title || "Convocatoria sin título";
    card.querySelector(".institution").textContent = opportunity.institution || "Institución no especificada";
    card.querySelector(".region").textContent = opportunity.region || "Región no especificada";
    card.querySelector(".commune").textContent = opportunity.commune || "Comuna no especificada";
    card.querySelector(".source").textContent = opportunity.source || "Fuente pública";
    card.querySelector(".description").textContent = opportunity.description || "Revisa la fuente oficial para conocer el detalle.";
    card.querySelector(".operational-meta").textContent =
      `Cierre: ${opportunity.closing_date || "No especificado"} · Área: ${opportunity.area || "No especificada"}`;
    card.querySelector(".match-explanation").textContent = matchExplanation(opportunity);
    score.textContent = `${opportunity.match_score || 0}%`;
    score.classList.add(scoreClass(opportunity.match_score || 0));
    operationalBadges(opportunity).forEach(([label, className]) => {
      const badge = document.createElement("span");
      badge.textContent = label;
      badge.className = `operational-badge ${className}`;
      card.querySelector(".operational-badges").append(badge);
    });
    (opportunity.tags || []).forEach((tag) => {
      const element = document.createElement("span");
      element.textContent = tag;
      card.querySelector(".tags").append(element);
    });

    const link = card.querySelector(".primary-button");
    if (hasValidSourceUrl(opportunity)) {
      link.href = opportunity.source_url;
      link.setAttribute("aria-label", `Ver fuente oficial: ${opportunity.title}`);
    } else {
      link.textContent = "Enlace demo";
      link.classList.add("disabled");
      link.removeAttribute("href");
      link.removeAttribute("target");
      link.removeAttribute("rel");
      link.setAttribute("aria-disabled", "true");
      card.querySelector(".demo-note").hidden = false;
    }
    list.append(card);
  });
}

function renderDataMode(opportunities) {
  const badge = document.querySelector(".prototype-badge");
  const realCount = opportunities.filter(({ is_demo: isDemo }) => isDemo === false).length;
  const isMostlyReal = realCount > opportunities.length / 2;
  badge.textContent = isMostlyReal ? "Captura local de Empleos Públicos" : "Datos de ejemplo / prototipo";
  badge.classList.toggle("real-data", isMostlyReal);
}

function renderMetrics(summary, lastRun) {
  const updated = formatDate(lastRun.finished_at);
  document.querySelector("#last-updated").textContent = updated;
  document.querySelector("#footer-last-updated").textContent = `Última actualización: ${updated}`;
  document.querySelector("#run-status").textContent = lastRun.message;
  document.querySelector("#sources-reviewed").textContent = summary.sources_reviewed;
  document.querySelector("#active-opportunities").textContent = summary.active_opportunities;
  document.querySelector("#new-opportunities-label").textContent =
    "first_seen_this_run" in summary ? "Nuevas desde última actualización" : "Nuevas oportunidades";
  document.querySelector("#new-opportunities").textContent = summary.new_opportunities;
  document.querySelector("#high-match").textContent = summary.high_match;
  document.querySelector("#closing-soon").textContent = summary.closing_soon;
}

async function initialize() {
  try {
    const [opportunitiesResponse, summaryResponse, lastRunResponse] = await Promise.all([
      fetch("data/opportunities.json"),
      fetch("data/summary.json"),
      fetch("data/last_run.json"),
    ]);
    if (![opportunitiesResponse, summaryResponse, lastRunResponse].every((response) => response.ok)) {
      throw new Error("No fue posible cargar uno o más archivos JSON.");
    }
    const [opportunities, summary, lastRun] = await Promise.all([
      opportunitiesResponse.json(),
      summaryResponse.json(),
      lastRunResponse.json(),
    ]);
    state.opportunities = opportunities;
    renderDataMode(opportunities);
    fillSelect(filters.area, opportunities.map(({ area }) => area));
    fillSelect(filters.region, opportunities.map(({ region }) => region));
    fillSelect(filters.commune, opportunities.map(({ commune }) => commune));
    fillSelect(filters.source, opportunities.map(({ source }) => source));
    renderMetrics(summary, lastRun);
    renderOpportunities();
  } catch (error) {
    const list = document.querySelector("#opportunities-list");
    list.innerHTML = `<div class="empty-state"><strong>No fue posible cargar el radar.</strong><span>${error.message} Sirve public mediante un servidor HTTP local.</span></div>`;
    document.querySelector("#results-count").textContent = "Error de carga";
  }
}

Object.values(filters).forEach((select) => select.addEventListener("change", renderOpportunities));
relevanceFilter.addEventListener("change", renderOpportunities);
sortFilter.addEventListener("change", renderOpportunities);
textFilter.addEventListener("input", renderOpportunities);
document.querySelector("#reset-filters").addEventListener("click", () => {
  Object.values(filters).forEach((select) => { select.value = ""; });
  relevanceFilter.value = "relevant";
  sortFilter.value = "priority";
  textFilter.value = "";
  renderOpportunities();
});

initialize();
