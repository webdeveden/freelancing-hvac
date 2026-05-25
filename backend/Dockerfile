FROM node:20-alpine

WORKDIR /app

# Copy package.json and Prisma schema before install so @prisma/client postinstall
# can run prisma generate automatically
COPY backend/package.json ./
COPY backend/prisma/ ./prisma/
RUN npm install --omit=dev && npx prisma generate

# Copy backend source
COPY backend/src/ ./src/

# Copy database folder into /app/database so the seed script sits inside the
# same node_modules lookup tree as the backend (/app/node_modules).
# ESM resolves packages by walking UP from the file's location, so the script
# must live under /app to find pg, bcryptjs, etc.
COPY database/ ./database/

EXPOSE 3001

CMD ["node", "src/index.js"]
