import React from 'react';
import { Box, Text } from 'ink';
import type { TurnData, RunStatusValue } from '../types';
import RunContent from './RunContent';

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

interface RunItemProps {
  index: number;
  turn: TurnData;
  expanded: boolean;
  showContext: boolean;
}

/** Static/committed run — always expanded, no interactive controls. */
export default function RunItem({
  index,
  turn,
  expanded,
  showContext,
}: RunItemProps): React.JSX.Element {
  const run = turn.run;
  if (!run) return <Box />;

  const statusIcon = STATUS_ICON[run.status] ?? '○';
  const statusColor = STATUS_COLOR[run.status] ?? 'gray';

  return (
    <Box flexDirection="column" marginBottom={expanded ? 1 : 0}>
      <Box>
        <Text dimColor>{expanded ? '▼' : '▶'} </Text>
        <Text bold>Run {index + 1}</Text>
        {run.model && <Text dimColor>  {run.model}</Text>}
        <Text color={statusColor} bold>
          {'  '}
          {statusIcon} {run.status}
        </Text>
        {run.duration_ms !== null && (
          <Text dimColor>  {(run.duration_ms / 1000).toFixed(1)}s</Text>
        )}
        {run.tokens.input_tokens + run.tokens.output_tokens > 0 && !expanded && (
          <Text dimColor>
            {'  '}
            {(run.tokens.input_tokens + run.tokens.output_tokens).toLocaleString()} tok
          </Text>
        )}
      </Box>

      {expanded && (
        <RunContent run={run} functionCalls={turn.function_calls} showContext={showContext} />
      )}
    </Box>
  );
}
