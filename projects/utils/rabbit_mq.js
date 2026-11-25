const fs = require('fs');
const amqp = require('amqplib/callback_api');

const exchange = 'picturas';
const retryMs = 3000;
let activeCallbacks = 0;
const workMarker = `/run/picturas/picturas-work-${process.pid}.json`;
fs.mkdirSync("/run/picturas", { recursive: true, mode: 0o700 });
function recordWork() {
    fs.writeFileSync(`${workMarker}.tmp`, JSON.stringify({ pid: process.pid, active_count: activeCallbacks }), { mode: 0o600 });
    fs.renameSync(`${workMarker}.tmp`, workMarker);
}
recordWork();
const host = process.env.RABBITMQ_HOST;
const port = Number(process.env.RABBITMQ_PORT);
const url = `amqps://${encodeURIComponent(process.env.RABBITMQ_USER)}:${encodeURIComponent(process.env.RABBITMQ_PASS)}@${host}:${port}`;
const options = { ca: [fs.readFileSync('/run/secrets/pki/ca.crt')], servername: host,
                  rejectUnauthorized: true, heartbeat: 30 };

function send_rabbit_msg(msg, queue) {
    amqp.connect(url, options, (err, connection) => {
        if (err) {
            console.error('[rabbit] publish connection failed');
            setTimeout(() => send_rabbit_msg(msg, queue), retryMs);
            return;
        }
        connection.on('error', () => console.error('[rabbit] publish connection error'));
        connection.createConfirmChannel((channelError, channel) => {
            if (channelError) { connection.close(); return; }
            channel.on('error', () => console.error('[rabbit] publish channel error'));
            channel.checkExchange(exchange, (checkError) => {
                if (checkError) { connection.close(); return; }
                channel.publish(exchange, queue, Buffer.from(JSON.stringify(msg)), {}, (publishError) => {
                    if (publishError) console.error('[rabbit] publish failed');
                    connection.close();
                });
            });
        });
    });
}

function read_rabbit_msg(queue, callback) {
    let reconnecting = false;
    function retry() {
        if (reconnecting) return;
        reconnecting = true;
        setTimeout(() => read_rabbit_msg(queue, callback), retryMs);
    }
    amqp.connect(url, options, (err, connection) => {
        if (err) { retry(); return; }
        connection.on('error', () => console.error('[rabbit] consume connection error'));
        connection.on('close', retry);
        connection.createChannel((channelError, channel) => {
            if (channelError) { connection.close(); retry(); return; }
            channel.on('error', () => console.error('[rabbit] consume channel error'));
            channel.on('close', retry);
            channel.checkExchange(exchange, (exchangeError) => {
                if (exchangeError) { connection.close(); retry(); return; }
                channel.checkQueue(queue, (queueError) => {
                    if (queueError) { connection.close(); retry(); return; }
                    channel.consume(queue, (message) => {
                        if (!message) return;
                        activeCallbacks++; recordWork();
                        const finished = () => { activeCallbacks--; recordWork(); };
                        try {
                            const pending = callback(message);
                            if (pending && typeof pending.finally === 'function') pending.finally(finished);
                            else finished();
                        } catch (_) { finished(); console.error('[rabbit] message handler failed'); }
                        // Preserve existing acknowledgement timing; B11 owns reconciliation.
                        channel.ack(message);
                    }, { noAck: false });
                });
            });
        });
    });
}

module.exports = { send_rabbit_msg, read_rabbit_msg };
