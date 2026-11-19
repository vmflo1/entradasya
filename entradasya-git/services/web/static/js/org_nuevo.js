/* Nuevo evento (organizador): nace en borrador y abre su pantalla de edición. */
(function () {
  const app = document.getElementById("org-nuevo");
  if (!requireRole(["organizador"], app)) return;

  const form = document.getElementById("form-evento");
  const alerta = document.getElementById("alert");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (form.nombre.value.trim().length < 2) return mostrarAlerta(alerta, "Escribe el nombre del evento.");
    if (!form.fecha.value) return mostrarAlerta(alerta, "Elige la fecha y la hora.");
    if (form.lugar.value.trim().length < 2) return mostrarAlerta(alerta, "Escribe el lugar.");
    const boton = form.querySelector("button[type=submit]");
    boton.disabled = true;
    try {
      const ev = await API.request("/api/events/organizador/eventos", {
        method: "POST", auth: true,
        body: { nombre: form.nombre.value, fecha: form.fecha.value, lugar: form.lugar.value, descripcion: form.descripcion.value },
      });
      location.href = "/organizador/evento/" + ev.id;
    } catch (err) {
      mostrarAlerta(alerta, err.message);
      boton.disabled = false;
    }
  });
})();
