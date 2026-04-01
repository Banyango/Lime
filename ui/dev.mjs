#!/usr/bin/env node
/**
 * Dev fixture: spawns the Ink UI and feeds it fake state updates.
 * Usage: node ui/dev.mjs
 */
import { spawn } from 'child_process';
import * as readline from 'readline';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const bundle = join(__dirname, '../src/lime_ai/app/writers/ink_ui/index.js');

const proc = spawn('node', [bundle], {
    stdio: ['pipe', 'pipe', 'inherit'],
});

// Log anything the UI sends back (quit, input_response, permission_response)
const rl = readline.createInterface({ input: proc.stdout, terminal: false });
rl.on('line', (line) => {
    const msg = JSON.parse(line);
    if (msg.type === 'ui_ready') {
        console.error('[dev] UI ready — sending fake state');
        sendFakeState();
    } else {
        console.error('[dev] UI sent:', msg);
    }
});

proc.on('exit', (code) => process.exit(code ?? 0));

function send(msg) {
    proc.stdin.write(JSON.stringify(msg) + '\n');
}

function sendFakeState() {
    // --- Edit the state below to test different UI scenarios ---
    const state = {
        header: 'Dev fixture run',
        warnings: [],
        import_errors: [],
        metadata: { file: 'example.mgx' },
        memory: null,
        turns: [
            {
                run: {
                    status: 'running',
                    model: 'claude-sonnet-4-6',
                    provider: 'anthropic',
                    duration_ms: null,
                    event_name: 'running',
                    tokens: { input_tokens: 1234, output_tokens: 56, cache_read_tokens: 0, cache_write_tokens: 0 },
                    content_blocks: [
                        { type: 'response', text: 'Hello, working on it…', ref: null },
                    ],
                    tool_calls: [
                        {
                            tool_name: 'read_file',
                            tool_call_id: 'tc1',
                            arguments: { path: '/tmp/foo.py' },
                            result: 'print("hello")',
                            success: true,
                            duration_ms: 42,
                            parent_tool_call_id: null,
                        },
                        {
                            tool_name: 'write_file',
                            tool_call_id: 'tc2',
                            arguments: { path: '/tmp/bar.py', content: '…' },
                            result: null,
                            success: null,  // pending
                            duration_ms: null,
                            parent_tool_call_id: null,
                        },
                    ],
                    errors: [],
                    code_changes: null,
                    request_count: 2,
                    total_cost: 0,
                    prompt: 'Do something useful.',
                },
                function_calls: [],
            },
        ],
        pending_input: null,
        pending_permission: null,
    };

    send({ type: 'state_update', payload: state });

    // Simulate completion after 3 seconds
    setTimeout(() => {
        state.turns[0].run.status = 'completed';
        state.turns[0].run.duration_ms = 3100;
        state.turns[0].run.tool_calls[1].success = true;
        state.turns[0].run.tool_calls[1].duration_ms = 800;
        send({ type: 'state_update', payload: state });
        send({ type: 'agent_done', payload: {} });
    }, 3000);
}
