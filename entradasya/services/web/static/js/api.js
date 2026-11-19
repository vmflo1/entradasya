/* Utilidades comunes: llamadas a /api/... (siempre a través de Nginx), sesión y formato. */
(function () {
  const TOKEN_KEY = "ey_token";
  const USER_KEY = "ey_user";

  function guardar(clave, valor) { try { localStorage.setItem(clave, valor); } catch (e) { /* sin almacenamiento */ } }
  function leer(clave) { try { return localStorage.getItem(clave); } catch (e) { return null; } }
  function borrar(clave) { try { localStorage.removeItem(clave); } catch (e) { /* nada */ } }

  class ApiError extends Error {
    constructor(status, mensaje) { super(mensaje); this.status = status; }
  }

  function mensajeDeError(data, status) {
    if (data && typeof data.detail === "string") return data.detail;
    if (data && Array.isArray(data.detail) && data.detail.length) {
      const d = data.detail[0];
      const campo = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : "";
      return (campo ? campo + ": " : "") + (d.msg || "Dato inválido").replace(/^Value error, /, "");
    }
    if (status === 502 || status === 503 || status === 504) return "Un servicio no está disponible. Intenta de nuevo.";
    return "Ocurrió un error (" + status + ")";
  }

  const API = {
    token() { return leer(TOKEN_KEY); },
    usuario() { try { return JSON.parse(leer(USER_KEY) || "null"); } catch (e) { return null; } },
    guardarSesion(data) { guardar(TOKEN_KEY, data.access_token); guardar(USER_KEY, JSON.stringify(data.usuario)); },
    cerrarSesion() { borrar(TOKEN_KEY); borrar(USER_KEY); },

    async request(path, { method = "GET", body, auth = false } = {}) {
      const headers = { "Accept": "application/json" };
      const esFormulario = body instanceof FormData;  // para subir archivos (imagen del evento)
      if (body !== undefined && !esFormulario) headers["Content-Type"] = "application/json";
      if (auth && API.token()) headers["Authorization"] = "Bearer " + API.token();
      let res;
      try {
        res = await fetch(path, {
          method, headers,
          body: body === undefined ? undefined : esFormulario ? body : JSON.stringify(body),
        });
      } catch (e) {
        throw new ApiError(0, "No hay conexión con el servidor");
      }
      const data = await res.json().catch(() => null);
      if (!res.ok) {
        if (res.status === 401 && auth) {
          API.cerrarSesion();
          irALogin();
        }
        throw new ApiError(res.status, mensajeDeError(data, res.status));
      }
      return data;
    },

    /* Descarga un archivo protegido (el enlace normal no puede enviar el token). */
    async descargar(path, nombre) {
      const res = await fetch(path, { headers: { "Authorization": "Bearer " + API.token() } });
      if (res.status === 401) { API.cerrarSesion(); irALogin(); return; }
      if (!res.ok) throw new ApiError(res.status, "No se pudo descargar el archivo");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = nombre;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 2000);
    },
  };

  function irALogin() {
    const next = encodeURIComponent(location.pathname + location.search);
    location.href = "/login?next=" + next;
  }

  function requireLogin() {
    if (!API.token()) { irALogin(); return false; }
    return true;
  }

  /* Exige un rol. Si el usuario no lo tiene, muestra un aviso en lugar de la página. */
  function requireRole(roles, contenedor) {
    if (!requireLogin()) return false;
    const u = API.usuario();
    if (u && roles.includes(u.rol)) return true;
    if (contenedor) {
      contenedor.innerHTML = '<div class="card empty-state"><p class="eyebrow">Acceso restringido</p>' +
        '<h1 class="auth__title">Esta sección es para ' + roles.join(" o ") + '</h1>' +
        '<p class="muted">Ingresa con una cuenta que tenga ese rol.</p>' +
        '<button type="button" class="btn btn--primary" id="btn-cambiar">Cambiar de cuenta</button></div>';
      document.getElementById("btn-cambiar").addEventListener("click", () => { API.cerrarSesion(); irALogin(); });
    }
    return false;
  }

  /* Página de inicio según el rol */
  function inicioPorRol(rol) {
    return rol === "organizador" ? "/organizador" : rol === "portero" ? "/portero" : "/";
  }

  /* ---- Formato ---- */
  const fmt = {
    bs(valor) { return "Bs " + Number(valor || 0).toFixed(2); },
    fecha(iso) {
      const t = new Date(iso).toLocaleDateString("es-BO", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
      return t.charAt(0).toUpperCase() + t.slice(1);
    },
    hora(iso) { return new Date(iso).toLocaleTimeString("es-BO", { hour: "2-digit", minute: "2-digit" }); },
    dia(iso) { return new Date(iso).getDate(); },
    mes(iso) { return new Date(iso).toLocaleDateString("es-BO", { month: "short" }).replace(".", ""); },
    paraInput(iso) {  // "2027-03-20T21:00" para <input type="datetime-local"> en hora de Bolivia
      const d = new Date(iso);
      const p = new Intl.DateTimeFormat("en-CA", { timeZone: "America/La_Paz", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false }).formatToParts(d);
      const g = (t) => p.find((x) => x.type === t).value;
      return g("year") + "-" + g("month") + "-" + g("day") + "T" + g("hour").replace("24", "00") + ":" + g("minute");
    },
    corta(iso) { return new Date(iso).toLocaleDateString("es-BO", { day: "2-digit", month: "2-digit", year: "numeric" }); },
  };

  function esc(texto) {
    return String(texto == null ? "" : texto)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function mostrarAlerta(el, mensaje, tipo = "error") {
    if (!el) return;
    el.textContent = mensaje;
    el.className = "alert alert--" + tipo;
    el.hidden = false;
  }

  /* ---- Menú: cada rol ve solo sus secciones ---- */
  const MENU = {
    invitado: [["/", "Cartelera"]],
    cliente: [["/", "Cartelera"], ["/mis-entradas", "Mis entradas"]],
    organizador: [["/organizador", "Eventos"]],
    portero: [["/portero", "Eventos"]],
  };

  function pintarSesion() {
    const u = API.token() ? API.usuario() : null;
    const rol = u ? u.rol : "invitado";
    const links = MENU[rol] || MENU.invitado;
    const ruta = location.pathname;
    // El enlace activo es el que más coincide con la ruta actual
    let activo = "";
    links.forEach(([href]) => {
      const coincide = href === "/" ? ruta === "/" || ruta.startsWith("/evento/") : ruta === href || ruta.startsWith(href + "/");
      if (coincide && href.length > activo.length) activo = href;
    });
    const navLinks = document.getElementById("nav-links");
    if (navLinks) {
      navLinks.innerHTML = links.map(([href, texto]) =>
        `<a href="${href}" class="nav__link${href === activo ? " is-active" : ""}">${texto}</a>`).join("");
    }
    const logo = document.getElementById("logo");
    if (logo) logo.href = inicioPorRol(rol);

    const cont = document.getElementById("nav-sesion");
    if (!cont) return;
    if (u) {
      cont.innerHTML = '<span class="nav__user">' + esc(u.nombre.split(" ")[0]) +
        (rol !== "cliente" ? ' <small class="nav__rol">' + esc(rol) + '</small>' : "") + '</span>' +
        '<button type="button" class="nav__link nav__btn" id="btn-salir">Salir</button>';
      document.getElementById("btn-salir").addEventListener("click", () => { API.cerrarSesion(); location.href = "/"; });
    } else {
      cont.innerHTML = '<a href="/login" class="btn btn--small">Ingresar</a>';
    }
  }

  /* ---- Fechas por día y mes en la hora de Bolivia ---- */
  const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
  const fechas = {
    dia(iso) { return fmt.paraInput(iso).slice(0, 10); },          // "2026-12-31"
    mes(iso) { return fmt.paraInput(iso).slice(0, 7); },           // "2026-12"
    hoy() { return fmt.paraInput(new Date().toISOString()).slice(0, 10); },
    mesActual() { return fmt.paraInput(new Date().toISOString()).slice(0, 7); },
    nombreMes(clave) {                                              // "2026-12" -> "Diciembre 2026"
      const [a, m] = clave.split("-");
      const n = MESES[Number(m) - 1];
      return n.charAt(0).toUpperCase() + n.slice(1) + " " + a;
    },
  };

  window.API = API;
  window.ApiError = ApiError;
  window.requireLogin = requireLogin;
  window.requireRole = requireRole;
  window.inicioPorRol = inicioPorRol;
  window.fmt = fmt;
  window.fechas = fechas;
  window.esc = esc;
  window.mostrarAlerta = mostrarAlerta;
  document.addEventListener("DOMContentLoaded", pintarSesion);
})();
