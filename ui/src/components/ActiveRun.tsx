import React from 'react';
import {Box, Text, useInput} from 'ink';
import type {RunStatusValue, TurnData, ToolCall} from '../types';

const STATUS_ICON: Record<RunStatusValue, string> = {
    starting: '○',
    running: '◉',
    idle: '◎',
    completed: '●',
    error: '✗',
};

const STATUS_COLOR: Record<RunStatusValue, string> = {
    starting: 'gray',
    running: 'yellow',
    idle: 'cyan',
    completed: 'green',
    error: 'red',
};

interface ActiveRunProps {
    turn: TurnData;
    index: number;
    hasOverlay: boolean;
    showContext: boolean;
}

/** Dynamically rendered active (in-progress) run — redrawn on every state update. */
export default function ActiveRun({
    turn,
    index,
    hasOverlay,
}: ActiveRunProps): React.JSX.Element {
    const run = turn.run;

    useInput((_input, _key) => {}, {isActive: !hasOverlay});

    if (!run) return <Box />;

    const statusIcon = STATUS_ICON[run.status] ?? '○';
    const statusColor = STATUS_COLOR[run.status] ?? 'gray';
    const totalTokens = run.tokens.input_tokens + run.tokens.output_tokens;

    const allTcs: ToolCall[] = run.tool_calls;
    const pendingToolCall = [...allTcs].reverse().find((tc) => tc.success === null) ?? null;
    const committedTcCount = allTcs.filter((tc) => tc.success !== null).length;

    const latestResponse =
        run.content_blocks
            .filter((b) => b.type === 'response' && b.text)
            .at(-1)?.text ?? null;

    let argsSnippet = '';
    if (pendingToolCall?.arguments) {
        try {
            argsSnippet = JSON.stringify(pendingToolCall.arguments);
            if (argsSnippet.length > 120) argsSnippet = argsSnippet.slice(0, 117) + '…';
        } catch {
            argsSnippet = String(pendingToolCall.arguments).slice(0, 120);
        }
    }

    let responseSnippet = '';
    if (latestResponse && !pendingToolCall) {
        const trimmed = latestResponse.trim();
        const lastLine = trimmed.split('\n').filter(Boolean).at(-1) ?? trimmed;
        responseSnippet = lastLine.length > 120 ? lastLine.slice(0, 117) + '…' : lastLine;
    }

    return (
        <Box flexDirection="column" marginBottom={1}>
            <Box>
                <Text color="cyan">▼ </Text>
                <Text bold>Run {index + 1}</Text>
                {run.model && <Text dimColor>  {run.model}</Text>}
                <Text color={statusColor} bold>
                    {'  '}
                    {statusIcon} {run.status}
                </Text>
                {run.duration_ms !== null && (
                    <Text dimColor>  {(run.duration_ms / 1000).toFixed(1)}s</Text>
                )}
                {totalTokens > 0 && (
                    <Text dimColor>  {totalTokens.toLocaleString()} tok</Text>
                )}
            </Box>

            {pendingToolCall && (
                <Box flexDirection="column" paddingLeft={2}>
                    <Box>
                        <Text color="yellow">⌛ </Text>
                        <Text bold>{pendingToolCall.tool_name}</Text>
                    </Box>
                    {argsSnippet && (
                        <Box paddingLeft={2}>
                            <Text dimColor>{argsSnippet}</Text>
                        </Box>
                    )}
                </Box>
            )}

            {responseSnippet && (
                <Box paddingLeft={2}>
                    <Text dimColor>✍  {responseSnippet}</Text>
                </Box>
            )}

            {committedTcCount > 0 && (
                <Box paddingLeft={2}>
                    <Text dimColor>
                        {committedTcCount} operation{committedTcCount !== 1 ? 's' : ''} completed
                    </Text>
                </Box>
            )}

            {run.errors.map((err, i) => (
                <Box key={i} paddingLeft={2}>
                    <Text color="red">
                        ✗ {err.error_type ? `(${err.error_type}) ` : ''}
                        {err.message}
                    </Text>
                </Box>
            ))}
        </Box>
    );
}
