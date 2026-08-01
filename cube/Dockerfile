FROM node:20-alpine

WORKDIR /cube

RUN apk add --no-cache curl python3 make g++

COPY package.json package-lock.json* ./

RUN npm ci --omit=dev || npm install --production

COPY . ./

ENV CUBEJS_DEV_MODE=false \
    NODE_ENV=production

RUN addgroup -S cube && adduser -S cube -G cube && chown -R cube:cube /cube
USER cube

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost:4000/readyz || curl -sf http://localhost:4000/ || exit 1

EXPOSE 4000

CMD ["npm", "start"]
