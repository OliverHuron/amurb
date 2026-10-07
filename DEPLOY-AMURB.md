# AmUrb — Despliegue en producción

Sitio: **https://amurb.siafsystem.online** · Repo: `OliverHuron/amurb` · Servidor: `infraestructura` (compartido con los proyectos SIAF).

```
Internet → Cloudflare Tunnel (119ed31c…) → cloudflared → nginx :80 (server_name amurb.siafsystem.online)
             ├─ /_astro/, /frames/, /brand/ y páginas prerenderizadas → /var/www/amurb/dist/client (estático, caché)
             └─ resto (SSR) → 127.0.0.1:5011 → PM2 "amurb" → Astro (Node standalone, Node 22)
```

## Despliegue normal

`git push origin main` → GitHub Actions (`.github/workflows/deploy.yml`) → runner self-hosted
`infra-amurb` (label `amurb`) → `rsync` a `/var/www/amurb` → `npm ci` + `npm run build` con
**Node 22** (instalado por `actions/setup-node`; el sistema tiene Node 20 y Astro 7 exige ≥ 22.12)
→ `pm2 start ecosystem.config.cjs` → verificación con `curl` a `:5011`.

## Configuración del servidor (ya hecha el 2026-10-07)

| Pieza | Ubicación |
|---|---|
| App | `/var/www/amurb` (dueño `oliver`) |
| NGINX | `/etc/nginx/sites-available/amurb` (+ enlace en `sites-enabled`) |
| Tunnel | entrada `amurb.siafsystem.online` en `/etc/cloudflared/config.yml` (respaldo `config.yml.bak.<epoch>`) y CNAME creado con `cloudflared tunnel route dns` |
| Runner | `~/actions-runner-amurb`, servicio `actions.runner.OliverHuron-amurb.infra-amurb` |
| PM2 | proceso `amurb`, puerto **5011** (5001-5006 y 5010 ya están ocupados por otras apps) |

## Verificar

```bash
pm2 list                                   # amurb online
pm2 logs amurb --lines 50
curl -sI http://127.0.0.1:5011/            # en el servidor
curl -sI https://amurb.siafsystem.online   # desde fuera
```

## Notas

- No hay `.env` por ahora (sitio sin secretos). Si se agrega, guardar en `/var/www/.env.amurb` y restaurarlo en el workflow como en los proyectos SIAF.
- El despliegue hace `pm2 delete` + `pm2 start` (fork, 1 instancia): hay un corte de ~1 s. Para cero cortes, pasar a `exec_mode: 'cluster'` y `pm2 reload` (probar antes con el entry ESM de Astro).
- Archivos pesados que **no** van al repo: `desktop_frames/` (originales 5K), `blender/texturas/`, `blender/render/`, `blender/*.blend`.
