/* Control de ingresos de un evento (portero): capacidad, vendidas, escaneadas, faltantes y
   disponibles por zona, más el escaneo del QR o el código escrito. */
(function () {
  const app = document.getElementById("control-app");
  if (!requireRole(["portero"], app)) return;

  const eventoId = Number(app.dataset.eventoId);
  const $ = (x) => document.getElementById(x);
  const resultado = $("resultado");
  const historial = [];
  let lector = null;
  let ocupado = false;
  let ultimo = { codigo: "", t: 0 };

  /* ---------- Ingresos por zona: solo "ingresaron X de Y" ---------- */
  function zona(nombre, ingresaron, vendidas) {
    const pct = vendidas ? Math.min(100, (ingresaron / vendidas) * 100) : 0;
    return `
      <div class="zona">
        <div class="zona__head"><strong>${esc(nombre)}</strong><span><b>${ingresaron}</b> de ${vendidas} ingresaron</span></div>
        <div class="zona__bar" role="progressbar" aria-valuenow="${ingresaron}" aria-valuemax="${vendidas}"><span class="zona__escaneadas" style="width:${pct}%"></span></div>
      </div>`;
  }

  async function actualizar() {
    try {
      const [ev, ing] = await Promise.all([
        API.request("/api/events/eventos/" + eventoId),
        API.request("/api/checkin/eventos/" + eventoId + "/asistentes", { auth: true }),
      ]);
      document.title = "Control · " + ev.nombre;
      $("ev-head").innerHTML = `
        <p class="eyebrow">Control de ingresos</p>
        <h1 class="event-head__title">${esc(ev.nombre)}</h1>
        <p class="event-head__meta">${esc(fmt.fecha(ev.fecha))} · ${esc(fmt.hora(ev.fecha))} · ${esc(ev.lugar)}</p>`;

      const porSector = Object.fromEntries((ing.por_sector || []).map((s) => [s.sector, s.ingresados]));
      let totalIngresaron = 0, totalVendidas = 0, aLaVenta = 0, html = "";
      ev.sectores.forEach((s) => {
        const vendidas = s.cupo_total - s.cupo_disponible;
        const ingresaron = porSector[s.nombre] || 0;
        delete porSector[s.nombre];
        totalIngresaron += ingresaron; totalVendidas += vendidas; aLaVenta += s.cupo_disponible;
        html += zona(s.nombre, ingresaron, vendidas);
      });
      // Ingresos registrados antes de que se guardara la zona
      Object.entries(porSector).forEach(([nombre, n]) => {
        totalIngresaron += n;
        html += `<p class="muted small">${esc(nombre)}: ${n} ingreso(s) sin zona asignada</p>`;
      });
      $("zonas").innerHTML = html || '<p class="muted">El evento no tiene sectores.</p>';
      $("total-ingresos").innerHTML = `
        <span class="total-ingresos__num">${totalIngresaron} <small>de ${totalVendidas}</small></span>
        <span class="muted small">personas ingresaron · ${aLaVenta} entradas aún a la venta</span>`;
      $("actualizado").textContent = "Actualizado a las " + new Date().toLocaleTimeString("es-BO");
    } catch (err) {
      if (err.status === 404) {
        $("ev-head").innerHTML = '<p class="eyebrow">Evento no disponible</p><h1 class="event-head__title">Este evento no está publicado</h1>';
        $("zonas").innerHTML = '<p class="muted">Si fue cancelado o volvió a borrador, no se puede controlar el ingreso.</p>';
        $("form-codigo").querySelectorAll("input, button").forEach((el) => { el.disabled = true; });
        $("btn-camara").disabled = true;
      } else {
        $("actualizado").textContent = "No se pudo actualizar: " + err.message;
      }
    }
  }

  /* ---------- Escaneo ---------- */
  function mostrar(r) {
    const ok = r.permitido;
    resultado.className = "resultado " + (ok ? "resultado--ok" : "resultado--no");
    resultado.innerHTML = `
      <p class="resultado__titulo">${ok ? "Ingreso permitido" : "Ingreso rechazado"}</p>
      <p class="resultado__codigo">${esc(r.codigo)}${ok && r.sector_nombre ? " · Zona " + esc(r.sector_nombre) : ""}</p>
      <p class="resultado__detalle">${ok ? esc(r.evento_nombre || "") : esc(r.motivo || "")}</p>`;
    historial.unshift({ ok, codigo: r.codigo, texto: ok ? "Permitido" + (r.sector_nombre ? " · " + r.sector_nombre : "") : r.motivo, hora: new Date() });
    $("historial").innerHTML = historial.slice(0, 8).map((h) => `
      <li class="historial__item ${h.ok ? "is-ok" : "is-no"}">
        <span class="historial__dot"></span>
        <code>${esc(h.codigo)}</code>
        <span>${esc(h.texto)}</span>
        <small class="muted">${h.hora.toLocaleTimeString("es-BO")}</small>
      </li>`).join("");
  }

  async function validar(codigo) {
    codigo = (codigo || "").trim().toUpperCase();
    if (!codigo || ocupado) return;
    // La cámara lee el mismo QR varias veces por segundo: se ignora la repetición inmediata
    if (codigo === ultimo.codigo && Date.now() - ultimo.t < 5000) return;
    ultimo = { codigo, t: Date.now() };
    ocupado = true;
    resultado.className = "resultado resultado--espera";
    resultado.innerHTML = '<p class="resultado__titulo">Validando…</p><p class="resultado__codigo">' + esc(codigo) + "</p>";
    try {
      mostrar(await API.request("/api/checkin/ingresos", { method: "POST", auth: true, body: { codigo, evento_id: eventoId } }));
      actualizar();
    } catch (err) {
      resultado.className = "resultado resultado--no";
      resultado.innerHTML = '<p class="resultado__titulo">No se pudo validar</p><p class="resultado__detalle">' + esc(err.message) + "</p>";
    } finally {
      ocupado = false;
    }
  }

  $("form-codigo").addEventListener("submit", (e) => {
    e.preventDefault();
    validar(e.target.codigo.value);
    e.target.reset();
    e.target.codigo.focus();
  });

  $("btn-camara").addEventListener("click", async () => {
    const boton = $("btn-camara");
    if (lector) {
      await lector.stop().catch(() => {});
      lector = null;
      $("lector").classList.remove("is-on");
      boton.textContent = "Activar cámara";
      return;
    }
    if (typeof Html5Qrcode === "undefined") {
      $("nota-camara").textContent = "No se cargó el lector de QR. Escribe el código.";
      return;
    }
    try {
      // El contenedor debe estar visible ANTES de iniciar: el lector toma su ancho para el video
      $("lector").classList.add("is-on");
      lector = new Html5Qrcode("lector");
      await lector.start({ facingMode: "environment" },
        { fps: 10, qrbox: (w, h) => { const lado = Math.floor(Math.min(w, h) * 0.8); return { width: lado, height: lado }; } },
        (texto) => validar(texto));
      boton.textContent = "Detener cámara";
    } catch (err) {
      lector = null;
      $("lector").classList.remove("is-on");
      $("nota-camara").innerHTML = "No se pudo abrir la cámara (" + esc(String(err).slice(0, 120)) +
        "). En el celular se necesita HTTPS o <strong>localhost</strong>. Escribe el código.";
    }
  });

  actualizar();
  setInterval(actualizar, 20000);  // otros porteros pueden estar escaneando en otra puerta
})();
