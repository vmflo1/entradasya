/* Panel Eventos (organizador): Hoy, Próximos eventos y anteriores, con filtro por mes y por día.
   Incluye sus eventos y los cargados en el sistema sin organizador (datos de prueba). */
(function () {
  const app = document.getElementById("org-app");
  if (!requireRole(["organizador"], app)) return;

  const ESTADOS = { borrador: "Borrador", publicado: "Publicado", cancelado: "Cancelado" };
  const $ = (x) => document.getElementById(x);
  const fDia = $("f-dia");
  let eventos = [];
  let mes = "";   // "" = todos los meses

  function etiquetaEstado(e) {
    return `<span class="status status--ev-${e.estado}">${ESTADOS[e.estado] || esc(e.estado)}</span>`;
  }

  /* Tarjeta pequeña para "Hoy" */
  function mini(e) {
    return `
      <a class="mini" href="/organizador/evento/${e.id}">
        <div class="mini__top">${etiquetaEstado(e)}<span class="mini__hora">${esc(fmt.hora(e.fecha))}</span></div>
        <h3 class="mini__titulo">${esc(e.nombre)}</h3>
        <p class="muted small">${esc(e.lugar)}</p>
        <p class="small"><b>${e.vendidos}</b> de ${e.cupo_total} vendidas</p>
      </a>`;
  }

  /* Fila completa para las listas */
  function fila(e) {
    const pct = e.cupo_total ? Math.round((e.vendidos / e.cupo_total) * 100) : 0;
    const esHoy = fechas.dia(e.fecha) === fechas.hoy();
    return `
      <a class="org-item ${e.estado === "cancelado" ? "is-cancelado" : ""}" href="/organizador/evento/${e.id}">
        <div class="org-item__date"><span>${fmt.dia(e.fecha)}</span><small>${esc(fmt.mes(e.fecha))}</small></div>
        <div class="org-item__body">
          <h3>${esc(e.nombre)} ${esHoy ? '<span class="status status--hoy">Hoy</span>' : ""}</h3>
          <p class="muted">${esc(fmt.fecha(e.fecha))} · ${esc(fmt.hora(e.fecha))} · ${esc(e.lugar)}</p>
          <div class="bar" aria-label="${pct}% vendido"><span style="width:${pct}%"></span></div>
          <p class="small">${e.vendidos} de ${e.cupo_total} entradas vendidas · ${e.sectores.length} sector(es)</p>
        </div>
        <div class="org-item__side">${etiquetaEstado(e)}<span class="org-item__cta">Editar →</span></div>
      </a>`;
  }

  function vacio(texto) {
    return `<div class="card empty-state empty-state--small"><p class="muted">${texto}</p></div>`;
  }

  function pintarMeses() {
    const meses = [...new Set(eventos.map((e) => fechas.mes(e.fecha)))].sort();
    const chips = [["", "Todos", eventos.length]].concat(
      meses.map((m) => [m, fechas.nombreMes(m), eventos.filter((e) => fechas.mes(e.fecha) === m).length]));
    $("meses").innerHTML = chips.map(([clave, texto, n]) =>
      `<button type="button" role="tab" class="chip ${clave === mes ? "is-active" : ""}" data-mes="${clave}"
         aria-selected="${clave === mes}">${texto} <span class="chip__n">${n}</span></button>`).join("");
    $("meses").querySelectorAll(".chip").forEach((b) => b.addEventListener("click", () => {
      mes = b.dataset.mes;
      if (fDia.value && (!mes || !fDia.value.startsWith(mes))) fDia.value = "";
      pintar();
    }));
  }

  function pintar() {
    pintarMeses();
    const hoy = fechas.hoy();

    // Hoy (siempre visible)
    $("hoy-fecha").textContent = "· " + fmt.fecha(new Date().toISOString());
    const deHoy = eventos.filter((e) => fechas.dia(e.fecha) === hoy);
    $("hoy").innerHTML = deHoy.length ? deHoy.map(mini).join("") : vacio("No hay eventos para hoy.");

    // Lista principal: próximos eventos, o los del mes / día elegido
    const dia = fDia.value;
    let lista, titulo;
    if (dia) {
      lista = eventos.filter((e) => fechas.dia(e.fecha) === dia);
      titulo = "Eventos del " + fmt.fecha(dia + "T12:00:00-04:00");
    } else if (mes) {
      lista = eventos.filter((e) => fechas.mes(e.fecha) === mes);
      titulo = "Eventos de " + fechas.nombreMes(mes).toLowerCase();
    } else {
      lista = eventos.filter((e) => fechas.dia(e.fecha) >= hoy);
      titulo = "Próximos eventos";
    }
    $("t-lista").textContent = titulo + " (" + lista.length + ")";
    $("org-list").innerHTML = lista.length ? lista.map(fila).join("")
      : vacio(eventos.length ? "No hay eventos con ese filtro." : 'Aún no hay eventos. <a href="/organizador/nuevo">Crea el primero</a>.');

    // Eventos anteriores: solo sin filtro
    const anteriores = eventos.filter((e) => fechas.dia(e.fecha) < hoy).reverse();
    $("sec-anteriores").hidden = Boolean(dia || mes) || !anteriores.length;
    $("n-anteriores").textContent = "(" + anteriores.length + ")";
    $("anteriores").innerHTML = anteriores.map(fila).join("");
  }

  fDia.addEventListener("change", () => {
    mes = fDia.value ? fDia.value.slice(0, 7) : mes;
    pintar();
  });
  $("f-limpiar").addEventListener("click", () => { mes = ""; fDia.value = ""; pintar(); });

  async function cargar() {
    try {
      eventos = await API.request("/api/events/organizador/eventos", { auth: true });
      pintar();
    } catch (err) {
      $("hoy").innerHTML = '<p class="muted">' + esc(err.message) + "</p>";
    }
  }

  cargar();
})();
