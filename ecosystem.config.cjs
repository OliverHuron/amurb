// PM2: servidor Node standalone de Astro para amurb.siafsystem.online.
// El workflow de despliegue exporta AMURB_NODE con la ruta de Node 22 (Astro 7 requiere >= 22.12).
module.exports = {
  apps: [
    {
      name: 'amurb',
      script: './dist/server/entry.mjs',
      interpreter: process.env.AMURB_NODE || 'node',
      cwd: __dirname,
      exec_mode: 'fork',
      instances: 1,
      max_memory_restart: '300M',
      env: {
        NODE_ENV: 'production',
        HOST: '127.0.0.1',
        PORT: 5011,
      },
    },
  ],
};
