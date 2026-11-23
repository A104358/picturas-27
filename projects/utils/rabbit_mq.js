const fs = require('fs');
const amqp = require('amqplib/callback_api');

const exchange = 'picturas';
const retryMs = 3000;
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
                        try { callback(message); }
                        catch (_) { console.error('[rabbit] message handler failed'); }
                        channel.ack(message);
                    }, { noAck: false });
                });
            });
        });
    });
}

module.exports = { send_rabbit_msg, read_rabbit_msg };
