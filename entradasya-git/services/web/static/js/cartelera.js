/* Cartelera del cliente: buscador, destacados, filas que se deslizan (Esta semana, Más vendidos)
   y la grilla con todos los eventos publicados. */
(function () {
  const COLORES = ["#2B2B2A", "#4A4A4A", "#8C8577", "#2E3B36"];
  const $ = (x) => document.getElementById(x);
  let eventos = [];

  function imagen(e, tipo) {
    return e.imagen ? `/api/events/imagenes/${encodeURIComponent(e.imagen)}-${tipo}.webp` : "";
  }
  function fondo(e, i, tipo) {
    const img = imagen(e, tipo);
    return img ? `background-image:linear-gradient(180deg,rgba(0,0,0,0) 35%,rgba(0,0,0,.75)),url('${img}')`
               : `background:${COLORES[i % COLORES.length]}`;
  }
  function fechaCorta(iso) {
    const d = new Date(iso);
    const dia = d.toLocaleDateString("es-BO", { weekday: "short" }).replace(".", "");
    return `${dia} · ${d.getDate()} ${fmt.mes(iso)} · ${fmt.hora(iso)}`;
  }
  function etiqueta(e) {
    if (e.estado_venta === "Agotado") return '<span class="status status--out">Agotado</span>';
    if (e.estado_venta === "Pocas entradas") return '<span class="status status--low">Pocas entradas</span>';
    return "";
  }

  /* Destacado grande + hasta 4 laterales */
  function destacado(e, i, grande) {
    return `
      <a class="destacado ${grande ? "destacado--grande" : ""}" href="/evento/${e.id}" style="${fondo(e, i, grande ? "banner" : "card")}">
        <span class="destacado__lugar">${esc(e.lugar)}</span>
        <div class="destacado__info">
          ${etiqueta(e)}
          <h3 class="destacado__titulo">${esc(e.nombre)}</h3>
          <p class="destacado__meta">${esc(fechaCorta(e.fecha))}${e.precio_desde != null ? " · desde " + fmt.bs(e.precio_desde) : ""}</p>
        </div>
      </a>`;
  }

  /* Tarjeta para filas y grilla */
  function tarjeta(e, i) {
    return `
      <a class="tcard" href="/evento/${e.id}" draggable="false">
        <div class="tcard__img" style="${fondo(e, i, "card")}">${e.imagen ? "" : `<span>${esc(e.nombre)}</span>`}</div>
        <p class="tcard__fecha">${esc(fechaCorta(e.fecha))}</p>
        <h3 class="tcard__titulo">${esc(e.nombre)}</h3>
        <p class="tcard__lugar">${esc(e.lugar)}</p>
        <p class="tcard__precio">${e.estado_venta === "Agotado" ? "Agotado" : e.precio_desde != null ? "Desde " + fmt.bs(e.precio_desde) : ""}</p>
      </a>`;
  }

  function pintar() {
    const proximos = eventos.filter((e) => fechas.dia(e.fecha) >= fechas.hoy());

    // Destacados: primero los que tienen imagen, luego los más cercanos
    const orden = [...proximos].sort((a, b) => (b.imagen ? 1 : 0) - (a.imagen ? 1 : 0));
    const [principal, ...resto] = orden;
    $("destacados").innerHTML = principal
      ? destacado(principal, 0, true) + `<div class="destacados__lado">${resto.slice(0, 4).map((e, i) => destacado(e, i + 1, false)).join("")}</div>`
      : '<div class="card empty-state"><p class="muted">No hay eventos publicados por ahora.</p></div>';

    // Esta semana (próximos 7 días); si no hay, los más cercanos
    const limite = new Date(Date.now() + 7 * 864e5).toISOString();
    let semana = proximos.filter((e) => e.fecha <= limite || fechas.dia(e.fecha) <= fechas.dia(limite));
    $("t-semana").textContent = semana.length ? "Esta semana" : "Próximamente";
    if (!semana.length) semana = proximos.slice(0, 8);
    $("semana").innerHTML = semana.map(tarjeta).join("");
    $("sec-semana").hidden = !semana.length;

    // Más vendidos
    const vendidos = [...proximos].filter((e) => e.vendidos > 0).sort((a, b) => b.vendidos - a.vendidos).slice(0, 10);
    $("vendidos").innerHTML = vendidos.map(tarjeta).join("");
    $("sec-vendidos").hidden = !vendidos.length;

    filtrar();
  }

  /* Buscador: filtra la grilla "Todos los eventos" */
  const form = $("buscador");
  function filtrar() {
    const q = form.q.value.trim().toLowerCase();
    const mes = form.mes.value;
    const lista = eventos.filter((e) => fechas.dia(e.fecha) >= fechas.hoy())
      .filter((e) => !q || (e.nombre + " " + e.lugar).toLowerCase().includes(q))
      .filter((e) => !mes || fechas.mes(e.fecha) === mes);
    $("t-todos").textContent = q || mes ? `Resultados (${lista.length})` : "Todos los eventos";
    $("todos").innerHTML = lista.length ? lista.map(tarjeta).join("")
      : '<p class="muted">No encontramos eventos con esa búsqueda.</p>';
  }
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    filtrar();
    $("t-todos").scrollIntoView({ behavior: "smooth", block: "start" });
  });
  form.q.addEventListener("input", filtrar);
  form.mes.addEventListener("change", filtrar);

  /* Filas deslizables: flechas, teclado y arrastre con el mouse */
  document.querySelectorAll("[data-rail]").forEach((b) => b.addEventListener("click", () => {
    const rail = $(b.dataset.rail);
    const card = rail.querySelector(".tcard");
    rail.scrollBy({ left: Number(b.dataset.dir) * (card ? card.offsetWidth + 16 : 300) * 2, behavior: "smooth" });
  }));
  document.querySelectorAll(".rail--cards").forEach((rail) => {
    let presionado = false, inicioX = 0, scrollInicio = 0, movido = false;
    rail.addEventListener("pointerdown", (e) => {
      if (e.pointerType !== "mouse") return;
      presionado = true; movido = false; inicioX = e.clientX; scrollInicio = rail.scrollLeft;
    });
    window.addEventListener("pointermove", (e) => {
      if (!presionado) return;
      const dx = e.clientX - inicioX;
      if (!movido && Math.abs(dx) > 5) { movido = true; rail.classList.add("is-dragging"); }
      if (movido) rail.scrollLeft = scrollInicio - dx;
    });
    window.addEventListener("pointerup", () => { presionado = false; rail.classList.remove("is-dragging"); });
    rail.addEventListener("click", (e) => { if (movido) { e.preventDefault(); movido = false; } }, true);
  });

  async function cargar() {
    try {
      eventos = await API.request("/api/events/eventos");
      const meses = [...new Set(eventos.filter((e) => fechas.dia(e.fecha) >= fechas.hoy()).map((e) => fechas.mes(e.fecha)))].sort();
      form.mes.innerHTML = '<option value="">Todas las fechas</option>' +
        meses.map((m) => `<option value="${m}">${fechas.nombreMes(m)}</option>`).join("");
      pintar();
    } catch (err) {
      $("destacados").innerHTML = '<p class="muted">No se pudo cargar la cartelera: ' + esc(err.message) + "</p>";
    }
  }

  cargar();
})();
