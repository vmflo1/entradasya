/* Edición de un evento del organizador: datos, imagen, sectores, estado, ventas e ingresos. */
(function () {
  const app = document.getElementById("org-evento");
  if (!requireRole(["organizador"], app)) return;

  const id = Number(app.dataset.eventoId);
  const BASE = "/api/events/organizador/eventos/" + id;
  const ESTADOS = { borrador: "Borrador", publicado: "Publicado", cancelado: "Cancelado" };
  const $ = (x) => document.getElementById(x);
  let evento = null;

  /* ---------- Pintar ---------- */
  function pintar(ev) {
    evento = ev;
    document.title = ev.nombre + " · Panel";
    $("org-head").innerHTML = `
      <p class="eyebrow">Evento #${ev.id} · <span class="status status--ev-${ev.estado}">${ESTADOS[ev.estado]}</span></p>
      <h1 class="event-head__title">${esc(ev.nombre)}</h1>
      <p class="event-head__meta">${esc(fmt.fecha(ev.fecha))} · ${esc(fmt.hora(ev.fecha))} · ${esc(ev.lugar)}</p>
      ${ev.estado === "publicado" ? `<p class="small"><a href="/evento/${ev.id}" target="_blank" rel="noopener">Ver como cliente ↗</a></p>` : ""}`;

    // Datos
    const f = $("form-datos");
    f.nombre.value = ev.nombre;
    f.fecha.value = fmt.paraInput(ev.fecha);
    f.lugar.value = ev.lugar;
    f.descripcion.value = ev.descripcion || "";
    const cancelado = ev.estado === "cancelado";
    document.querySelectorAll("#form-datos input, #form-datos textarea, #form-datos button, #form-sector input, #form-sector button, #form-imagen input, #form-imagen button")
      .forEach((el) => { el.disabled = cancelado; });

    // Imagen
    $("img-preview").innerHTML = ev.imagen
      ? `<img src="/api/events/imagenes/${encodeURIComponent(ev.imagen)}-banner.webp" alt="Imagen de ${esc(ev.nombre)}">`
      : '<span class="muted">Sin imagen</span>';

    // Sectores
    $("sectores").innerHTML = ev.sectores.length ? ev.sectores.map((s) => `
      <tr data-id="${s.id}">
        <td><input class="cell-input" name="nombre" value="${esc(s.nombre)}" maxlength="60" ${cancelado ? "disabled" : ""}></td>
        <td><input class="cell-input" name="precio" type="number" min="0" step="0.01" value="${Number(s.precio).toFixed(2)}" ${cancelado ? "disabled" : ""}></td>
        <td><input class="cell-input" name="cupo_total" type="number" min="1" step="1" value="${s.cupo_total}" ${cancelado ? "disabled" : ""}></td>
        <td>${s.vendidos}</td>
        <td>${s.cupo_disponible}</td>
        <td class="cell-actions">
          ${cancelado ? "" : `<button type="button" class="btn btn--small" data-accion="guardar">Guardar</button>
          <button type="button" class="btn btn--small btn--ghost" data-accion="eliminar" ${s.vendidos > 0 ? "disabled title=\"Tiene ventas\"" : ""}>Eliminar</button>`}
        </td>
      </tr>`).join("") : '<tr><td colspan="6" class="muted">Agrega al menos un sector para poder publicar.</td></tr>';

    // Estado
    $("estado-actual").innerHTML = `Estado actual: <strong>${ESTADOS[ev.estado]}</strong>` +
      (ev.estado === "borrador" ? '<br><span class="muted small">No aparece en la cartelera.</span>' : "") +
      (ev.estado === "publicado" ? '<br><span class="muted small">Visible en la cartelera y a la venta.</span>' : "") +
      (ev.estado === "cancelado" ? '<br><span class="muted small">No se vende y no se puede editar.</span>' : "");
    const acciones = [];
    if (ev.estado === "borrador") acciones.push(["publicado", "Publicar", "btn--primary"]);
    if (ev.estado === "publicado") acciones.push(["borrador", "Volver a borrador", ""]);
    if (ev.estado !== "cancelado") acciones.push(["cancelado", "Cancelar evento", "btn--danger"]);
    $("estado-acciones").innerHTML = acciones.map(([e, t, c]) =>
      `<button type="button" class="btn btn--block ${c}" data-estado="${e}">${t}</button>`).join("");
  }

  async function pintarVentas() {
    const [ventas, ingresos] = await Promise.allSettled([
      API.request("/api/orders/ventas/eventos/" + id, { auth: true }),
      API.request("/api/checkin/eventos/" + id + "/asistentes", { auth: true }),
    ]);
    const v = ventas.status === "fulfilled" ? ventas.value : null;
    const a = ingresos.status === "fulfilled" ? ingresos.value : null;
    const cupo = evento ? evento.cupo_total : 0;
    $("stats").innerHTML = `
      <div class="stat"><span class="stat__num">${v ? v.entradas_vendidas : "—"}</span><span class="stat__txt">entradas vendidas${cupo ? " de " + cupo : ""}</span></div>
      <div class="stat"><span class="stat__num">${v ? fmt.bs(v.total_recaudado) : "—"}</span><span class="stat__txt">recaudado</span></div>
      <div class="stat"><span class="stat__num">${v ? v.ordenes_pagadas : "—"}</span><span class="stat__txt">compras pagadas · ${v ? v.ordenes_rechazadas : "—"} rechazadas</span></div>
      <div class="stat"><span class="stat__num">${a ? a.asistentes : "—"}</span><span class="stat__txt">personas ingresaron</span></div>`;
    $("ventas").innerHTML = !v ? `<tr><td colspan="3" class="muted">${esc(ventas.reason ? ventas.reason.message : "Sin datos")}</td></tr>`
      : v.por_sector.length ? v.por_sector.map((s) =>
        `<tr><td>${esc(s.sector)}</td><td>${s.entradas}</td><td>${fmt.bs(s.recaudado)}</td></tr>`).join("")
      : '<tr><td colspan="3" class="muted">Todavía no hay ventas.</td></tr>';
  }

  async function cargar() {
    try {
      pintar(await API.request(BASE, { auth: true }));
      pintarVentas();
    } catch (err) {
      $("org-head").innerHTML = `<p class="eyebrow">Error</p><h1 class="event-head__title">${esc(err.message)}</h1>`;
    }
  }

  /* ---------- Acciones ---------- */
  async function enviar(fn, alerta, ok) {
    $(alerta).hidden = true;
    try {
      pintar(await fn());
      pintarVentas();
      if (ok) mostrarAlerta($(alerta), ok, "ok");
    } catch (err) {
      mostrarAlerta($(alerta), err.message);
    }
  }

  $("form-datos").addEventListener("submit", (e) => {
    e.preventDefault();
    const f = e.target;
    enviar(() => API.request(BASE, { method: "PUT", auth: true, body: {
      nombre: f.nombre.value, fecha: f.fecha.value, lugar: f.lugar.value, descripcion: f.descripcion.value,
    } }), "alert-datos", "Cambios guardados.");
  });

  $("form-sector").addEventListener("submit", (e) => {
    e.preventDefault();
    const f = e.target;
    if (!f.nombre.value.trim()) return mostrarAlerta($("alert-sector"), "Escribe el nombre del sector (por ejemplo VIP).");
    if (f.precio.value === "" || Number(f.precio.value) < 0) return mostrarAlerta($("alert-sector"), "Escribe un precio válido.");
    if (!f.cupo_total.value || Number(f.cupo_total.value) < 1) return mostrarAlerta($("alert-sector"), "El cupo debe ser al menos 1.");
    enviar(() => API.request(BASE + "/sectores", { method: "POST", auth: true, body: {
      nombre: f.nombre.value, precio: f.precio.value || 0, cupo_total: f.cupo_total.value || 0,
    } }), "alert-sector").then(() => { if ($("alert-sector").hidden) f.reset(); });
  });

  $("sectores").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-accion]");
    if (!b) return;
    const fila = b.closest("tr");
    const sid = fila.dataset.id;
    if (b.dataset.accion === "guardar") {
      const val = (n) => fila.querySelector(`[name=${n}]`).value;
      enviar(() => API.request("/api/events/organizador/sectores/" + sid, { method: "PUT", auth: true, body: {
        nombre: val("nombre"), precio: val("precio"), cupo_total: val("cupo_total"),
      } }), "alert-sector", "Sector actualizado.");
    } else if (b.dataset.accion === "eliminar") {
      if (b.dataset.confirmar !== "1") { b.dataset.confirmar = "1"; b.textContent = "¿Seguro?"; return; }
      enviar(() => API.request("/api/events/organizador/sectores/" + sid, { method: "DELETE", auth: true }), "alert-sector", "Sector eliminado.");
    }
  });

  $("estado-acciones").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-estado]");
    if (!b) return;
    if (b.dataset.estado === "cancelado" && b.dataset.confirmar !== "1") {
      b.dataset.confirmar = "1";
      b.textContent = "Confirmar cancelación (no se puede deshacer)";
      return;
    }
    enviar(() => API.request(BASE + "/estado", { method: "POST", auth: true, body: { estado: b.dataset.estado } }), "alert-estado");
  });

  $("form-imagen").addEventListener("submit", (e) => {
    e.preventDefault();
    const archivo = e.target.archivo.files[0];
    if (!archivo) return mostrarAlerta($("alert-imagen"), "Elige una imagen.");
    if (archivo.size > 5 * 1024 * 1024) return mostrarAlerta($("alert-imagen"), "La imagen supera los 5 MB.");
    const datos = new FormData();
    datos.append("archivo", archivo);
    enviar(() => API.request(BASE + "/imagen", { method: "POST", auth: true, body: datos }), "alert-imagen", "Imagen actualizada.")
      .then(() => e.target.reset());
  });

  cargar();
})();
