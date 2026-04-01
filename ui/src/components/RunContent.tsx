import React from 'react';
import { Box, Text } from 'ink';
import type { RunData, FunctionCallData } from '../types';
import ToolCallBlock from './ToolCallBlock';

interface RunContentProps {
  run: RunData;
  functionCalls: FunctionCallData[];
  showContext: boolean;
}

export default function RunContent({
  run,
  functionCalls,
  showContext,
}: RunContentProps): React.JSX.Element {
  const toolCallMap = new Map(run.tool_calls.map((tc) => [tc.tool_call_id, tc]));

  return (
    <Box flexDirection="column" paddingLeft={2}>
      {/* Function calls */}
      {functionCalls.map((fc, i) => (
        <Box
          key={i}
          borderStyle="single"
          borderColor="cyan"
          flexDirection="column"
          paddingX={1}
          marginBottom={1}
        >
          <Text color="cyan" bold>
            ❯  {fc.method}
          </Text>
          <Text dimColor>{fc.params}</Text>
          {fc.result && <Text dimColor>{fc.result}</Text>}
        </Box>
      ))}

      {/* Prompt */}
      {showContext && run.prompt && run.provider !== 'local' && (
        <Box flexDirection="column" marginBottom={1}>
          <Text color="blue" bold>
            Prompt:
          </Text>
          <Text dimColor>{run.prompt}</Text>
        </Box>
      )}

      {/* Content blocks */}
      {run.content_blocks.map((block, i) => {
        if (block.type === 'reasoning') return null;

        if (block.type === 'response') {
          if (!block.text) return null;
          return (
            <Box key={i} flexDirection="column" marginBottom={1}>
              <Text color="blue" bold>
                Response:
              </Text>
              <Text>{block.text}</Text>
            </Box>
          );
        }

        if (block.type === 'tool_call') {
          const tc = block.ref ? toolCallMap.get(block.ref) : null;
          if (!tc) return null;
          return <ToolCallBlock key={i} toolCall={tc} />;
        }

        if (block.type === 'input') {
          if (!block.text) return null;
          return (
            <Box key={i} borderStyle="single" borderColor="dim" paddingX={1} marginBottom={1}>
              <Text>{block.text}</Text>
            </Box>
          );
        }

        if (block.type === 'logging') {
          if (!block.text) return null;
          return (
            <Box key={i}>
              <Text color="cyan" dimColor>
                [INFO] {block.text}
              </Text>
            </Box>
          );
        }

        return null;
      })}

      {/* Errors */}
      {run.errors.map((err, i) => (
        <Box
          key={i}
          borderStyle="single"
          borderColor="red"
          flexDirection="column"
          paddingX={1}
          marginBottom={1}
        >
          <Text color="red" bold>
            Error{err.error_type ? ` (${err.error_type})` : ''}
          </Text>
          <Text color="red">{err.message}</Text>
        </Box>
      ))}

      {/* Token usage */}
      {run.status === 'completed' && run.tokens.input_tokens + run.tokens.output_tokens > 0 && (
        <Box marginTop={1} gap={2}>
          <Text dimColor>Tokens:</Text>
          <Text dimColor>{run.tokens.input_tokens.toLocaleString()} in</Text>
          <Text dimColor>{run.tokens.output_tokens.toLocaleString()} out</Text>
          {run.request_count > 0 && (
            <>
              <Text dimColor>Requests:</Text>
              <Text dimColor>{run.request_count}</Text>
            </>
          )}
        </Box>
      )}

      {/* Code changes */}
      {run.code_changes && (
        <Box marginTop={1} gap={2}>
          <Text dimColor>{run.code_changes.files_modified.length} files</Text>
          <Text color="green">+{run.code_changes.lines_added}</Text>
          <Text color="red">-{run.code_changes.lines_removed}</Text>
        </Box>
      )}
    </Box>
  );
}
