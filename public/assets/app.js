const state = {
  opportunities: [],
};

const filters = {
  area: document.querySelector("#area-filter"),
  region: document.querySelector("#region-filter"),
  source: document.querySelector("#source-filter"),
  urgency: document.querySelector("#urgency-filter"),
};

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
  if (score >= 85) return "high";
  if (score >= 70) return "medium";
  return "low";
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

function renderOpportunities() {
  const selected = Object.fromEntries(
    Object.entries(filters).map(([key, select]) => [key, select.value]),
  );
  const filtered = state.opportunities.filter((opportunity) =>
    Object.entries(selected).every(
      ([key, value]) => !value || opportunity[key] === value,
    ),
  );
  const list = document.querySelector("#opportunities-list");
  const template = document.querySelector("#opportunity-template");

  list.replaceChildren();
  document.querySelector("#results-count").textContent =
    `${filtered.length} de ${state.opportunities.length} oportunidades`;

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
    score.textContent = `${opportunity.match_score}%`;
    score.classList.add(scoreClass(opportunity.match_score));

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

document.querySelector("#reset-filters").addEventListener("click", () => {
  Object.values(filters).forEach((select) => {
    select.value = "";
  });
  renderOpportunities();
});

initialize();
