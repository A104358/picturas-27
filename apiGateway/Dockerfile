FROM node:26.13.1-trixie@sha256:e18c3ccdf7d71619990b0e85639f506e2028a95410999cab24cc373cbd10e0ac
WORKDIR /app

COPY . .
RUN npm install

EXPOSE 8000
CMD ["npm", "start"]