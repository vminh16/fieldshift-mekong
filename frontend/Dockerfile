# Production build of the SPA, served by Caddy. API is reached same-origin at /v1.
# Build context = repo root: the frontend imports ../contracts.
FROM node:22-alpine AS build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY contracts /app/contracts
COPY frontend ./
ENV VITE_API_BASE_URL=""
RUN npm run build

FROM caddy:2-alpine
COPY --from=build /app/frontend/dist /srv
# /v1 goes to the compose `api` service, so the stack also works standalone (laptop fallback).
# On the VM the host Caddy already routes /v1 to the API before requests reach this container.
COPY <<CADDY /etc/caddy/Caddyfile
:80 {
	encode gzip
	handle /v1/* {
		reverse_proxy api:8000
	}
	handle {
		root * /srv
		file_server
	}
}
CADDY
