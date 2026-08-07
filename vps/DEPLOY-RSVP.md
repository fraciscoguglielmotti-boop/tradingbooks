# RSVP + invitación en tu VPS (206.81.11.133)

Un servidor en **Python puro** (no instala nada) que:
- muestra la invitación,
- recibe las confirmaciones y las guarda en `rsvp.jsonl`,
- te da un **panel** en `/admin?key=TU_CLAVE` (con total de personas + descarga CSV).

Archivos que necesitás (te los mandé por el chat): `invitacion-christian-60.html` y `server.py`.

---

## 1) Subir los archivos al VPS
Desde tu compu (en la carpeta donde los bajaste):

```bash
ssh root@206.81.11.133 "mkdir -p /opt/cumple"
scp invitacion-christian-60.html root@206.81.11.133:/opt/cumple/index.html
scp server.py                    root@206.81.11.133:/opt/cumple/server.py
```

> El archivo de la invitación tiene que llamarse **`index.html`** en el server (por eso el `scp` lo renombra).

## 2) Probarlo una vez
```bash
ssh root@206.81.11.133
# Si ya tenías algo sirviendo en el puerto 80, primero liberalo:
#   fuser -k 80/tcp        # (o: systemctl stop nginx)
cd /opt/cumple
PORT=80 ADMIN_KEY="PONE-UNA-CLAVE-SECRETA" python3 server.py
```
Abrí en el navegador:
- `http://206.81.11.133/` → la invitación
- `http://206.81.11.133/admin?key=PONE-UNA-CLAVE-SECRETA` → el panel

Frená con `Ctrl+C`.

## 3) Dejarlo prendido siempre (systemd)
Creá el archivo `/etc/systemd/system/cumple.service`:

```ini
[Unit]
Description=Invitacion Cumple 60 Christian
After=network.target

[Service]
WorkingDirectory=/opt/cumple
Environment=PORT=80
Environment=ADMIN_KEY=PONE-UNA-CLAVE-SECRETA
ExecStart=/usr/bin/python3 /opt/cumple/server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Y activalo:
```bash
systemctl daemon-reload
systemctl enable --now cumple
systemctl status cumple      # debe decir "active (running)"
```

Las confirmaciones se guardan en `/opt/cumple/rsvp.jsonl` (no se borran al reiniciar).

## 4) Ver las confirmaciones
`http://206.81.11.133/admin?key=TU_CLAVE`
→ tarjetas con **cuántos confirmaron**, **total de personas** (para el salón/catering), **quién no puede**, la tabla completa con **restricciones alimenticias**, y botón para **descargar CSV**.

---

## 5) (Recomendado) HTTPS + dominio → candado y link lindo
1. Registrá un dominio (ej. `los60dechristian.com`) y creá un registro **A** apuntando a **206.81.11.133**.
2. Instalá **Caddy** (saca el certificado HTTPS solo):
   ```bash
   apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
   curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
   curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
   apt update && apt install -y caddy
   ```
3. Pasá el server al puerto **8080**: en `cumple.service` cambiá `Environment=PORT=8080`, luego:
   ```bash
   systemctl daemon-reload && systemctl restart cumple
   ```
4. Editá `/etc/caddy/Caddyfile`:
   ```
   los60dechristian.com {
       reverse_proxy 127.0.0.1:8080
   }
   ```
   ```bash
   systemctl reload caddy
   ```
   Listo: `https://los60dechristian.com` con candado 🔒. (Avisame el dominio y te doy el Caddyfile exacto + las etiquetas de preview para WhatsApp.)

---

## Links personalizados por invitado
La invitación lee `?p=` de la URL:
- `https://TU-DOMINIO/?p=Carlos y Josefa` → dice *"Hola Carlos y Josefa 👋"* y precarga ese nombre en el RSVP.
- `https://TU-DOMINIO/?p=Pepe` → *"Hola Pepe 👋"*.

Cuando tengas el Google Sheet (Saludo · Teléfono), yo te genero **por cada fila** el link + el mensaje de WhatsApp listo para enviar.
