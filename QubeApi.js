"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const http = __importStar(require("http"));
const QubeAgent_1 = require("./QubeAgent");
const PORT = process.env.PORT || 3000;
/**
 * Capture console.log output.
 * WARNING: This overrides the global console.log. This is not thread-safe and
 * will cause issues if multiple requests are processed simultaneously.
 */
async function captureLogs(callback) {
    const logs = [];
    const originalLog = console.log;
    console.log = (...args) => {
        logs.push(args.map(a => String(a)).join(' '));
        // originalLog(...args); // Uncomment to see logs in server terminal too
    };
    try {
        await callback();
        return logs;
    }
    catch (e) {
        logs.push(`ERROR: ${e}`);
        return logs;
    }
    finally {
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
            const agent = new QubeAgent_1.QubeAgent();
            const logs = await captureLogs(() => agent.runSimulation(duration));
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                status: 'success',
                output: logs.join('\n')
            }));
        }
        catch (err) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ status: 'error', message: err instanceof Error ? err.message : String(err) }));
        }
    }
    else {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('Not Found. Use POST /simulate');
    }
});
server.listen(PORT, () => {
    console.log(`Qube API Server running on port ${PORT}`);
    console.log(`To expose to GPT: Use a tunnel like 'ngrok http ${PORT}'`);
});
