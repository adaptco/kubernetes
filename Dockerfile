# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /usr/src/app

COPY package*.json ./
RUN npm install
COPY . .
RUN npx tsc

# Remove dev dependencies to keep the image small
RUN rm -rf node_modules

# Stage 2: Production
FROM node:20-alpine

WORKDIR /usr/src/app

# Copy compiled artifacts from builder
COPY --from=builder /usr/src/app .

# Add health check using wget (built-in to Alpine)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:${PORT:-3000}/health || exit 1

# NOTE: Run docker build from the parent directory (Downloads) to include package.json
# docker build -f Qube/Dockerfile -t qube-agent .
CMD [ "node", "QubeApi.js" ]