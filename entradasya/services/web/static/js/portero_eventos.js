/* Eventos (portero): los de hoy y los próximos (todos, o los del mes elegido).
   Al elegir uno se abre su control de ingresos. */
(function () {
  const app = document.getElementById("portero-app");
  if (!requireRole(["portero"], app)) return;

  const $ = (x) => document.getElementById(x);
  let eventos = [];
  let mesElegido = "";   // "" = todos los próximos

  function tarjeta(e) {
    const dia = fechas.dia(e.fecha);
    const hoy = fechas.hoy();
    const etiqueta = dia === hoy ? '<span class="status status--hoy">Hoy</span>'
      : dia < hoy ? '<span class="status status--pasado">Pasado</span>' : "";
    return `
      <a class="pt-card ${dia === hoy ? "is-hoy" : ""} ${dia < hoy ? "is-pasado" : ""}" href="/portero/evento/${e.id}">
        <div class="pt-card__date"><span>${fmt.dia(e.fecha)}</span><small>${esc(fmt.mes(e.fecha))}</small></div>
        <div class="pt-card__body">
          <h3>${esc(e.nombre)}</h3>
          <p class="muted">${esc(fmt.hora(e.fecha))} · ${esc(e.lugar)}</p>
        </div>
        <div class="pt-card__side">${etiqueta}<span class="pt-card__cta">Control de ingresos →</span></div>
      </a>`;
  }

  function pintarHoy() {
    const hoy = fechas.hoy();
    $("hoy-fecha").textContent = "· " + fmt.fecha(new Date().toISOString());
    const deHoy = eventos.filter((e) => fechas.dia(e.fecha) === hoy);
    $("hoy").innerHTML = deHoy.length ? deHoy.map(tarjeta).join("")
      : '<div class="card empty-state empty-state--small"><p class="muted">No hay eventos para hoy.</p></div>';
  }

  function pintarMeses() {
    // "Todos" + los meses que tienen eventos desde hoy en adelante (el mes en curso siempre aparece)
    const hoy = fechas.hoy();
    const proximos = eventos.filter((e) => fechas.dia(e.fecha) >= hoy);
    const meses = [...new Set([fechas.mesActual(), ...proximos.map((e) => fechas.mes(e.fecha))])].sort();
    const chips = [["", "Todos", proximos.length]].concat(
      meses.map((m) => [m, fechas.nombreMes(m), eventos.filter((e) => fechas.mes(e.fecha) === m).length]));
    $("meses").innerHTML = chips.map(([clave, texto, n]) =>
      `<button type="button" role="tab" class="chip ${clave === mesElegido ? "is-active" : ""}" data-mes="${clave}"
         aria-selected="${clave === mesElegido}">${texto} <span class="chip__n">${n}</span></button>`).join("");
    $("meses").querySelectorAll(".chip").forEach((b) => b.addEventListener("click", () => {
      mesElegido = b.dataset.mes;
      pintarMeses();
      pintarLista();
    }));
  }

  function pintarLista() {
    const hoy = fechas.hoy();
    const lista = mesElegido ? eventos.filter((e) => fechas.mes(e.fecha) === mesElegido)
                             : eventos.filter((e) => fechas.dia(e.fecha) >= hoy);
    $("t-mes").textContent = (mesElegido ? "Eventos de " + fechas.nombreMes(mesElegido).toLowerCase() : "Próximos eventos") +
      " (" + lista.length + ")";
    $("lista").innerHTML = lista.length ? lista.map(tarjeta).join("")
      : `<div class="card empty-state empty-state--small"><p class="muted">No hay eventos publicados${mesElegido ? " en " + fechas.nombreMes(mesElegido).toLowerCase() : " próximos"}.</p></div>`;
  }

  async function cargar() {
    try {
      // Solo los eventos publicados (activos): los cancelados o en borrador no se pueden controlar
      eventos = await API.request("/api/events/eventos");
      pintarHoy();
      pintarMeses();
      pintarLista();
    } catch (err) {
      $("hoy").innerHTML = '<p class="muted">' + esc(err.message) + "</p>";
    }
  }

  cargar();
})();
