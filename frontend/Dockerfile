FROM node:18

WORKDIR /usr/src/app

COPY package.json ./
RUN npm install -g bun
RUN bun i
COPY . .
# para produção:
RUN bun run build

EXPOSE 3000
# para produção: Next behind nginx over mTLS (B5), own HTTPS server with the normal build
CMD ["node", "server-https.js"]
# para dev:
# CMD ["bun", "dev"]
