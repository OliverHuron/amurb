# AmUrb — Sitio Web Corporativo Interactivo

Contexto del proyecto para Claude. Idioma de trabajo: **español**.

**Marca (decisión 2026-10-06):** todo el sitio es de **AmUrb, Ambiental y Urbanística de Michoacán**. Es la **misma empresa que Grupo CRUBA con el nombre cambiado**: toda la información de cruba.com.mx sigue vigente. La carpeta conserva el nombre `CRUBA`. Empresa mexicana de infraestructura inteligente, logística, suministro a gobierno y defensa (SEDENA) y soluciones urbanas sustentables. Rol esperado: ingeniero de software full-stack y diseñador de experiencias 3D web.

## Stack de la aplicación

- **Framework:** Astro en modo SSR (alternativa: Next.js). Frontend y endpoints de API viven en un solo proyecto.
- **Estilos:** Tailwind CSS.
- **Interactividad:** islas de Astro. Cargar JS solo en los componentes que lo necesitan.
- **Animación:** GSAP + ScrollTrigger (scrubbing, text masking, pinning de secciones).
- **UI:** Bento Grids (tarjetas asimétricas con glow/glassmorphism en hover) para las divisiones:
  - Defensa / Gobierno
  - Infraestructura Inteligente
  - Logística
  - Materiales / CCTV

## Proyecto web (estado 2026-10-06)

- **Versiones:** Astro 7, `@astrojs/node` 11 (`mode: 'standalone'`), Tailwind v4 (`@tailwindcss/vite`, tokens en `src/styles/global.css`) y GSAP 3.15.
- **Comandos:** `npm run dev`, `npm run build`, `npm run start` (servidor de producción para PM2), `npm run check` y `npm run assets`.
- **Contenido:** centralizado en `src/data/empresa.ts`. Viene de cruba.com.mx con el nombre cambiado a AmUrb, y es vigente porque es la misma empresa. La página `/solutions` de cruba.com.mx es una plantilla de Wix sin editar: no usarla. Pendiente: la lista real de soluciones y los enlaces de Biocup y SBETech.
- **Hecho:**
  - `Navbar.astro`: logo, enlaces, teléfono, CTA, modo "glass" al hacer scroll y menú móvil accesible.
  - `HeroScroll.astro`: secuencia de frames en canvas ligada al scroll y 3 bloques de texto.
  - `index.astro`: se prerenderiza. Las secciones Nosotros, Soluciones, Marcas, Campus 3D y Contacto son provisionales.
- **Assets:** `scripts/optimizar-assets.mjs` genera `public/frames/{desktop,mobile}` y `public/brand/` a partir de `desktop_frames/` (originales 5K de 279 MB, fuera de git) y `assets-origen/`. Recorta el 7 % del borde para quitar la marca de agua "AI".
- **Identidad AmUrb:**
  - **Logos:** `logo-claro.webp` (barra de navegación: invertido para fondo oscuro, sin subtítulo) y `logo.webp` (original). Ambos se generan desde `logo_ambiental.png`.
  - **Favicon:** monograma **"AU"**, recortado del propio logotipo (A verde, U clara), en `public/favicon.png` y `public/apple-touch-icon.png`.
  - **Paleta:** `verde` `#5f8f45`, `verde-luz` `#9fd36b` (acentos), `ambar` `#ffc46b` (luminaria) y `noche` `#070b14`.
  - **CRUBA:** su logo ya no se publica; solo queda el original en `assets-origen/logo_cruba.png`.
- **Tailwind v4 / CSS:** los estilos `<style>` de los componentes no van en capa y le ganan a las utilidades. No pongas reglas genéricas como `> * { display: block }`.

## Campus fotorrealista en Blender (en curso, 2026-10-07)

- **Decisión:** el usuario no quiere Google ni nada que requiera facturación, y la vista debe ser **isométrica** (no en primera persona). La escena de Spline quedó corta en realismo, así que el campus se genera con código en **Blender 5.1.2** y se renderiza con **Cycles + OptiX** (RTX 4070 SUPER, ~9 s por frame a 1080p).
- **Código:** `blender/construir_campus.py` es el punto de entrada; los módulos están en `blender/campus/`:
  - `geo`: primitivas en metros;
  - `materiales`: PBR con texturas de Poly Haven CC0, en `blender/texturas/` (fuera de git; se descargan con `node blender/descargar-texturas.mjs`);
  - `piezas`: edificios, naves, árboles, autos, postes y cámaras;
  - `zonas`: las 10 zonas;
  - `entorno`: calles, muro, interactivos y ciudad de contexto;
  - `escena`: cielo físico `MULTIPLE_SCATTERING`, cámara ortográfica en un pivote para la órbita, ajustes y proyección de hotspots.
- **Ejecutar:** `blender -b --factory-startup --python blender/construir_campus.py -- --modo still|orbita|solo-escena [--frames 120 --muestras 128 --cielo 0.06]`.
- **Salidas:** `blender/campus.blend` y `blender/render/` (`still.png`, `orbita/frame_####.png`, `hotspots.json` con la posición 2D por frame de cada ancla de la colección `Interactivos`).
- **Plan acordado ("ambas"):**
  1. Órbita 360° prerenderizada en la web, con hotspots que siguen cada frame.
  2. Después, versión en tiempo real (glTF con luz horneada) a partir de la misma escena.
- **Notas de Blender 5.1:** el nodo Mix se usa con `data_type='RGBA'` y sockets por nombre y tipo. El cielo `MULTIPLE_SCATTERING` necesita intensidad baja (~0.06 con AgX); con 0.35 todo sale blanco. La lámina de Poly Haven `box_profile_metal_sheet` es rojiza: necesita un tinte fuerte.

### Estado al cierre de la sesión (2026-10-07) — RETOMAR AQUÍ

- **Hecho:** escena completa y render de prueba aprobado como v1 (`blender/render/still.png`).
  - **Escena:** 4.434 objetos; se construye en ~1,3 s.
  - **Las 10 zonas a escala real**, los 22 interactivos como anclas en la colección `Interactivos` (`Poste Inteligente 01–12`, `Camara CCTV 01–08`, `Subestacion 01–02`, más `Zona <clave>`) y la ciudad de contexto.
  - **Materiales:** variación de tono y brillo por edificio (`por_objeto=True`), césped verde y lámina con tinte gris.
  - **Cámara:** `ortho_scale` 370, azimut -30°, elevación 35°, cielo 0,06.
- **Opinión del usuario:** le gustó el enfoque (Blender + Cycles, isométrico). Sabe que todavía es "maqueta arquitectónica" y no "foto aérea" tipo Apple Maps.
- **Ruta del archivo:** `C:\Users\Darcketo\Desktop\CRUBA\blender\campus.blend`. **Cada ejecución del script lo sobrescribe**: las ediciones manuales deben guardarse con otro nombre.
- **Siguientes pasos, en orden.** El usuario dijo "más al rato"; confirmar antes de lanzar renders largos.
  1. **Pase de realismo:**
     - arbustos y setos en los bordes de los patios (fuente instanciable `Arbusto`);
     - farolas normales en todas las calles (fuente `Farola`, no interactivas);
     - más manchas y desgaste en azoteas (`variacion` ~0.3) y asfalto;
     - árboles más naturales (más blobs, más variación);
     - mobiliario: bancas, señales y contenedores;
     - opcional: bruma atmosférica.
  2. **Oclusión de hotspots:** en `escena.proyectar_hotspots`, `scene.ray_cast` desde la dirección de la cámara hacia cada ancla; si algo la tapa, marcar `visible: false`.
  3. **Órbita 360°:** `--modo orbita --frames 120 --muestras 128`, unos 20 min; correrla en segundo plano. Después convertir los PNG a WebP (1920 escritorio y 960 móvil) en `public/campus/{desktop,mobile}`, con un script de Node + sharp similar a `scripts/optimizar-assets.mjs`.
  4. **Visor web:** componente Astro `CampusOrbita.astro` (isla) con:
     - canvas con la secuencia; arrastrar = girar, scroll opcional con GSAP;
     - hotspots HTML posicionados con `hotspots.json` por frame, ocultos si `visible: false`;
     - clic que abre un panel con la información de `src/data/empresa.ts`. Falta escribir descripciones por zona e interactivo.
     - Va en la sección `#campus` de `index.astro`.
  5. **Tiempo real:** exportar a glTF para three.js con cámara ortográfica y OrbitControls. Los shaders procedurales (vidrio con parteluces, variación por objeto) no se exportan a glTF: habrá que hornearlos a texturas o reimplementarlos. Luz: hornear AO o lightmaps, o usar sombras en tiempo real con HDRI.
- **Spline:** la escena de Spline (sección siguiente) queda como **antecedente**; el campus definitivo es el de Blender. No borrarla sin preguntar.

## Producción (en línea desde 2026-10-07)

- **URL:** https://amurb.siafsystem.online · **Repo:** `github.com/OliverHuron/amurb` (rama `main`).
- **Servidor:** `ssh oliver@100.100.81.42` (Tailscale; host `infraestructura`). Acceso con llave y `sudo` sin contraseña.
- **Desplegar:** `git push origin main` → runner `infra-amurb` (label `amurb`) → Node 22 vía `setup-node` (el sistema tiene Node 20) → build → PM2 `amurb` en el **puerto 5011**.
- **Detalles completos:** [DEPLOY-AMURB.md](DEPLOY-AMURB.md).
- **Token de GitHub:** no se guarda en el repo ni en la configuración de Git. El push se hace con `http.extraHeader` temporal o con la credencial del usuario.

## Infraestructura (autohospedada)

- **NGINX:** proxy inverso delante de la app Node.
- **PM2:** ciclo de vida y balanceo del proceso Node en producción.
- **Cloudflare:** proxy activo (nube naranja) para caché edge, protección DDoS y SSL.
- **CI/CD:** runner local en el servidor, disparado por Git, sin cortes vía `pm2 reload`.

### Sobre `DEPLOYMENT.md`

Documenta **otro sistema** (React + Express). **No usar su stack.** Sí reutilizar su arquitectura de despliegue (NGINX, PM2, runner, Cloudflare) adaptada a Astro SSR.

## Escena 3D (Spline)

- Se edita desde aquí con el **servidor MCP de Spline** (app de escritorio, puerto local `19692`), herramientas `mcp__Spline__3d_*`.
- **Estética (decisión 2026-10-05):** realismo **estilo Apple Maps 3D, de día** (sustituye la estética nocturna original). Fondo `#e8edf2`, sol cálido con sombras. Las 18 luces nocturnas siguen en la escena, ocultas, por si se quiere un modo noche.
- **Cámara:** estrictamente **ortográfica / isométrica**.
- **Comportamiento:** reacciona al scroll. Clic/hover en postes de luz inteligentes, cámaras de seguridad y subestaciones despliega menús de información en la web.
- **Integración web:** isla de Astro con `@splinetool/runtime`. El scroll se sincroniza con GSAP y los eventos de objetos se escuchan por nombre.

### Estado actual de la escena (2026-10-05)

Campus isométrico basado en la imagen de referencia, en 3 filas. Cada zona es un grupo con nombre:

| Fila | Zonas (grupos) |
|---|---|
| Trasera (z ≈ -1750) | `Zona Construcción`, `Zona Acero`, `Zona Hidráulicos y sanitarios`, `Zona Eléctrico` |
| Media (z ≈ -250) | `Zona CCTV y tecnología`, `Sede Grupo CRUBA` (centro, x = 0), `Zona Textiles y equipo técnico` |
| Frontal (z ≈ 1300) | `Zona Logística y suministro`, `Zona Ingeniería y proyectos`, `Zona Calidad y soporte` |

Otros grupos: `Entrada Principal` (muro + portón + lema, z ≈ 2380), `Etiquetas` (placas azul marino), `Arboles` (copas y troncos fusionados), `Bases y Pasos Peatonales`. `Senalizacion Vial` es una malla fusionada. Plano base: `Terreno Urbano` (7400 × 5400). Unos 577 objetos.

Escala: superficie de las bases en y = 15. Luces activas: `Luz Sol` (direccional, con sombras) y `Luz Relleno Cielo`.

**Materiales compartidos:** `Asfalto`, `Pavimento Claro`, `Cesped`, `Muro Concreto Claro` (textura dibujada `Fachada Ventanas`, triplanar), `Vidrio Reflejante`, `Techo Lamina Metalica` (textura `Techo Membrana`).

**Elementos interactivos** (grupos en la raíz, con eventos sensores `MouseDown` + `MouseHover` sin acciones, para escucharlos desde la web):

| Nombre | Cantidad | Dónde |
|---|---|---|
| `Poste Inteligente 01`…`12` | 12 | 01–06 en z ≈ 390, 07–12 en z ≈ -930 |
| `Camara CCTV 01`…`08` | 8 | 01–04 zona CCTV, 05 portón, 06 sede, 07 logística, 08 acero |
| `Subestacion 01`, `Subestacion 02` | 2 | 01 en Eléctrico; 02 junto a la sede (820, -720) |

**Cámara web:** `Camara Isometrica Web` (OrthographicCamera, rotación x = -35°, zoom 5.3). Es la cámara de Play/exportación.

### Pendientes de la escena

- [x] Nombrar y preparar los objetos interactivos.
- [x] Optimizar: objetos 1.478 → 577, materiales 1.476 → 516.
- [x] Cámara ortográfica de Play con zoom correcto.
- [x] Realismo estilo Apple Maps de día.
- [ ] Seguir bajando objetos y materiales (aún en rojo: más de 300 objetos y de 30 materiales). Pendiente: fusionar más piezas estáticas y compartir materiales.
- [ ] Opcional: transición día → noche con el scroll, usando las luces nocturnas ocultas.

## Notas técnicas de Spline MCP (aprendidas)

- `select(filtro)` + `position()`/`translate()` aplica a toda la selección. `get('selection')` y los callbacks de `iterate` no devuelven datos fiables. Para verificar, usa `get_scene` / `get_objects`.
- Los filtros con caracteres acentuados (ñ, á…) pueden fallar. Usa nombres ASCII en los objetos que haya que seleccionar desde código.
- Los `Text` necesitan un `width` explícito (≈ caracteres × fontSize × 0.6). Su glifo se dibuja más arriba que su posición: compensa en y.
- Las capturas `view: 'live'` tienen un presupuesto limitado por tarea. Verifica la vista final al final, no a mitad del trabajo.
- No usar `tree` como nombre de función local: choca con un alias del DSL.
- Los filtros de `select(o => …)` se evalúan **de forma diferida**. Dentro de un bucle, captura la variable en una `const` antes del filtro; si no, todos los filtros ven el último valor y crean grupos vacíos.
- `select(o => o.color('#hex'))` tiene tolerancia: tonos parecidos entran juntos.
- `merge()` necesita al menos 2 mallas. Si falla, el resto de la llamada se omite.
- `group(target)` no acepta un array de IDs: primero `select` y luego `group()`.
- **Cámara ortográfica de escena:** `add('OrthographicCamera')` crea una perspectiva. Hay que activarla con `activateCamera` y luego llamar a `camera('orthographic')`. El zoom se ajusta con `camera({ zoom: N })`; la distancia no cambia el tamaño.
- **Textura triplanar:** un `repeat` **menor** da ventanas **más grandes** (fachadas: ~0.35).
- El editor a veces queda en modo Play: llama a `stop()` antes de editar.
