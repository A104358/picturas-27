from node:26.13.1-trixie@sha256:e18c3ccdf7d71619990b0e85639f506e2028a95410999cab24cc373cbd10e0ac
# ffprobe to validate videos on upload
run apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
workdir /app

copy . .
run npm install

expose 9001
cmd ["npm", "start"]