import { cop, getJson, parseDate, pct, unid } from "./api.js";

const tip = d3.select("body").append("div").attr("class", "tooltip");

function showTip(event, html) {
  tip.html(html)
    .style("display", "block")
    .style("left", `${event.pageX + 12}px`)
    .style("top", `${event.pageY - 10}px`);
}

function hideTip() {
  tip.style("display", "none");
}

function setKpi(id, value, cls) {
  const el = document.getElementById(id);
  el.textContent = value;
  el.classList.remove("pos", "neg");
  if (cls) el.classList.add(cls);
}

function styleAxis(ax) {
  ax.selectAll("text").attr("fill", "#8a97ab");
  ax.selectAll("line,path").attr("stroke", "#2a3344");
}

function lineChart(el, series, metric) {
  const isQty = metric === "qty";
  const tKey = isQty ? "y_true_qty" : "y_true";
  const pKey = isQty ? "y_pred_qty" : "y_pred";
  const fmt = (v) => (v == null ? "—" : isQty ? `${unid.format(Math.round(v))} und.` : cop.format(v));
  const box = el.getBoundingClientRect();
  const margin = { top: 16, right: 16, bottom: 32, left: 64 };
  const width = Math.max(320, box.width);
  const height = Math.max(240, box.height);
  el.innerHTML = "";
  const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${width} ${height}`);
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  const x0 = d3.scaleTime()
    .domain(d3.extent(series, (d) => d.date))
    .range([0, innerW]);
  const y0 = d3.scaleLinear()
    .domain([0, d3.max(series, (d) => Math.max(d[tKey] || 0, d[pKey] || 0)) * 1.08])
    .nice()
    .range([innerH, 0]);
  let x = x0.copy();
  let y = y0.copy();

  svg.append("defs")
    .append("clipPath")
    .attr("id", "trend-clip")
    .append("rect")
    .attr("width", innerW)
    .attr("height", innerH);

  const gx = g.append("g").attr("transform", `translate(0,${innerH})`);
  const gy = g.append("g");
  const grid = g.append("g").attr("stroke", "#2a3344").attr("stroke-opacity", 0.8);
  const plot = g.append("g").attr("clip-path", "url(#trend-clip)");

  const actual = series.filter((d) => d[tKey] != null);
  const pred = series.filter((d) => d[pKey] != null && d.kind !== "forecast");
  const future = series.filter((d) => d.kind === "forecast");
  const bridge = future.length && pred.length ? [pred[pred.length - 1], ...future] : future;

  const pathOf = (key) =>
    d3.line()
      .x((d) => x(d.date))
      .y((d) => y(d[key]))
      .defined((d) => d[key] != null);

  const pActual = plot.append("path").datum(actual).attr("fill", "none").attr("stroke", "#d7dee8").attr("stroke-width", 1.6);
  const pPred = plot.append("path").datum(pred).attr("fill", "none").attr("stroke", "#4aa3e8").attr("stroke-width", 1.6);
  const pFc = plot.append("path").datum(bridge).attr("fill", "none").attr("stroke", "#4ecf9a").attr("stroke-width", 1.8).attr("stroke-dasharray", "5 4");

  function draw() {
    gx.call(d3.axisBottom(x).ticks(7).tickSizeOuter(0)).call(styleAxis);
    gy.call(d3.axisLeft(y).ticks(5).tickFormat((d) => d3.format(".2s")(d)).tickSizeOuter(0)).call(styleAxis);
    grid.selectAll("line")
      .data(y.ticks(5))
      .join("line")
      .attr("x1", 0)
      .attr("x2", innerW)
      .attr("y1", (d) => y(d))
      .attr("y2", (d) => y(d));
    pActual.attr("d", pathOf(tKey));
    pPred.attr("d", pathOf(pKey));
    pFc.attr("d", pathOf(pKey));
  }

  draw();

  const zoom = d3.zoom()
    .scaleExtent([1, 40])
    .extent([[0, 0], [innerW, innerH]])
    .translateExtent([[0, 0], [innerW, innerH]])
    .on("zoom", (event) => {
      x = event.transform.rescaleX(x0);
      y = event.transform.rescaleY(y0);
      draw();
    });

  const overlay = g.append("rect")
    .attr("width", innerW)
    .attr("height", innerH)
    .attr("fill", "transparent")
    .style("cursor", "grab")
    .call(zoom)
    .on("dblclick.zoom", null)
    .on("dblclick", () => overlay.call(zoom.transform, d3.zoomIdentity))
    .on("mousemove", (event) => {
      const [px] = d3.pointer(event);
      const t = x.invert(px);
      const nearest = d3.least(series, (d) => Math.abs(d.date - t));
      if (!nearest) return;
      overlay.style("cursor", event.buttons ? "grabbing" : "grab");
      const bits = [`<strong>${nearest.date.toISOString().slice(0, 10)}</strong>`];
      if (nearest.y_true != null) bits.push(`Real: ${cop.format(nearest.y_true)}`);
      if (nearest.y_true_qty != null) bits.push(`Unidades vendidas: ${unid.format(Math.round(nearest.y_true_qty))}`);
      if (nearest.y_pred != null) bits.push(`Predicho: ${cop.format(nearest.y_pred)}`);
      if (nearest.y_pred_qty != null) bits.push(`Unidades predichas: ${unid.format(Math.round(nearest.y_pred_qty))}`);
      showTip(event, bits.join("<br>"));
    })
    .on("mouseleave", hideTip);

  const reset = document.getElementById("zoom-reset");
  const zoomIn = document.getElementById("zoom-in");
  const zoomOut = document.getElementById("zoom-out");
  const step = (k) => overlay.transition().duration(200).call(zoom.scaleBy, k);
  if (reset) reset.onclick = () => overlay.transition().duration(200).call(zoom.transform, d3.zoomIdentity);
  if (zoomIn) zoomIn.onclick = () => step(1.4);
  if (zoomOut) zoomOut.onclick = () => step(1 / 1.4);
}

let trendCache = [];
let horizon = 7;
let metric = "revenue";
let filterCatalog = { categories: [], products: [] };

function queryParams() {
  const cat = document.getElementById("filter-category").value;
  const pid = document.getElementById("filter-product").value;
  const q = new URLSearchParams();
  if (pid) q.set("product_id", pid);
  else if (cat) q.set("category", cat);
  const s = q.toString();
  return s ? `?${s}` : "";
}

function fillProductOptions() {
  const cat = document.getElementById("filter-category").value;
  const sel = document.getElementById("filter-product");
  const prev = sel.value;
  const items = filterCatalog.products.filter((p) => !cat || p.category === cat);
  sel.innerHTML = `<option value="">Todos los productos</option>`
    + items.map((p) => `<option value="${p.id}">${p.name}</option>`).join("");
  if ([...sel.options].some((o) => o.value === prev)) sel.value = prev;
}

async function loadSeries() {
  const q = queryParams();
  const sep = q ? "&" : "?";
  const [trend, metrics] = await Promise.all([
    getJson(`/api/sales/trend${q}`),
    getJson(`/api/model/metrics${q}${sep}target=${metric}`),
  ]);
  const maeTxt = metric === "qty"
    ? `${unid.format(Math.round(metrics.mae))} und.`
    : cop.format(metrics.mae);
  document.getElementById("m-r2").textContent = `R² ${metrics.r2.toFixed(3)}`;
  document.getElementById("m-mae").textContent = `MAE ${maeTxt}`;
  document.getElementById("m-mape").textContent = `MAPE ${(metrics.mape * 100).toFixed(1)}%`;
  trendCache = trend.map((d) => ({
    date: parseDate(d.date),
    y_true: d.y_true,
    y_pred: d.y_pred,
    y_true_qty: d.y_true_qty,
    y_pred_qty: d.y_pred_qty,
    kind: "hist",
  }));
  await renderForecast();
}

async function renderForecast() {
  const fc = await getJson(`/api/forecast?horizon=${horizon}${queryParams().replace("?", "&")}`);
  const byDate = new Map(trendCache.map((d) => [d.date.toISOString().slice(0, 10), { ...d }]));
  for (const row of fc) {
    byDate.set(row.date, {
      date: parseDate(row.date),
      y_true: null,
      y_pred: row.y_pred,
      y_true_qty: null,
      y_pred_qty: row.y_pred_qty,
      kind: "forecast",
    });
  }
  const series = [...byDate.values()].sort((a, b) => a.date - b.date);
  lineChart(document.getElementById("trend-chart"), series, metric);
}

async function main() {
  const [kpis, filters] = await Promise.all([
    getJson("/api/kpis"),
    getJson("/api/filters"),
  ]);

  setKpi("kpi-ventas", cop.format(kpis.ventas_totales));
  setKpi("kpi-unidades", unid.format(kpis.unidades_totales));
  if (kpis.yoy == null) {
    setKpi("kpi-yoy", "n/d");
  } else {
    setKpi("kpi-yoy", pct.format(kpis.yoy), kpis.yoy >= 0 ? "pos" : "neg");
  }
  setKpi("kpi-ticket", cop.format(kpis.ticket_promedio));

  filterCatalog = filters;
  const catSel = document.getElementById("filter-category");
  catSel.innerHTML = `<option value="">Todas las categorías</option>`
    + filters.categories.map((c) => `<option value="${c}">${c}</option>`).join("");
  fillProductOptions();
  catSel.addEventListener("change", () => {
    fillProductOptions();
    loadSeries();
  });
  document.getElementById("filter-product").addEventListener("change", loadSeries);

  document.querySelectorAll("[data-horizon]").forEach((btn) => {
    btn.addEventListener("click", () => {
      horizon = Number(btn.dataset.horizon);
      document.querySelectorAll("[data-horizon]").forEach((b) => b.classList.toggle("on", b === btn));
      renderForecast();
    });
  });
  document.querySelectorAll("[data-metric]").forEach((btn) => {
    btn.addEventListener("click", () => {
      metric = btn.dataset.metric;
      document.querySelectorAll("[data-metric]").forEach((b) => b.classList.toggle("on", b === btn));
      loadSeries();
    });
  });

  await loadSeries();
}

main().catch((err) => {
  document.body.insertAdjacentHTML("beforeend", `<p class="wrap">${err.message}</p>`);
});
