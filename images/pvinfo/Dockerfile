# PV Info — web UI for browsing ChannelFinder PV metadata
# (https://github.com/ChannelFinder/pvinfo), built from a pinned tag and
# served by nginx. The same nginx reverse-proxies ChannelFinder and the
# archiver retrieval webapp so the browser only talks to one origin
# (ChannelFinder 4.7.x has no CORS configuration).
FROM node:20-alpine AS build

ARG PVINFO_VERSION=2.8.2

RUN apk add --no-cache git \
    && git clone --depth 1 --branch ${PVINFO_VERSION} \
        https://github.com/ChannelFinder/pvinfo.git /app
WORKDIR /app
RUN npm ci --silent

# Site settings are baked into the bundle at build time (Vite).
COPY pvinfo.env /app/.env.local
RUN npm run build

# ---------------------------------------------------------------- runtime
FROM nginx:1.27-alpine

# pvinfo's vite.config.js sets outDir to "build" (CRA compatibility)
COPY --from=build /app/build /usr/share/nginx/html/pvinfo
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
