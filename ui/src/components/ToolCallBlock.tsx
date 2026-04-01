import React from 'react';
import { Box, Text } from 'ink';
import type { ToolCall } from '../types';

interface ToolCallBlockProps {
  toolCall: ToolCall;
}

export default function ToolCallBlock({ toolCall: tc }: ToolCallBlockProps): React.JSX.Element {
  const isPending = tc.success === null;
  const isSuccess = tc.success === true;

  const statusIcon = isPending ? '⌛' : isSuccess ? '✔' : '✗';
  const statusColor = isPending ? 'yellow' : isSuccess ? 'green' : 'red';
  const borderColor = isPending ? 'yellow' : isSuccess ? 'green' : 'red';

  let argsText = '';
  if (tc.arguments) {
    try {
      argsText = JSON.stringify(tc.arguments, null, 2);
    } catch {
      argsText = String(tc.arguments);
    }
  }

  return (
    <Box
      borderStyle="single"
      borderColor={borderColor}
      flexDirection="column"
      paddingX={1}
      marginBottom={1}
    >
      <Box>
        <Text color={statusColor}>{statusIcon} </Text>
        <Text bold>{tc.tool_name}</Text>
        {tc.duration_ms !== null && (
          <Text dimColor>  {Math.round(tc.duration_ms)}ms</Text>
        )}
      </Box>

      {argsText && (
        <Box marginTop={1}>
          <Text dimColor>{argsText}</Text>
        </Box>
      )}

      {tc.result && (
        <Box marginTop={1}>
          <Text dimColor>{tc.result}</Text>
        </Box>
      )}
    </Box>
  );
}
