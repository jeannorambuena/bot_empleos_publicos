const state = {
  opportunities: [],
};

const filters = {
  area: document.querySelector("#area-filter"),
  region: document.querySelector("#region-filter"),
  source: document.querySelector("#source-filter"),
  urgency: document.querySelector("#urgency-filter"),
};
const relevanceFilter = document.querySelector("#relevance-filter");
const RELEVANT_LEVELS = new Set(["Alta", "Media", "Baja"]);

function formatDate(value) {
  return new Intl.DateTimeFormat("es-CL", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function fillSelect(select, values) {
  [...new Set(values)].sort((a, b) => a.localeCompare(b, "es")).forEach((value) => {
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

function feedbackLabel(opportunity) {
  if (opportunity.human_feedback_action === "false_positive") return "Falso positivo";
  if (["boost_priority", "lower_priority"].includes(opportunity.human_feedback_action)) {
    return "Prioridad ajustada";
  }
  if (opportunity.human_reviewed) return "Revisada";
  return "";
}

function operationalBadges(opportunity) {
  const badges = [];
  if (opportunity.is_new_since_last_run === true) badges.push(["NUEVA", "new"]);
  if (opportunity.match_level === "Alta") badges.push(["ALTA", "high"]);
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
  if (opportunity.human_feedback_action === "false_positive") {
    messages.push("Descartada por revisión humana: falso positivo.");
  } else if (opportunity.human_feedback_action === "useful") {
    messages.push("Subió por feedback humano: marcada como útil.");
  } else if (opportunity.human_feedback_action === "boost_priority") {
    messages.push("Subió por feedback humano: prioridad ajustada.");
  } else if (opportunity.human_feedback_action === "lower_priority") {
    messages.push("Bajó por feedback humano: prioridad ajustada.");
  }
  if (opportunity.manual_review === true || opportunity.human_feedback_action === "review") {
    messages.push("Pendiente de revisión humana.");
  }
  if (!messages.length && opportunity.match_level === "Alta") {
    messages.push("Alta coincidencia por puntaje.");
  }
  if (opportunity.urgency === "proximo") {
    messages.push("Cierre próximo: revisar pronto.");
  }
  if (opportunity.human_feedback_reason) {
    messages.push(`Motivo humano: ${opportunity.human_feedback_reason}`);
  }
  return messages.join(" ");
}

function locationLabel(opportunity) {
  return [opportunity.region, opportunity.commune]
    .filter((value) => value && value !== "No especificada")
    .join(" / ") || "No especificada";
}

function renderDataMode(opportunities) {
  const badge = document.querySelector(".prototype-badge");
  const realCount = opportunities.filter(({ is_demo: isDemo }) => isDemo === false).length;
  const isMostlyReal = realCount > opportunities.length / 2;

  badge.textContent = isMostlyReal
    ? "Captura local de Empleos Públicos"
    : "Datos de ejemplo / prototipo";
  badge.classList.toggle("real-data", isMostlyReal);
}

function matchesRelevance(opportunity, relevance) {
  if (relevance === "all") return true;
  if (relevance === "discarded") return opportunity.match_level === "Descartada";
  if (relevance === "relevant") {
    return RELEVANT_LEVELS.has(opportunity.match_level) || opportunity.is_alertable === true;
  }
  return opportunity.match_level === relevance;
}

function renderOpportunities() {
  const selected = Object.fromEntries(
    Object.entries(filters).map(([key, select]) => [key, select.value]),
  );
  const filtered = state.opportunities.filter((opportunity) =>
    matchesRelevance(opportunity, relevanceFilter.value) &&
    Object.entries(selected).every(
      ([key, value]) => !value || opportunity[key] === value,
    ),
  );
  const list = document.querySelector("#opportunities-list");
  const template = document.querySelector("#opportunity-template");

  list.replaceChildren();
  document.querySelector("#results-count").textContent =
    `${filtered.length} de ${state.opportunities.length} oportunidades visibles`;

  if (!filtered.length) {
    const emptyState = document.createElement("p");
    emptyState.className = "empty-state";
    emptyState.textContent = "No hay oportunidades que coincidan con estos filtros.";
    list.append(emptyState);
    return;
  }

  filtered.forEach((opportunity) => {
    const card = template.content.cloneNode(true);
    const urgency = card.querySelector(".urgency-tag");
    const score = card.querySelector(".match-score strong");
    const feedbackBadge = card.querySelector(".feedback-badge");

    card.querySelector(".institution-type").textContent = opportunity.institution_type;
    urgency.textContent =
      opportunity.urgency === "proximo" ? "Cierre próximo" : "Plazo normal";
    urgency.classList.toggle("normal", opportunity.urgency !== "proximo");
    card.querySelector(".opportunity-title").textContent = opportunity.title;
    card.querySelector(".institution").textContent = opportunity.institution;
    card.querySelector(".region").textContent = opportunity.region;
    card.querySelector(".area").textContent = opportunity.area;
    card.querySelector(".source").textContent = opportunity.source;
    card.querySelector(".description").textContent = opportunity.description;
    const baseMatch =
      Number.isInteger(opportunity.base_match_score) && opportunity.base_match_level
        ? ` · Base: ${opportunity.base_match_score}% (${opportunity.base_match_level})`
        : "";
    card.querySelector(".operational-meta").textContent =
      `Ubicación: ${locationLabel(opportunity)} · Cierre: ${opportunity.closing_date || "No especificado"} · Nivel: ${opportunity.match_level || "No especificado"}${baseMatch}`;
    card.querySelector(".match-explanation").textContent = matchExplanation(opportunity);
    score.textContent = `${opportunity.match_score}%`;
    score.classList.add(scoreClass(opportunity.match_score));
    const feedbackText = feedbackLabel(opportunity);
    if (feedbackText) {
      feedbackBadge.textContent = feedbackText;
      feedbackBadge.hidden = false;
      feedbackBadge.classList.toggle("false-positive", opportunity.human_feedback_action === "false_positive");
    }
    operationalBadges(opportunity).forEach(([label, className]) => {
      const badge = document.createElement("span");
      badge.textContent = label;
      badge.className = `operational-badge ${className}`;
      card.querySelector(".operational-badges").append(badge);
    });

    opportunity.tags.forEach((tag) => {
      const tagElement = document.createElement("span");
      tagElement.textContent = tag;
      card.querySelector(".tags").append(tagElement);
    });

    const link = card.querySelector(".primary-button");
    const isRealLink = hasValidSourceUrl(opportunity);

    if (isRealLink) {
      link.href = opportunity.source_url;
      link.textContent = "Ver convocatoria";
      link.setAttribute("aria-label", `Ver convocatoria: ${opportunity.title}`);
    } else {
      link.textContent = "Enlace demo";
      link.classList.add("disabled");
      link.removeAttribute("href");
      link.removeAttribute("target");
      link.removeAttribute("rel");
      link.setAttribute("aria-disabled", "true");
      link.setAttribute("aria-label", `Enlace demo no disponible: ${opportunity.title}`);
      card.querySelector(".demo-note").hidden = false;
    }

    list.append(card);
  });
}

function renderMetrics(summary, lastRun) {
  document.querySelector("#last-updated").textContent = formatDate(lastRun.finished_at);
  document.querySelector("#run-status").textContent = lastRun.message;
  document.querySelector("#sources-reviewed").textContent = summary.sources_reviewed;
  document.querySelector("#active-opportunities").textContent =
    summary.active_opportunities;
  document.querySelector("#new-opportunities-label").textContent =
    "first_seen_this_run" in summary
      ? "Nuevas desde última actualización"
      : "Nuevas oportunidades";
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

    if (![opportunitiesResponse, summaryResponse, lastRunResponse].every((r) => r.ok)) {
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
    fillSelect(filters.source, opportunities.map(({ source }) => source));
    renderMetrics(summary, lastRun);
    renderOpportunities();
  } catch (error) {
    document.querySelector("#opportunities-list").innerHTML =
      `<p class="empty-state">${error.message} Sirve la carpeta public mediante un servidor HTTP local.</p>`;
    document.querySelector("#results-count").textContent = "Error de carga";
  }
}

Object.values(filters).forEach((select) => {
  select.addEventListener("change", renderOpportunities);
});
relevanceFilter.addEventListener("change", renderOpportunities);

document.querySelector("#reset-filters").addEventListener("click", () => {
  Object.values(filters).forEach((select) => {
    select.value = "";
  });
  relevanceFilter.value = "relevant";
  renderOpportunities();
});

initialize();
