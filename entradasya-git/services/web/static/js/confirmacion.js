/* Compra exitosa: muestra el resumen de la orden. */
(function () {
  if (!requireLogin()) return;
  const cont = document.getElementById("success");
  const ordenId = cont.dataset.ordenId;

  async function cargar() {
    try {
      const o = await API.request("/api/orders/ordenes/" + encodeURIComponent(ordenId), { auth: true });
      document.getElementById("ok-evento").textContent = o.evento_nombre || "¡Listo!";
      document.getElementById("ok-texto").textContent = o.correo_enviado
        ? "Te enviamos un correo con el enlace para descargar tus entradas en PDF."
        : "Tu compra es válida. Puedes descargar tus entradas desde \"Mis entradas\".";
      document.getElementById("ok-resumen").innerHTML = `
        <div><span>Fecha</span><strong>${o.evento_fecha ? esc(fmt.fecha(o.evento_fecha)) + " · " + esc(fmt.hora(o.evento_fecha)) : "—"}</strong></div>
        <div><span>Lugar</span><strong>${esc(o.evento_lugar || "—")}</strong></div>
        <div><span>Sector</span><strong>${esc(o.sector_nombre || "—")}</strong></div>
        <div><span>Entradas</span><strong>${o.cantidad}</strong></div>
        <div class="summary__total"><span>Total pagado</span><strong>${fmt.bs(o.total)}</strong></div>`;
    } catch (e) {
      document.getElementById("ok-texto").textContent = e.message;
    }
  }
  cargar();
})();
