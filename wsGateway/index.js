const https = require("https");
const socketIo = require('socket.io');
const jwt = require("jsonwebtoken");
const pki = require("./tls/pkiTls");

const { read_rabbit_msg } = require("./utils/rabbit_mq.js");
// HTTPS with mTLS (B5): only nginx may reach the WebSocket gateway.
const httpServer = https.createServer(pki.serverOptions());
httpServer.listen(4000);
pki.guardValidity(() => httpServer.close());

const io = socketIo(httpServer, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"],
    },
    allowRequest: (req, callback) => callback(null, pki.peerAllowed(req, ["nginx"])),
});

io.on("connection", (socket) => {
    console.log("a user connected");

    const token = socket.handshake.auth.token;
    if (token != null) {
        // Same session rules as the gateway: HS256 only, installation iss/aud, no clock tolerance.
        jwt.verify(token, process.env.JWT_SECRET_KEY, {
            complete: true,
            algorithms: ["HS256"],
            issuer: process.env.JWT_ISSUER,
            audience: process.env.JWT_AUDIENCE,
            clockTolerance: 0,
            maxAge: 7 * 24 * 60 * 60,
        }, (e, verified) => {
            if (!e && (verified.header.typ !== "picturas-session+jwt" ||
                    typeof verified.payload.sub !== "string" ||
                    verified.payload.id !== verified.payload.sub)) {
                e = new Error("Invalid session");
            }
            const payload = verified?.payload;
            if (e) {
                socket.emit('authError', e);
                return;
            }

            console.log("Connecting to room:", payload.id)
            socket.join(payload.id);
        });
    }

    socket.on("join-project", (projectId) => {
        if (typeof projectId === "string" && projectId.length > 0) {
            socket.join(`project:${projectId}`);
        }
        });


    socket.on("leave-project", (projectId) => {
        if (typeof projectId === "string" && projectId.length > 0) {
            socket.leave(`project:${projectId}`);
        }
        });
        
    socket.on("disconnect", () => {
        console.log("A user disconnected");
    });

});

// id do user como room id

function process_msg() {
    read_rabbit_msg('ws_queue', (msg) => {
        const msg_content = JSON.parse(msg.content.toString());
        const msg_id = msg_content.messageId;
        const timestamp = msg_content.timestamp
        const status = msg_content.status;
        const user = msg_content.user;

        // Video editing progress, as a percentage
        if (/update-client-video-progress/.test(msg_id)) {
            io.to(user).emit("video-progress", {
                projectId: msg_content.projectId,
                imgId: msg_content.imgId,
                preview: msg_content.preview,
                percent: msg_content.percent,
            });
        }

        else if (/update-client-preview/.test(msg_id)) {
            if (status == "error") {
                const error_code = msg_content.errorCode;
                const error_msg = msg_content.errorMsg;

                io.to(user).emit("preview-error", { error_code, error_msg }); 

                return;
            }

            const img_url = msg_content.img_url;

            io.to(user).emit("preview-ready", img_url);
        }

        else if (/update-client-process/.test(msg_id)) {

            if (status == "error") {
                const error_code = msg_content.errorCode;
                const error_msg = msg_content.errorMsg;

                io.to(user).emit("process-error", { error_code, error_msg }); 

                return;
            }

            io.to(user).emit("process-update", msg_id);
        }

        else if (msg_content.type === "project-op") {
            const projectId = msg_content.projectId;
            const op = msg_content.op;

            if (projectId && op) {
                io.to(`project:${projectId}`).emit("project-op", { projectId, op });
            }
            }

        //  project updated
        else if (/project-updated/.test(msg_id) || msg_content.type === "project-updated") {
            const projectId = msg_content.projectId;
            const version = msg_content.version;

            if (projectId) {
                io.to(`project:${projectId}`).emit("project-updated", { projectId, version });
            }
        }
    })
}

process_msg();
