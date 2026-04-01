import React, { useState, useEffect } from 'react';
import { Box, Text } from 'ink';
import type { TurnData } from '../types';

const SPINNER_FRAMES = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏';

interface StatusLineProps {
  turns: TurnData[];
  agentDone: boolean;
  agentError: string | null;
}

export default function StatusLine({
  turns,
  agentDone,
  agentError,
}: StatusLineProps): React.JSX.Element | null {
  const [frame, setFrame] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setFrame((f) => (f + 1) % SPINNER_FRAMES.length);
    }, 500);
    return () => clearInterval(timer);
  }, []);

  const hasRuns = turns.some((t) => t.run !== null);
  if (!hasRuns && !agentError) return null;

  if (agentError) {
    return (
      <Box marginTop={1}>
        <Text color="red" bold>
          ✗ Agent error:{' '}
        </Text>
        <Text color="red">{agentError}</Text>
        <Text dimColor>  q to quit</Text>
      </Box>
    );
  }

  const allDone = turns.every(
    (t) => !t.run || t.run.status === 'completed' || t.run.status === 'error',
  );

  if (allDone || agentDone) {
    return (
      <Box marginTop={1}>
        <Text color="green" bold>
          ●{' '}
        </Text>
        <Text dimColor>All turns completed  </Text>
        <Text bold>q</Text>
        <Text dimColor> to quit</Text>
      </Box>
    );
  }

  // Get reasoning snippet from current run
  const lastTurn = turns[turns.length - 1];
  let reasoningSnippet = '';
  if (lastTurn?.run) {
    const reasoningBlocks = lastTurn.run.content_blocks.filter(
      (b) => b.type === 'reasoning' && b.text,
    );
    if (reasoningBlocks.length > 0) {
      const latest = reasoningBlocks[reasoningBlocks.length - 1].text;
      const boldMatches = latest.match(/\*\*(.+?)\*\*/g);
      let snippet = boldMatches
        ? boldMatches[boldMatches.length - 1].replace(/\*\*/g, '')
        : latest;
      snippet = snippet.replace(/\n/g, ' ').trim();
      if (snippet.length > 80) snippet = snippet.slice(0, 77) + '…';
      reasoningSnippet = snippet;
    }
  }

  return (
    <Box marginTop={1}>
      <Text color="green">{SPINNER_FRAMES[frame]} </Text>
      <Text dimColor>Executing…</Text>
      {reasoningSnippet && (
        <Text dimColor italic>
          {'  '}
          {reasoningSnippet}
        </Text>
      )}
    </Box>
  );
}
