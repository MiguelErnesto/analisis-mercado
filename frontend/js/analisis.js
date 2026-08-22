import { cop, getJson, pct } from "./api.js";

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

function barChart(el, data, { key, label, onSelect }) {
  const box = el.getBoundingClientRect();
  const margin = { top: 8, right: 16, bottom: 32, left: 110 };
  const width = Math.max(280, box.width);
  const height = Math.max(220, box.height);
  el.innerHTML = "";
  const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${width} ${height}`);
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  const y = d3.scaleBand().domain(data.map((d) => d[label])).range([0, innerH]).padding(0.28);
  const x = d3.scaleLinear().domain([0, d3.max(data, (d) => d[key])]).nice().range([0, innerW]);
  let selected = null;

  g.append("g")
    .call(d3.axisLeft(y).tickSize(0))
    .call((ax) => ax.select(".domain").remove())
    .call((ax) => ax.selectAll("text").attr("fill", "#8a97ab").style("cursor", "pointer"));

  g.append("g")
    .attr("transform", `translate(0,${innerH})`)
    .call(d3.axisBottom(x).ticks(4).tickFormat((d) => d3.format(".2s")(d)).tickSizeOuter(0))
    .call((ax) => ax.selectAll("text").attr("fill", "#8a97ab"))
    .call((ax) => ax.selectAll("line,path").attr("stroke", "#2a3344"));

  const bars = g.selectAll("rect")
    .data(data)
    .join("rect")
    .attr("x", 0)
    .attr("y", (d) => y(d[label]))
    .attr("height", y.bandwidth())
    .attr("width", (d) => x(d[key]))
    .attr("fill", "#4aa3e8")
    .style("cursor", "pointer")
    .on("mousemove", (event, d) => {
      showTip(event, `${d[label]}<br>${cop.format(d[key])}<br>Clic para ver productos`);
    })
    .on("mouseleave", hideTip)
    .on("click", (event, d) => select(d[label]));

  function paint() {
    bars.attr("fill", (d) => (d[label] === selected ? "#4aa3e8" : "#2a5a7a"));
    bars.attr("fill-opacity", (d) => (d[label] === selected ? 1 : 0.7));
  }

  function select(name) {
    selected = name;
    paint();
    hideTip();
    if (onSelect) onSelect(name);
  }

  g.selectAll(".tick text").on("click", (event, name) => select(name));
}

function promoBars(el, impact) {
  const rows = [
    { label: "Sin promoción", value: impact.sin_promocion?.avg_revenue || 0 },
    { label: "Con promoción", value: impact.con_promocion?.avg_revenue || 0 },
  ];
  const box = el.getBoundingClientRect();
  const margin = { top: 8, right: 16, bottom: 32, left: 120 };
  const width = Math.max(280, box.width);
  const height = Math.max(220, box.height);
  el.innerHTML = "";
  const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${width} ${height}`);
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
  const y = d3.scaleBand().domain(rows.map((d) => d.label)).range([0, innerH]).padding(0.3);
  const x = d3.scaleLinear().domain([0, d3.max(rows, (d) => d.value)]).nice().range([0, innerW]);
  const color = { "Sin promoción": "#8a97ab", "Con promoción": "#e0b04a" };

  g.append("g")
    .call(d3.axisLeft(y).tickSize(0))
    .call((ax) => ax.select(".domain").remove())
    .call((ax) => ax.selectAll("text").attr("fill", "#8a97ab"));
  g.append("g")
    .attr("transform", `translate(0,${innerH})`)
    .call(d3.axisBottom(x).ticks(4).tickFormat((d) => d3.format(".2s")(d)).tickSizeOuter(0))
    .call((ax) => ax.selectAll("text").attr("fill", "#8a97ab"))
    .call((ax) => ax.selectAll("line,path").attr("stroke", "#2a3344"));

  g.selectAll("rect")
    .data(rows)
    .join("rect")
    .attr("y", (d) => y(d.label))
    .attr("height", y.bandwidth())
    .attr("width", (d) => x(d.value))
    .attr("fill", (d) => color[d.label])
    .on("mousemove", (event, d) => showTip(event, `${d.label}<br>${cop.format(d.value)} / día`))
    .on("mouseleave", hideTip);
}

function storeMap(el, stores) {
  const box = el.getBoundingClientRect();
  const width = Math.max(280, box.width);
  const height = Math.max(280, box.height);
  el.innerHTML = "";
  const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${width} ${height}`);
  const projection = d3.geoMercator()
    .center([-74.8, 6.2])
    .scale(width * 2.15)
    .translate([width / 2, height / 2 + 10]);
  const r = d3.scaleSqrt()
    .domain([0, d3.max(stores, (d) => d.revenue)])
    .range([8, 28]);

  svg.append("rect").attr("width", width).attr("height", height).attr("fill", "#121822");

  const lon0 = -79.0;
  const lon1 = -66.8;
  const lat0 = 12.5;
  const lat1 = -4.2;
  const corners = [
    [lon0, lat0],
    [lon1, lat0],
    [lon1, lat1],
    [lon0, lat1],
  ].map(projection);

  svg.append("polygon")
    .attr("points", corners.map((p) => p.join(",")).join(" "))
    .attr("fill", "#1b2431")
    .attr("stroke", "#2a3344");

  const g = svg.append("g");
  g.selectAll("circle")
    .data(stores)
    .join("circle")
    .attr("cx", (d) => projection([d.lon, d.lat])[0])
    .attr("cy", (d) => projection([d.lon, d.lat])[1])
    .attr("r", (d) => r(d.revenue))
    .attr("fill", "#4aa3e8")
    .attr("fill-opacity", 0.55)
    .attr("stroke", "#8ec8f4")
    .on("mousemove", (event, d) => {
      showTip(event, `${d.name}<br>${d.region}<br>${cop.format(d.revenue)}`);
    })
    .on("mouseleave", hideTip);

  g.selectAll("text")
    .data(stores)
    .join("text")
    .attr("x", (d) => projection([d.lon, d.lat])[0] + 12)
    .attr("y", (d) => projection([d.lon, d.lat])[1] + 4)
    .attr("fill", "#c5d0dc")
    .attr("font-size", 11)
    .text((d) => d.name.replace("Super ", ""));
}

async function showProducts(category) {
  const title = document.getElementById("cat-products-title");
  const body = document.getElementById("cat-products-body");
  title.textContent = `Más vendidos en ${category}`;
  body.innerHTML = `<tr><td colspan="4">Cargando…</td></tr>`;
  const rows = await getJson(`/api/sales/by-product?category=${encodeURIComponent(category)}`);
  body.innerHTML = rows.map((r, i) => `
    <tr class="${i === 0 ? "top" : ""}">
      <td>${i + 1}</td>
      <td>${r.name}</td>
      <td>${cop.format(r.revenue)}</td>
      <td>${r.qty.toLocaleString("es-CO")}</td>
    </tr>`).join("");
}

async function main() {
  const [cats, stores, promos] = await Promise.all([
    getJson("/api/sales/by-category"),
    getJson("/api/sales/by-region"),
    getJson("/api/promos/impact"),
  ]);

  barChart(document.getElementById("cat-chart"), cats, {
    key: "revenue",
    label: "category",
    onSelect: showProducts,
  });
  storeMap(document.getElementById("map-chart"), stores);
  promoBars(document.getElementById("promo-chart"), promos);

  const liftEl = document.getElementById("promo-lift");
  if (promos.lift == null) {
    liftEl.textContent = "Sin datos suficientes para calcular lift.";
  } else {
    const verb = promos.lift >= 0 ? "suben" : "bajan";
    liftEl.textContent =
      `Las ventas diarias ${verb} ${pct.format(promos.lift)} en días con promoción ` +
      `(n=${promos.con_promocion?.n_days ?? 0} vs ${promos.sin_promocion?.n_days ?? 0} días).`;
  }
}

main().catch((err) => {
  document.body.insertAdjacentHTML("beforeend", `<p class="wrap">${err.message}</p>`);
});
