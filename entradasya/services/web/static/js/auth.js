/* Ingreso y registro. Al terminar, vuelve a la página desde donde se pidió ingresar. */
(function () {
  const params = new URLSearchParams(location.search);
  const nextRaw = params.get("next") || "/";
  const next = nextRaw.startsWith("/") && !nextRaw.startsWith("//") ? nextRaw : "/";
  const alerta = document.getElementById("alert");

  // Conserva el destino al cambiar entre ingresar y registrarse
  ["link-registro", "link-login"].forEach((id) => {
    const a = document.getElementById(id);
    if (a && next !== "/") a.href += "?next=" + encodeURIComponent(next);
  });

  async function enviar(form, path, cuerpo) {
    const boton = form.querySelector("button[type=submit]");
    boton.disabled = true;
    alerta.hidden = true;
    try {
      const data = await API.request(path, { method: "POST", body: cuerpo });
      API.guardarSesion(data);
      // Sin destino pedido: cada rol va a su pantalla principal
      location.href = next === "/" ? inicioPorRol(data.usuario.rol) : next;
    } catch (e) {
      mostrarAlerta(alerta, e.message);
      boton.disabled = false;
    }
  }

  const login = document.getElementById("login-form");
  if (login) {
    login.addEventListener("submit", (e) => {
      e.preventDefault();
      enviar(login, "/api/auth/login", { email: login.email.value, password: login.password.value });
    });
  }

  const registro = document.getElementById("registro-form");
  if (registro) {
    registro.addEventListener("submit", (e) => {
      e.preventDefault();
      if (registro.password.value.length < 6) return mostrarAlerta(alerta, "La contraseña debe tener al menos 6 caracteres.");
      enviar(registro, "/api/auth/registro", {
        nombre: registro.nombre.value, email: registro.email.value, password: registro.password.value,
      });
    });
  }
})();
