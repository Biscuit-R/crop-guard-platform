FROM node:22-alpine AS builder
WORKDIR /app
# 先拷清单再装依赖 —— 缓存键只含 package.json / lock
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
