import React from 'react';
import { Box, Text } from 'ink';
import type { StatePayload } from '../types';

const LOGO_LINES = [
  ' _ _                ',
  '| (_)_ __ ___   ___ ',
  '| | | \'_ ` _ \\ / _ \\',
  '| | | | | | | |  __/',
  '|_|_|_| |_| |_|\\___|',
];

interface HeaderProps {
  state: StatePayload;
}

export default function Header({ state }: HeaderProps): React.JSX.Element {
  return (
    <Box flexDirection="column" marginBottom={1}>
      {LOGO_LINES.map((line, i) => (
        <Text key={i} color="green">
          {line}
        </Text>
      ))}

      {state.import_errors.length > 0 && (
        <Box flexDirection="column" marginTop={1}>
          <Text color="red">── Import Errors ─────────────────────────</Text>
          {state.import_errors.map((err, i) => (
            <Text key={i} color="red">
              {err}
            </Text>
          ))}
          <Text color="red">──────────────────────────────────────────</Text>
        </Box>
      )}

      {state.warnings.length > 0 && (
        <Box flexDirection="column" marginTop={1}>
          <Text color="yellow">── Warnings ──────────────────────────────</Text>
          {state.warnings.map((w, i) => (
            <Text key={i} color="yellow">
              {w}
            </Text>
          ))}
          <Text color="yellow">──────────────────────────────────────────</Text>
        </Box>
      )}

      {state.header && (
        <Box marginTop={1}>
          <Text color="cyan" bold>
            {state.header}
          </Text>
        </Box>
      )}

      {Object.keys(state.metadata).length > 0 && (
        <Box flexDirection="column" marginTop={1}>
          <Text color="cyan" dimColor>
            ── Metadata ──────────────────────────────
          </Text>
          {Object.entries(state.metadata).map(([k, v]) => (
            <Text key={k} dimColor>
              {k}: {v}
            </Text>
          ))}
          <Text color="cyan" dimColor>
            ──────────────────────────────────────────
          </Text>
        </Box>
      )}

      {state.memory && Object.keys(state.memory).length > 0 && (
        <Box flexDirection="column" marginTop={1}>
          <Text color="magenta" dimColor>
            ── Memory ────────────────────────────────
          </Text>
          {Object.entries(state.memory).map(([k, v]) => (
            <Text key={k} dimColor>
              {k}: {v}
            </Text>
          ))}
          <Text color="magenta" dimColor>
            ──────────────────────────────────────────
          </Text>
        </Box>
      )}
    </Box>
  );
}
