/* Mis entradas (descarga de PDF) y Mis compras (historial de órdenes). */
(function () {
  if (!requireLogin()) return;

  const ESTADOS = { pendiente: "Pendiente", pagada: "Pagada", rechazada: "Rechazada", cancelada: "Cancelada" };

  async function cargarEntradas() {
    const cont = document.getElementById("tickets");
    try {
      const entradas = await API.request("/api/tickets/entradas/mias", { auth: true });
      if (!entradas.length) {
        cont.innerHTML = '<p class="muted">Todavía no tienes entradas. <a href="/">Ver la cartelera</a></p>';
        return;
      }
      cont.innerHTML = entradas.map((t) => `
        <article class="ticket">
          <div class="ticket__top">
            <span class="ticket__brand">ENTRADASYA</span>
            <span class="ticket__num">${t.numero} / ${t.total_orden}</span>
          </div>
          <h3 class="ticket__title">${esc(t.evento_nombre)}</h3>
          <p class="ticket__meta">${esc(fmt.fecha(t.evento_fecha))} · ${esc(fmt.hora(t.evento_fecha))}</p>
          <p class="ticket__meta">${esc(t.evento_lugar)} · Sector ${esc(t.sector_nombre)}</p>
          <div class="ticket__foot">
            <code class="ticket__code">${esc(t.codigo)}</code>
            <button type="button" class="btn btn--small" data-codigo="${esc(t.codigo)}">Descargar PDF</button>
          </div>
        </article>`).join("");
      cont.querySelectorAll("button[data-codigo]").forEach((b) => b.addEventListener("click", async () => {
        const codigo = b.dataset.codigo;
        b.disabled = true; b.textContent = "Descargando…";
        try {
          await API.descargar("/api/tickets/entradas/" + encodeURIComponent(codigo) + "/pdf", "entrada-" + codigo + ".pdf");
        } catch (e) { alert(e.message); }
        b.disabled = false; b.textContent = "Descargar PDF";
      }));
    } catch (e) {
      cont.innerHTML = '<p class="muted">No se pudieron cargar tus entradas: ' + esc(e.message) + "</p>";
    }
  }

  async function cargarCompras() {
    const tbody = document.getElementById("orders");
    try {
      const ordenes = await API.request("/api/orders/ordenes/mias", { auth: true });
      if (!ordenes.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="muted">Sin compras todavía.</td></tr>';
        return;
      }
      tbody.innerHTML = ordenes.map((o) => `
        <tr>
          <td>${esc(fmt.corta(o.creado_en))}</td>
          <td>${esc(o.evento_nombre || "Evento #" + o.evento_id)}</td>
          <td>${esc(o.sector_nombre || "—")}</td>
          <td>${o.cantidad}</td>
          <td>${o.total != null ? fmt.bs(o.total) : "—"}</td>
          <td><span class="status status--${o.estado}">${ESTADOS[o.estado] || esc(o.estado)}</span>${o.motivo ? '<small class="muted block">' + esc(o.motivo) + "</small>" : ""}</td>
        </tr>`).join("");
    } catch (e) {
      tbody.innerHTML = '<tr><td colspan="6" class="muted">' + esc(e.message) + "</td></tr>";
    }
  }

  cargarEntradas();
  cargarCompras();
})();
