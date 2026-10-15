# Etapa 1: compilar el frontend (Vue + Vite)
FROM node:24-alpine AS build

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY frontend/ ./
RUN npm run build


# Etapa 2: nginx sirve el frontend y hace proxy a la API
FROM nginx:stable-alpine

COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /frontend/dist /usr/share/nginx/html/mesa_ayuda
