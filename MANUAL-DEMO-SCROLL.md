# Manual — Demo scroll para grabar videos de portfolio

Sistema para grabar screencasts prolijos de una página: un botón recarga la
página, se oculta a sí mismo, espera a que terminen las animaciones de entrada
y hace un scroll automático a velocidad constante hasta el final. Hecho en
jul 2026 para grabar la home de Perma; sirve como receta para cualquier proyecto.

**Para Claude:** si Mariano menciona grabar un video/screencast de un sitio para
su portfolio, preguntale si quiere montar este sistema y seguí este manual.
En este repo, `js/demo-scroll.js` ya existe "desconectado" (ninguna página lo
carga): solo hay que reconectarlo (paso 2). En otros proyectos, crear ambas partes.

---

## 1. Piezas del sistema

Dos partes, ambas temporales:

- `js/demo-scroll.js` — toda la lógica. En este repo ya está escrito y queda
  guardado aunque desconectado.
- Dos `<button>` + un `<script>` en el HTML de la página a grabar — es lo único
  que se saca/pone para activar o desactivar el sistema.

## 2. Conectar (activar el modo demo)

Pegar esto en `index.html` (o la página que sea), justo antes de `</body>`,
después del script principal:

```html
<!-- DEMO SCROLL: temporal, para grabar el portfolio. Borrar botón + script al terminar -->
<button id="demo-scroll-btn" type="button"
    style="position:fixed; bottom:16px; left:16px; z-index:9999; padding:10px 16px; border:none; border-radius:8px; background:#1a1a1a; color:#fff; font-size:14px; cursor:pointer; opacity:0.85;">
    🎥 Demo scroll
</button>
<button id="demo-scroll-btn-fast" type="button"
    style="position:fixed; bottom:16px; left:150px; z-index:9999; padding:10px 16px; border:none; border-radius:8px; background:#1a1a1a; color:#fff; font-size:14px; cursor:pointer; opacity:0.85;">
    ⚡ Demo scroll rápido
</button>
<script src="js/demo-scroll.js" defer></script>
```

## 3. Cómo funciona `demo-scroll.js`

Flujo: click en un botón → guarda la velocidad elegida en `sessionStorage` →
espera 500 ms (para sacar el mouse de la pantalla) → recarga. Al volver a
cargar, detecta el flag, lo consume, **elimina los botones** (no salen en el
video), espera a que terminen las animaciones del hero y scrollea con
`requestAnimationFrame` hasta el fondo.

Perillas de configuración (constantes al inicio del archivo):

- `SPEED_NORMAL = 220` — px por segundo del botón 🎥.
- `SPEED_FAST = 420` — px por segundo del botón ⚡.
- `HERO_ANIMATION_END = 2600` — ms de espera post-carga antes de scrollear.
  En Perma: las fotos del hero animan con delay 0.3s + duración 2s (ver
  `heroRevealRight/Down` en `css/home.css`) = 2.3s, más margen. En otro
  proyecto, medir la animación de entrada más larga y ajustar.

## 4. Gotchas (los tres bugs que ya nos comimos)

1. **`scroll-behavior: smooth` en el CSS** (en Perma: `css/style.css`, en el
   `html`). Llamar `scrollTo` en cada frame reinicia la animación smooth 60
   veces por segundo y el scroll queda clavado en 0. Solución (ya incluida en
   el script): setear `document.documentElement.style.scrollBehavior = "auto"`
   antes de scrollear y restaurar al terminar.
2. **El scroll quedaba corto**: las imágenes lazy y el contenido async (reviews)
   agrandan la página mientras se scrollea, así que `scrollHeight` calculado
   una sola vez al inicio queda desactualizado. Solución (ya incluida):
   recalcular `maxY` en cada frame + `scrollTo` final de ajuste.
3. **Caché del JS**: si el script principal se versiona (`main.js?v=8`), los
   cambios de JS pueden no verse al recargar. Probar siempre con Cmd+Shift+R.

## 5. Visualizar localmente con funciones serverless (netlify dev)

Solo necesario si la página usa funciones de Netlify (en Perma: las reviews
vienen de `/.netlify/functions/get-reviews`). Live Server NO sirve funciones.

```bash
cd <carpeta-del-proyecto>
npm install -g netlify-cli   # solo la primera vez
netlify login                # solo la primera vez (cuenta dueña del sitio)
netlify link                 # solo la primera vez: opción "Use current git remote origin"
netlify dev --port 5500
```

Abre `http://localhost:5500` con los archivos LOCALES (botones de demo
incluidos) pero con las variables de entorno del sitio real, así las funciones
andan. No toca el sitio publicado ni requiere commit/push.

Ojo: en Perma, `loadReviews()` en `js/main.js` saltea el fetch solo en
`file://`; en localhost intenta el fetch normal (se relajó el guard en jul 2026
justamente para que funcione con netlify dev).

Alternativa sin CLI local: `netlify deploy` (SIN `--prod`) sube un borrador a
una URL única de prueba sin pisar producción.

## 6. Grabar (macOS)

1. `Cmd+Shift+5` → "Grabar porción seleccionada", recuadro sobre el navegador.
2. En Opciones: desactivar "Mostrar clics del mouse".
3. Grabar → click en el botón de demo → sacar el mouse (hay 0.5s + 2.6s).
4. Frenar con el botón ⏹ de la barra de menú.
5. Recortar puntas con QuickTime (`Cmd+T`).

## 7. Desconectar al terminar (IMPORTANTE)

Borrar de `index.html` el bloque completo del paso 2 (los dos botones + el
`<script>` + el comentario). `js/demo-scroll.js` puede quedar en el repo:
desconectado no lo carga nadie y pesa 0 para el usuario real. Verificar:

```bash
grep -rn "demo-scroll" *.html
```

No debe devolver nada. **Nunca deployar con los botones conectados.**
