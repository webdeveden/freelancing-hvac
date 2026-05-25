FROM node:22-alpine

RUN apk upgrade --no-cache

WORKDIR /app

# Copy package.json and Prisma schema before install so @prisma/client postinstall
# can run prisma generate automatically
COPY backend/package.json ./
COPY backend/prisma/ ./prisma/
RUN npm install --omit=dev && npx prisma generate

# Copy backend source
COPY backend/src/ ./src/

EXPOSE 3001

CMD ["node", "src/index.js"]
