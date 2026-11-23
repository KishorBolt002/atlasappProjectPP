import fs from "fs"
import path from "path"
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    }
  },
  build: {
    target: 'esnext',
    modulePreload: { polyfill: false },
    sourcemap: false,
    reportCompressedSize: false
  },
  preview: {
    host: '0.0.0.0',
    port: parseInt(process.env.APP_PORT || '5000'),
    strictPort: true,
    open: false,
    allowedHosts: true,
    cors: {
      origin: '*',
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization'],
    },
    headers: {
      'Cache-Control': 'no-store, no-cache, must-revalidate',
    },
    // Proxy /api to the backend when VITE_ENABLE_PROXY=true.
    ...(process.env.VITE_ENABLE_PROXY === 'true' && (() => {
      const { owner_email, owner_name, app_id } = JSON.parse(
        fs.readFileSync(path.resolve(__dirname, "../project.json"), "utf8")
      )
      // The platform proxies validate the signed-in user's session and forward
      // it as X-Atlas-User-Session, which the protected connected-agents routes
      // require. The platform stages an equivalent builder session per prompt,
      // so dev requests read it fresh on every request.
      const sessionTokenPath = app_id
        ? `/workspace/work/connected-app-sessions/${app_id}/runtime-session`
        : null
      const readSessionToken = () => {
        if (!sessionTokenPath) return null
        try {
          const token = fs.readFileSync(sessionTokenPath, "utf8").trim()
          return token || null
        } catch {
          return null
        }
      }

      return {
        proxy: {
          '/api': {
            target: 'http://localhost:8000',
            changeOrigin: true,
            configure(proxy) {
              proxy.on('proxyReq', (proxyReq, req) => {
                // The workspace dev proxy stands in for the platform proxies, which
                // always send the user's Atlas ID; per-user code paths (per-user MCP
                // servers) require it, so dev requests must carry it too.
                const userId = (process.env.USER_ID || '').trim()
                if (userId && req.headers['atlas-user-id'] === undefined) {
                  proxyReq.setHeader('Atlas-User-Id', userId)
                }
                if (req.headers['atlas-user-email'] === undefined) {
                  proxyReq.setHeader('Atlas-User-Email', owner_email.trim().toLowerCase())
                }
                if (req.headers['atlas-user-name-b64'] === undefined) {
                  proxyReq.setHeader(
                    'Atlas-User-Name-B64',
                    Buffer.from(owner_name.trim(), 'utf8').toString('base64')
                  )
                }
                // Stand in for the visitor's address the platform proxies send.
                // A connection the browser already closed has no address left.
                if (req.headers['x-atlas-client-ip'] === undefined && req.socket.remoteAddress) {
                  proxyReq.setHeader('X-Atlas-Client-IP', req.socket.remoteAddress)
                }
                if (req.headers['x-atlas-user-session'] === undefined) {
                  const sessionToken = readSessionToken()
                  if (sessionToken) {
                    proxyReq.setHeader('X-Atlas-User-Session', sessionToken)
                  }
                }
              })
            },
          },
        },
      }
    })())
  }
})
