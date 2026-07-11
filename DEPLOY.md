# Publicar la invitación en tu VPS (link propio para mobile)

La invitación es **un solo archivo** (`invitacion-christian-60.html`), 100%
autocontenido. En el navegador del celular se ve nativo, a pantalla completa.

> Nota: el link de claude.ai ya funciona en mobile. Hostearla en tu VPS te da
> **URL propia** (ej. `https://cumple.tudominio.com`), sin marca de terceros, y
> te habilita usar **fotos como archivos** y — si algún día querés — un RSVP
> propio.

## Opción rápida — Caddy (HTTPS automático)

```bash
# 1) Copiá el archivo a tu VPS
scp invitacion-christian-60.html usuario@TU_VPS:/var/www/cumple/index.html
# (si tenés fotos, copiá también la carpeta img/)
scp -r img usuario@TU_VPS:/var/www/cumple/

# 2) En el VPS, /etc/caddy/Caddyfile:
cumple.tudominio.com {
    root * /var/www/cumple
    file_server
    encode gzip
}

# 3) Recargá Caddy
sudo systemctl reload caddy
```

Apuntá el DNS de `cumple.tudominio.com` (registro A) a la IP del VPS y listo:
Caddy saca el certificado HTTPS solo.

## Opción Nginx

```nginx
server {
    listen 80;
    server_name cumple.tudominio.com;
    root /var/www/cumple;
    index index.html;
}
```

Después corré `certbot --nginx -d cumple.tudominio.com` para el HTTPS.

## Fotos (cuando la hosteás en el VPS)

1. Poné las imágenes en `/var/www/cumple/img/` (ej. `1.jpg`, `2.jpg`, `3.jpg`).
2. En `invitacion-christian-60.html`, en el `<script>`, cargá el array:

```js
var PHOTOS = [
  { src: "img/1.jpg", cap: "Christian y la celeste" },
  { src: "img/2.jpg", cap: "De viaje" },
  { src: "img/3.jpg", cap: "Los 60, a puro rock" },
];
```

(Con archivos locales no hace falta convertir a base64 — sólo funciona cuando la
página está en tu dominio, no en el link de claude.ai.)

---

¿Querés que te deje esto andando? Pasame el dominio/subdominio que vas a usar y
te dejo el `Caddyfile`/config exactos y el bloque `PHOTOS` listo para pegar.
