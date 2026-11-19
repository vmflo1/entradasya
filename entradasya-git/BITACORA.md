# Bitácora de instalación y despliegue · EntradasYa v1

Registre aquí cada problema de instalación, versiones o despliegue (lo pide el documento de requerimientos).

| Fecha | Servicio | Problema | Causa | Solución |
|---|---|---|---|---|
| 2026-11-16 | infra/postgres | `syntax error at or near ":"` al ejecutar `01_crear_bases.sql` | Se ejecutó en pgAdmin; las variables `:'auth_pass'` solo existen en psql | Ejecutarlo con psql (lo hace `scripts/setup.ps1`) |
| 2026-11-16 | tickets | WeasyPrint necesita GTK/Pango en Windows | Dependencia nativa del sistema | Se usa ReportLab, que se instala solo con pip |
| 2026-11-17 | orders | En Ubuntu el botón del correo no abría las entradas | `PUBLIC_URL` apuntaba a `localhost:8080`; en Ubuntu Nginx usa el puerto 80 | `PUBLIC_URL=http://localhost` en `services/orders/.env` |
| 2026-11-17 | scripts | `start.sh` mostraba `localhost:8080` en Ubuntu | Dirección escrita fija en el mensaje | Leer `PUBLIC_URL` del `.env` de orders |
| 2026-11-17 | postgres (Ubuntu) | `systemctl stop postgresql` no apagaba la base | El servidor real corre como `postgresql@18-main` | Usar `systemctl stop postgresql@18-main` |
| 2026-11-17 | pipeline | Los primeros despliegues quedaron en cola ~20 min | El runner autohospedado aún no estaba instalado | Instalar el runner como servicio (`svc.sh install`); el despliegue real tarda ~30 s |
| 2026-11-18 | tickets/checkin | El portero podía validar entradas de un evento de otro día | `validar` no revisaba la fecha | tickets compara la fecha del evento con la fecha actual de La Paz |
|  |  |  |  |  |
