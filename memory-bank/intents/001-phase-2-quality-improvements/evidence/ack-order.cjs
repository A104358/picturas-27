// Observes the real consumer helper with a fake AMQP transport; no broker is used.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { createHash } = require('node:crypto');
const { execFileSync } = require('node:child_process');

async function main() {
  const root = path.resolve(__dirname, '../../../..');
  const relativeSource = 'projects/utils/rabbit_mq.js';
  const source = fs.readFileSync(path.join(root, relativeSource), 'utf8');
  const events = [];
  let consumer;
  const channel = {
    assertExchange() {},
    assertQueue(name, options, callback) { callback(null, { queue: name }); },
    consume(name, callback) { consumer = callback; },
    ack() { events.push('ack'); },
  };
  const transport = {
    connect(url, callback) {
      callback(null, {
        createChannel(callback) { callback(null, channel); },
      });
    },
  };
  const sandbox = {
    module: { exports: {} },
    process: { env: {} },
    require(name) {
      if (name !== 'amqplib/callback_api') throw new Error(`Unexpected import: ${name}`);
      return transport;
    },
  };
  vm.runInNewContext(source, sandbox, { filename: relativeSource });
  let release;
  const blocked = new Promise(resolve => { release = resolve; });
  let callbackDone;
  sandbox.module.exports.read_rabbit_msg('exploration-only', () => {
    callbackDone = (async () => {
      events.push('callback-start');
      await blocked;
      events.push('callback-complete');
    })();
    return callbackDone;
  });
  const handlerDone = consumer({ content: Buffer.from('{}') });
  const eventsWhilePending = [...events];
  release();
  await callbackDone;
  await handlerDone;
  console.log(JSON.stringify({
    recorded_at: new Date().toISOString(),
    commit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(),
    source: relativeSource,
    source_sha256: createHash('sha256').update(source).digest('hex'),
    node: process.version,
    method: 'Real helper evaluated with a fake AMQP channel and a controlled asynchronous callback.',
    events_while_callback_pending: eventsWhilePending,
    events,
    ack_precedes_callback_completion: events.indexOf('ack') < events.indexOf('callback-complete'),
    limits: 'No real broker, database, crash or end-to-end job. Demonstrates callback order only; not message loss frequency.',
  }, null, 2));
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
