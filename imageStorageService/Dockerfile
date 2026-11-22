from node:26.13.1-trixie@sha256:e18c3ccdf7d71619990b0e85639f506e2028a95410999cab24cc373cbd10e0ac
workdir /app

copy . .
run npm install

expose 11000
cmd ["npm", "start"]