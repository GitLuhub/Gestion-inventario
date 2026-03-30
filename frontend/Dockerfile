# =============================================================================
# Frontend Next.js — Multi-stage build 3 etapas (H1)
# Stage 1 (deps):    npm ci — cachea node_modules
# Stage 2 (builder): next build — genera .next/standalone
# Stage 3 (runner):  imagen mínima node:18-alpine con solo el output standalone
# Resultado: imagen ~70% más pequeña; node_modules de dev excluidos en producción.
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: deps — instala dependencias (cacheado si package.json no cambia)
# ---------------------------------------------------------------------------
FROM node:18-alpine AS deps

RUN apk add --no-cache libc6-compat

WORKDIR /app

COPY package.json package-lock.json* ./

RUN npm ci


# ---------------------------------------------------------------------------
# Stage 2: builder — compila la aplicación
# ---------------------------------------------------------------------------
FROM node:18-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build


# ---------------------------------------------------------------------------
# Stage 3: runner — imagen mínima de producción
# ---------------------------------------------------------------------------
FROM node:18-alpine AS runner

ARG BUILD_DATE
ARG VERSION=1.0.0

LABEL maintainer="Luis Brito" \
      org.label-schema.build-date="${BUILD_DATE}" \
      org.label-schema.description="Frontend Next.js — Gestión de Inventario" \
      org.label-schema.name="inventory-frontend" \
      org.label-schema.version="${VERSION}"

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

RUN addgroup --system --gid 1001 nodejs && \
    adduser  --system --uid 1001 nextjs

WORKDIR /app

# Archivos estáticos públicos
COPY --from=builder /app/public ./public

# Output standalone de Next.js (incluye todo lo necesario para ejecutar)
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD wget -qO- http://localhost:3000 || exit 1

CMD ["node", "server.js"]
