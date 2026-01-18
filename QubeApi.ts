
import * as http from 'http';
import { QubeAgent } from './QubeAgent';

const PORT = 3000;

/**
 * Capture console.log output.
 */
function captureLogs(callback: () => Promise<void>): Promise<string[]> {
    return new Promise(async (resolve, reject) => {
        const logs: string[] = [];
        const originalLog = console.log;

        console.log = (...args: any[]) => {
            logs.push(args.map(a => String(a)).join(' '));
            // originalLog(...args); // Uncomment to see logs in server terminal too
        };

        try {
            await callback();
            resolve(logs);
        } catch (e) {
            logs.push(`ERROR: ${e}`);
            resolve(logs);
        } finally {
            console.log = originalLog;
        }
    });
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

    if (req.method === 'POST' && req.url === '/simulate') {
        try {
            const agent = new QubeAgent();
            const logs = await captureLogs(() => agent.runSimulation());

            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                status: 'success',
                output: logs.join('\n')
            }));
        } catch (err) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ status: 'error', message: String(err) }));
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
