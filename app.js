const CATEGORIES = {
  all: { label: "Tout" },
  cinema: { label: "Cinéma" },
  exposition: { label: "Expositions" },
  theatre: { label: "Théâtre" },
  spectacle: { label: "Spectacles" },
  conference: { label: "Conférences" },
};
const SINGULAR = {
  cinema: "Cinéma", exposition: "Exposition", theatre: "Théâtre",
  spectacle: "Spectacle", conference: "Conférence",
};
const ENDING_DAYS = 14;

const state = { cat: "all", q: "", arr: "", free: false, ending: false };
let events = [];
let weekStart = new Date();

const $ = (id) => document.getElementById(id);
const fmtDay = new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "long" });
const fmtDayYear = new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "long", year: "numeric" });
const fmtFull = new Intl.DateTimeFormat("fr-FR", { dateStyle: "full", timeStyle: "short" });

const parseDay = (s) => new Date(`${s}T12:00:00`);
// Intl écrit « 1 octobre » ; l'usage français est « 1er octobre ».
const premier = (s) => s.replace(/(^|\s)1(\s)/, "$11er$2");
const day = (s) => premier(fmtDay.format(parseDay(s)));
const dayYear = (s) => premier(fmtDayYear.format(parseDay(s)));
const norm = (s) => (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function arrLabel(code) {
  const n = parseInt(String(code).slice(-2), 10);
  if (!code || !String(code).startsWith("75") || !n || n > 20) return "";
  return n === 1 ? "1er" : `${n}e`;
}

function isEndingSoon(ev) {
  if (ev.category === "cinema") return false;
  const days = (parseDay(ev.end_date) - weekStart) / 864e5;
  return days <= ENDING_DAYS && ev.end_date !== ev.start_date;
}

function dateText(ev) {
  if (ev.category === "cinema") return `Sortie le ${dayYear(ev.start_date)}`;
  if (ev.start_date === ev.end_date) return `Le ${day(ev.start_date)}`;
  if (parseDay(ev.start_date) <= weekStart) return `Jusqu'au ${dayYear(ev.end_date)}`;
  return `Du ${day(ev.start_date)} au ${dayYear(ev.end_date)}`;
}

function matches(ev) {
  if (state.cat !== "all" && ev.category !== state.cat) return false;
  if (state.arr && ev.arrondissement !== state.arr) return false;
  if (state.free && !ev.free) return false;
  if (state.ending && !isEndingSoon(ev)) return false;
  if (state.q) {
    const hay = norm(`${ev.title} ${ev.venue} ${ev.description} ${(ev.tags || []).join(" ")}`);
    if (!norm(state.q).split(/\s+/).every((w) => hay.includes(w))) return false;
  }
  return true;
}

function card(ev) {
  const arr = arrLabel(ev.arrondissement);
  const badges = [
    ev.free ? `<span class="badge free">Gratuit</span>` : "",
    isEndingSoon(ev) ? `<span class="badge soon">Bientôt fini</span>` : "",
  ].join("");
  const img = ev.image
    ? `<div class="img"><img src="${escapeHtml(ev.image)}" alt="" loading="lazy" onerror="this.parentNode.remove()"></div>`
    : "";
  return `
    <article class="card" style="--c: var(--${ev.category})">
      ${img}
      <div class="body">
        <div class="meta-top"><span class="cat">${SINGULAR[ev.category]}</span>${badges}</div>
        <h2><a href="${escapeHtml(ev.url)}" target="_blank" rel="noopener">${escapeHtml(ev.title)}</a></h2>
        <p class="venue">${escapeHtml(ev.venue)}${arr ? ` <span class="arr">· ${arr}</span>` : ""}</p>
        ${ev.description ? `<p class="desc">${escapeHtml(ev.description)}</p>` : ""}
        <div class="facts">
          <span><b>${escapeHtml(dateText(ev))}</b></span>
          ${ev.schedule ? `<span>${escapeHtml(ev.schedule)}</span>` : ""}
          ${ev.price && !ev.free ? `<span>${escapeHtml(ev.price)}</span>` : ""}
        </div>
      </div>
    </article>`;
}

function renderTabs() {
  const counts = { all: events.length };
  for (const ev of events) counts[ev.category] = (counts[ev.category] || 0) + 1;
  $("tabs").innerHTML = Object.entries(CATEGORIES)
    .map(([key, { label }]) => `
      <button class="tab" role="tab" data-cat="${key}" aria-selected="${state.cat === key}">
        ${label}<span class="n">${counts[key] || 0}</span>
      </button>`)
    .join("");
}

function render() {
  const list = events.filter(matches);
  $("grid").innerHTML = list.map(card).join("");
  $("empty").hidden = list.length > 0;
  $("count").textContent = `${list.length} sortie${list.length > 1 ? "s" : ""}`;
  document.querySelectorAll(".tab").forEach((t) => t.setAttribute("aria-selected", t.dataset.cat === state.cat));
}

function initFilters() {
  const arrs = [...new Set(events.map((e) => e.arrondissement).filter(arrLabel))].sort();
  $("arr").insertAdjacentHTML("beforeend", arrs.map((a) => `<option value="${a}">${arrLabel(a)} </option>`).join(""));

  $("tabs").addEventListener("click", (e) => {
    const tab = e.target.closest(".tab");
    if (tab) { state.cat = tab.dataset.cat; render(); }
  });
  $("q").addEventListener("input", (e) => { state.q = e.target.value.trim(); render(); });
  $("arr").addEventListener("change", (e) => { state.arr = e.target.value; render(); });
  $("free").addEventListener("change", (e) => { state.free = e.target.checked; render(); });
  $("ending").addEventListener("change", (e) => { state.ending = e.target.checked; render(); });
}

async function main() {
  try {
    const res = await fetch("data/events.json", { cache: "no-cache" });
    const data = await res.json();
    events = data.events || [];
    weekStart = parseDay(data.week.start);
    $("week").textContent = `Semaine du ${day(data.week.start)} au ${dayYear(data.week.end)}`;
    $("updated").textContent = `Mis à jour le ${premier(fmtFull.format(new Date(data.generated_at)))}.`;
    renderTabs();
    initFilters();
    render();
  } catch (err) {
    $("week").textContent = "Données indisponibles";
    $("empty").hidden = false;
    $("empty").textContent = "Impossible de charger la sélection de la semaine.";
    console.error(err);
  }
}

main();
