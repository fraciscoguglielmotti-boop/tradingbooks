# RSVP — Cumple 60 de Christian ✈️🎉

Objetivo: que los invitados confirmen con un toque y vos veas, **en vivo y sin
trabajo manual**, quién viene y cuántas personas van en total.

Arquitectura elegida: **Google Form → Google Sheet** (sin servidor, no se
rompe, gratis).

---

## Paso 1 — Cargá la lista de invitados

1. Entrá a [Google Sheets](https://sheets.google.com) → **Archivo → Importar**
   → subí `lista-invitados.csv` (está en esta misma carpeta).
2. Completá una fila por **hogar** (no por persona): parejas/familias en una
   sola fila. Columnas:
   - **Nombre**, **Telefono** (con código país, ej. `5491122334455`),
     **Grupo/Familia**, **Personas_estimadas** (cuántos calculás que son).
   - **Estado**, **Personas_confirmadas**, **Tema_DJ**, **Notas** → se llenan
     solas más adelante (dejalas vacías).

Guardá esta hoja como pestaña **`Invitados`**.

---

## Paso 2 — Creá el formulario de confirmación

1. En [Google Forms](https://forms.google.com) → formulario en blanco.
   Título: **"Confirmá tu embarque — Cumple 60 de Christian"**.
2. Agregá estas preguntas:
   | Pregunta | Tipo | Obligatoria |
   |---|---|---|
   | Tu nombre y apellido | Respuesta corta | Sí |
   | ¿Venís? | Opción múltiple: *Sí, ahí estoy* / *No puedo* | Sí |
   | ¿Cuántos van en total? (contándote) | Respuesta corta (número) | Sí |
   | Nombres de los que te acompañan | Respuesta corta | No |
   | Un tema que no puede faltar (para el DJ) | Respuesta corta | No |
   | Mensaje para Christian (opcional) | Párrafo | No |
3. Arriba a la derecha → pestaña **Respuestas** → ícono de **Sheets** →
   "Crear hoja de cálculo". Elegí **vincular al mismo Sheet** que armaste en el
   Paso 1 (se crea una pestaña nueva, ej. `Respuestas de formulario 1`).
4. Botón **Enviar** → ícono de **enlace** 🔗 → **Copiar** el link (activá
   "acortar URL" si querés). Ese es tu `FORM_URL`.

---

## Paso 3 — Enganchá el formulario a la invitación

En `invitacion-christian-60.html`, arriba del todo del `<script>`, pegá tu link:

```js
var FORM_URL = "https://forms.gle/TU-LINK-ACA";
```

Listo: el botón **"Confirmar asistencia"** de la invitación abre tu formulario.
(Avisame y lo cargo yo cuando tengas el link.)

---

## Paso 4 — Que el Sheet marque solo quién confirmó

En la pestaña **`Invitados`**, en la columna **Estado**, pegá esta fórmula en la
primera fila de datos (fila 2) y arrastrala para abajo. Busca el nombre en las
respuestas del formulario y trae el estado:

```
=IFERROR(
   INDEX('Respuestas de formulario 1'!$C:$C,
         MATCH(A2, 'Respuestas de formulario 1'!$B:$B, 0)),
   "Pendiente")
```

> Ajustá las letras de columna según dónde caigan "nombre" (col. B) y "¿Venís?"
> (col. C) en tu pestaña de respuestas.

Para **Personas_confirmadas**, misma idea apuntando a la columna "¿Cuántos van?".

**Total de cabezas confirmadas** (para el salón/catering), en cualquier celda:

```
=SUMIF(E2:E, "Sí, ahí estoy", F2:F)
```

---

## Paso 5 — Enviar la invitación a los 50 (por WhatsApp)

- **A mano / lista de difusión** (más seguro, sin riesgo de bloqueo): copiás el
  link de la invitación y lo mandás. Un mensaje por hogar.
- **Automatizado desde tu VPS** (si querés): un script con `whatsapp-web.js`
  lee la columna *Telefono* del Sheet y manda el link. **Importante:** poné
  varios segundos de delay entre mensaje y mensaje para que WhatsApp no te
  bloquee. (Si vas por acá, decime y te dejo el script.)

Texto sugerido:
> ¡{Nombre}! 🎉 Christian cumple 60 y no podés faltar. Toda la info y la
> confirmación, en esta invitación 👉 {link}

---

## ¿Preferís que lo reconcilie yo?

Cuando empiecen a confirmar, **pegame acá el contenido del Sheet** (o exportá a
CSV) y te devuelvo: quién confirmó, quién falta, y el total de personas. Sin que
toques ninguna fórmula.
