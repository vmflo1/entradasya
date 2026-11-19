/* Página del evento: mapa de sectores, cantidad (1 a 6), pago simulado y compra. */
(function () {
  const app = document.getElementById("evento-app");
  const eventoId = Number(app.dataset.eventoId);
  const COLORES = ["#111111", "#4A4A4A", "#8C8577", "#B9B2A3"];
  const SELECCIONADO = "#FAAC43"; // amarillo del logo
  const MAX = 6;

  const estado = { evento: null, sectorId: null, cantidad: 1 };
  const $ = (id) => document.getElementById(id);
  const alerta = $("alert");

  function colorDe(i) { return COLORES[Math.min(i, COLORES.length - 1)]; }
  function textoClaro(color) { return color === "#111111" || color === "#4A4A4A" || color === "#8C8577"; }
  function sectorActual() { return estado.evento && estado.evento.sectores.find((s) => s.id === estado.sectorId); }

  /* ---------- Cabecera ---------- */
  function pintarCabecera(ev) {
    document.title = ev.nombre + " · EntradasYa";
    if (ev.imagen && !document.getElementById("event-banner")) {
      $("event-head").insertAdjacentHTML("beforebegin",
        `<div class="event-banner" id="event-banner"><img src="/api/events/imagenes/${encodeURIComponent(ev.imagen)}-banner.webp" alt=""></div>`);
    }
    $("event-head").innerHTML = `
      <div class="event-head__date">
        <span class="event-head__day">${fmt.dia(ev.fecha)}</span>
        <span class="event-head__month">${esc(fmt.mes(ev.fecha))}</span>
      </div>
      <div class="event-head__info">
        <p class="eyebrow">${esc(ev.estado_venta)}</p>
        <h1 class="event-head__title">${esc(ev.nombre)}</h1>
        <p class="event-head__meta">${esc(fmt.fecha(ev.fecha))} · ${esc(fmt.hora(ev.fecha))} · ${esc(ev.lugar)}</p>
        <p class="event-head__desc">${esc(ev.descripcion)}</p>
      </div>`;
  }

  /* ---------- Mapa SVG: cada franja es un sector; el escenario abajo ---------- */
  function pintarMapa(sectores) {
    const W = 600, H = 440, n = Math.max(sectores.length, 1);
    const alto = Math.min(72, 290 / n), gap = 10;
    let filas = "", minY = 380;
    sectores.forEach((s, i) => {
      const abajo = 362 - i * (alto + gap);
      const arriba = abajo - alto;
      minY = Math.min(minY, arriba);
      const anchoAbajo = 280 + i * 2 * (alto * 0.6 + gap);
      const anchoArriba = anchoAbajo + alto * 1.2;
      const x1 = (W - anchoAbajo) / 2, x2 = x1 + anchoAbajo;
      const x3 = (W + anchoArriba) / 2, x4 = (W - anchoArriba) / 2;
      const agotado = s.cupo_disponible <= 0;
      const elegido = s.id === estado.sectorId;
      const fill = elegido ? SELECCIONADO : agotado ? "url(#rayado)" : colorDe(i);
      const claro = !elegido && !agotado && textoClaro(colorDe(i));
      filas += `
        <g class="sector ${agotado ? "is-out" : ""} ${elegido ? "is-selected" : ""}" data-id="${s.id}"
           tabindex="${agotado ? -1 : 0}" role="button" aria-label="${esc(s.nombre)}, ${fmt.bs(s.precio)}, ${agotado ? "agotado" : s.cupo_disponible + " disponibles"}">
          <title>${esc(s.nombre)} · ${fmt.bs(s.precio)} · ${agotado ? "Agotado" : s.cupo_disponible + " disponibles"}</title>
          <polygon points="${x1},${abajo} ${x2},${abajo} ${x3},${arriba} ${x4},${arriba}" fill="${fill}" />
          <text x="${W / 2}" y="${arriba + alto / 2 - 4}" class="sector__name" fill="${claro ? "#FFFFFF" : "#111111"}">${esc(s.nombre)}</text>
          <text x="${W / 2}" y="${arriba + alto / 2 + 14}" class="sector__price" fill="${claro ? "#FFFFFF" : "#111111"}">${agotado ? "Agotado" : fmt.bs(s.precio)}</text>
        </g>`;
    });
    $("map").innerHTML = `
      <svg viewBox="0 ${minY - 16} ${W} ${H - minY + 16}" xmlns="http://www.w3.org/2000/svg" role="img">
        <defs>
          <pattern id="rayado" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="10" height="10" fill="#E2DFD8"/><line x1="0" y1="0" x2="0" y2="10" stroke="#C9C6BF" stroke-width="4"/>
          </pattern>
        </defs>
        ${filas}
        <rect x="${(W - 240) / 2}" y="380" width="240" height="40" rx="20" fill="#C9C6BF"/>
        <text x="${W / 2}" y="405" class="stage">ESCENARIO</text>
      </svg>`;

    $("legend").innerHTML = sectores.map((s, i) =>
      `<li><span class="dot" style="background:${s.cupo_disponible <= 0 ? "#E2DFD8" : colorDe(i)}"></span>${esc(s.nombre)}</li>`
    ).join("") + `<li><span class="dot" style="background:${SELECCIONADO}"></span>Tu elección</li>`;

    $("map").querySelectorAll(".sector:not(.is-out)").forEach((g) => {
      g.addEventListener("click", () => elegirSector(Number(g.dataset.id)));
      g.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); elegirSector(Number(g.dataset.id)); } });
    });
  }

  /* ---------- Lista lateral de sectores ---------- */
  function pintarLista(sectores) {
    $("sector-list").innerHTML = sectores.map((s, i) => {
      const agotado = s.cupo_disponible <= 0;
      return `
        <li>
          <button type="button" class="sector-row ${s.id === estado.sectorId ? "is-selected" : ""}" data-id="${s.id}" ${agotado ? "disabled" : ""}>
            <span class="dot" style="background:${agotado ? "#E2DFD8" : colorDe(i)}"></span>
            <span class="sector-row__name">${esc(s.nombre)}<small>${agotado ? "Agotado" : s.cupo_disponible + " disponibles"}</small></span>
            <span class="sector-row__price">${fmt.bs(s.precio)}</span>
          </button>
        </li>`;
    }).join("");
    $("sector-list").querySelectorAll(".sector-row").forEach((b) =>
      b.addEventListener("click", () => elegirSector(Number(b.dataset.id))));
  }

  /* ---------- Cantidad: píldoras del 1 al 6 ---------- */
  function pintarCantidad() {
    const s = sectorActual();
    const limite = s ? Math.min(MAX, s.cupo_disponible) : MAX;
    if (estado.cantidad > limite) estado.cantidad = Math.max(1, limite);
    let html = "";
    for (let n = 1; n <= MAX; n++) {
      const off = !s || n > limite;
      html += `<button type="button" class="pill ${n === estado.cantidad && s ? "is-active" : ""}" data-n="${n}" ${off ? "disabled" : ""}>${n}</button>`;
    }
    $("pills").innerHTML = html;
    $("pills").querySelectorAll(".pill").forEach((b) =>
      b.addEventListener("click", () => { estado.cantidad = Number(b.dataset.n); actualizar(); }));
  }

  function pintarResumen() {
    const s = sectorActual();
    $("sum-sector").textContent = s ? s.nombre : "—";
    $("sum-cantidad").textContent = s ? estado.cantidad : "—";
    $("sum-total").textContent = fmt.bs(s ? Number(s.precio) * estado.cantidad : 0);
    $("qr-monto").textContent = $("sum-total").textContent;
    $("btn-comprar").disabled = !s;
    // Barra fija del celular
    $("buybar").hidden = false;
    $("buybar-detalle").textContent = s ? `${s.nombre} · ${estado.cantidad} entrada(s)` : "Elige un sector";
    $("buybar-total").textContent = fmt.bs(s ? Number(s.precio) * estado.cantidad : 0);
    $("buybar-btn").disabled = !s;
  }

  function actualizar() {
    const sectores = estado.evento.sectores;
    pintarMapa(sectores);
    pintarLista(sectores);
    pintarCantidad();
    pintarResumen();
  }

  function elegirSector(id) {
    estado.sectorId = id;
    alerta.hidden = true;
    actualizar();
  }

  /* ---------- Carga ---------- */
  async function cargar() {
    try {
      const ev = await API.request("/api/events/eventos/" + eventoId);
      estado.evento = ev;
      if (estado.sectorId && !ev.sectores.some((s) => s.id === estado.sectorId && s.cupo_disponible > 0)) {
        estado.sectorId = null;
      }
      pintarCabecera(ev);
      actualizar();
    } catch (e) {
      $("event-head").innerHTML = `<p class="eyebrow">Error</p><h1 class="event-head__title">${esc(e.message)}</h1>`;
    }
  }

  /* ---------- Forma de pago ---------- */
  let metodo = "tarjeta";
  const TEXTO_BOTON = { tarjeta: "Confirmar compra", qr: "Ya pagué · Confirmar compra" };
  document.querySelectorAll(".metodo").forEach((b) => b.addEventListener("click", () => {
    metodo = b.dataset.metodo;
    document.querySelectorAll(".metodo").forEach((x) => {
      x.classList.toggle("is-active", x === b);
      x.setAttribute("aria-selected", x === b ? "true" : "false");
    });
    $("pago-tarjeta").hidden = metodo !== "tarjeta";
    $("pago-qr").hidden = metodo !== "qr";
    $("btn-comprar").textContent = TEXTO_BOTON[metodo];
    alerta.hidden = true;
  }));

  // Formato como en una tarjeta real: 4111 1111 1111 1111 y MM/AA
  const payForm = $("pay-form");
  payForm.numero.addEventListener("input", (e) => {
    const d = e.target.value.replace(/\D/g, "").slice(0, 19);
    e.target.value = d.replace(/(\d{4})(?=\d)/g, "$1 ");
  });
  payForm.vencimiento.addEventListener("input", (e) => {
    const d = e.target.value.replace(/\D/g, "").slice(0, 4);
    e.target.value = d.length > 2 ? d.slice(0, 2) + "/" + d.slice(2) : d;
  });
  payForm.cvv.addEventListener("input", (e) => { e.target.value = e.target.value.replace(/\D/g, "").slice(0, 4); });

  function datosTarjeta(form) {
    const titular = form.titular.value.trim();
    const numero = form.numero.value.replace(/[\s-]/g, "");
    const vencimiento = form.vencimiento.value.trim();
    const cvv = form.cvv.value.trim();
    if (titular.length < 2) return { error: "Escribe el nombre del titular." };
    if (!/^\d{12,19}$/.test(numero)) return { error: "El número de tarjeta debe tener entre 12 y 19 dígitos." };
    const m = /^(0[1-9]|1[0-2])\/(\d{2})$/.exec(vencimiento);
    if (!m) return { error: "El vencimiento debe tener el formato MM/AA." };
    const hoy = new Date();
    const anio = 2000 + Number(m[2]), mes = Number(m[1]);
    if (anio < hoy.getFullYear() || (anio === hoy.getFullYear() && mes < hoy.getMonth() + 1))
      return { error: "La tarjeta está vencida." };
    if (!/^\d{3,4}$/.test(cvv)) return { error: "El código de seguridad (CVV) debe tener 3 o 4 dígitos." };
    return { tarjeta_titular: titular, tarjeta_numero: numero, tarjeta_vencimiento: vencimiento, tarjeta_cvv: cvv };
  }

  /* ---------- Compra ---------- */
  payForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!requireLogin()) return;
    const s = sectorActual();
    if (!s) return;
    let pago = { metodo: "qr" };
    if (metodo === "tarjeta") {
      const t = datosTarjeta(e.target);
      if (t.error) return mostrarAlerta(alerta, t.error);
      pago = { metodo: "tarjeta", ...t };
    }

    const boton = $("btn-comprar");
    boton.disabled = true;
    boton.textContent = "Procesando…";
    alerta.hidden = true;
    try {
      const orden = await API.request("/api/orders/ordenes", {
        method: "POST",
        auth: true,
        body: { evento_id: eventoId, sector_id: s.id, cantidad: estado.cantidad, ...pago },
      });
      location.href = "/confirmacion/" + orden.id;
    } catch (err) {
      if (err.status === 409) mostrarAlerta(alerta, "Agotado: ya no quedan entradas suficientes en este sector.");
      else if (err.status === 402) mostrarAlerta(alerta, "Pago rechazado. No se realizó ningún cobro y los cupos fueron liberados.");
      else mostrarAlerta(alerta, err.message);
      boton.textContent = TEXTO_BOTON[metodo];
      await cargar();
    }
  });

  $("buybar-btn").addEventListener("click", () => {
    $("pay-form").scrollIntoView({ behavior: "smooth", block: "start" });
    setTimeout(() => { if (metodo === "tarjeta") payForm.titular.focus({ preventScroll: true }); }, 400);
  });

  cargar();
})();
