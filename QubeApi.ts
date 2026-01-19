
import * as http from 'http';
import { QubeAgent } from './QubeAgent';

const PORT = process.env.PORT || 3000;

/**
 * Capture console.log output.
 * WARNING: This overrides the global console.log. This is not thread-safe and
 * will cause issues if multiple requests are processed simultaneously.
 */
async function captureLogs(callback: () => Promise<void>): Promise<string[]> {
    const logs: string[] = [];
    const originalLog = console.log;

    console.log = (...args: any[]) => {
        logs.push(args.map(a => String(a)).join(' '));
        // originalLog(...args); // Uncomment to see logs in server terminal too
    };

    try {
        await callback();
        return logs;
    } catch (e) {
        logs.push(`ERROR: ${e}`);
        return logs;
    } finally {
        console.log = originalLog;
    }
}

const server = http.createServer(async (req, res) => {
    // Enable CORS for local testing/GPT interactions if needed
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.writeHead(204);
        res.end();
        return;
    }

    // Health check endpoint for Docker/Cloud Run
    if (req.method === 'GET' && req.url === '/health') {
        res.writeHead(200, { 'Content-Type': 'text/plain' });
        res.end('OK');
        return;
    }

    if (req.method === 'POST' && req.url === '/simulate') {
        try {
            const buffers = [];
            for await (const chunk of req) {
                buffers.push(chunk);
            }
            const body = buffers.length ? JSON.parse(Buffer.concat(buffers).toString()) : {};
            const duration = body.duration || 500;

            const agent = new QubeAgent();
            const logs = await captureLogs(() => agent.runSimulation(duration));

            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                status: 'success',
                output: logs.join('\n')
            }));
        } catch (err) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ status: 'error', message: err instanceof Error ? err.message : String(err) }));
        }
    } else {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('Not Found. Use POST /simulate');
    }
});

server.listen(PORT, () => {
    console.log(`Qube API Server running on port ${PORT}`);
    console.log(`To expose to GPT: Use a tunnel like 'ngrok http ${PORT}'`);
});
