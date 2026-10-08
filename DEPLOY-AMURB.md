# AmUrb — Despliegue en producción

Sitio: **https://amurb.com.mx** (www redirige con 301 a la versión sin www) · Repo: `OliverHuron/amurb`.

Servidor: **VPS propio** `amurb-vps` (Ubuntu 24.04, 1 vCPU, 3,8 GB). Acceso **solo por Tailscale con llave**:

```bash
ssh root@100.97.61.87
```

La IP pública (`2.25.200.198`) tiene el SSH y el HTTP cerrados con `ufw`, y no hay acceso con contraseña. Si Tailscale fallara, la única entrada es la consola web del proveedor del VPS.

```
Internet → Cloudflare (proxy) → Cloudflare Tunnel "amurb" (7d6b74e6…) → cloudflared → nginx :80
             ├─ /_astro/, /frames/, /brand/ y páginas prerenderizadas → /var/www/amurb/dist/client
             ├─ /recorrido/ → /var/www/amurb-media/recorrido (frames del recorrido 3D, fuera del repo)
             └─ resto (SSR) → 127.0.0.1:5011 → PM2 "amurb" (usuario amurb) → Astro (Node 22)
```

## Despliegue normal

`git push origin main` → GitHub Actions (`.github/workflows/deploy.yml`) → runner `amurb-vps`
(label `amurb-vps`, usuario `amurb`) → `rsync` a `/var/www/amurb` → `npm ci` + `npm run build`
→ `pm2 start ecosystem.config.cjs` → verificación con `curl` a `:5011`.

- El daemon de PM2 corre como servicio systemd **`pm2-amurb`**. El paso de PM2 lleva `RUNNER_TRACKING_ID: ''`; sin eso, el runner mata la app al terminar el job.
- **Frames del recorrido** (no van a git):
  1. `npm run assets:recorrido`
  2. Subirlos con:
     ```bash
     cd public && tar -cf - recorrido | ssh root@100.97.61.87 'tar -xf - -C /var/www/amurb-media && chown -R amurb:amurb /var/www/amurb-media'
     ```

## Configuración del servidor (2026-10-08)

| Pieza | Ubicación |
|---|---|
| App | `/var/www/amurb` (dueño `amurb`) |
| Frames del recorrido | `/var/www/amurb-media/recorrido/{desktop,mobile}` |
| NGINX | `/etc/nginx/sites-available/amurb` y `amurb-www` (redirección 301 de www) |
| Tunnel | `/etc/cloudflared/config.yml` + credenciales en `/etc/cloudflared/`, servicio `cloudflared`. DNS creado con `cloudflared tunnel route dns` |
| Runner | `/home/amurb/actions-runner`, servicio `actions.runner.OliverHuron-amurb.amurb-vps` |
| PM2 | servicio `pm2-amurb`, proceso `amurb`, puerto 5011 |
| SSH | `/etc/ssh/sshd_config.d/00-amurb.conf` (solo llaves) + `ufw` (entrada solo por `tailscale0` y 41641/udp) |

## Verificar

```bash
ssh root@100.97.61.87 'sudo -iu amurb pm2 list; curl -sI http://127.0.0.1:5011/ | head -1'
curl -sI https://amurb.com.mx | head -1
```

Usa siempre `sudo -iu amurb`, con sesión: `sudo -u amurb` desde `/root` falla con `EACCES`.

## SEO

- `robots.txt`, `sitemap.xml` y una clave de **IndexNow** (`public/<clave>.txt`) en `public/`.
- **Google Search Console:** propiedad de dominio `amurb.com.mx`, verificada con un registro TXT en Cloudflare. Se envía el sitemap y se pide la indexación.

## Servidor anterior (antecedente)

`amurb.siafsystem.online` en el servidor `infraestructura` (`100.100.81.42`): PM2 `amurb` en :5011 y runner `infra-amurb`. El workflow ya no lo usa. Pendiente decidir si se retira.
