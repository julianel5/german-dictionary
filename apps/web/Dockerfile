# syntax=docker/dockerfile:1
FROM node:24-alpine

WORKDIR /repo

COPY packages/shared-types ./packages/shared-types
COPY apps/web ./apps/web

WORKDIR /repo/apps/web
RUN npm install && npm run build

EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
