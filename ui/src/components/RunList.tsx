import React, { useState } from 'react';
import { Box, useInput } from 'ink';
import type { TurnData } from '../types';
import RunItem from './RunItem';

interface RunListProps {
  turns: TurnData[];
  agentDone: boolean;
  hasOverlay: boolean;
  showContext: boolean;
}

export default function RunList({
  turns,
  agentDone,
  hasOverlay,
  showContext,
}: RunListProps): React.JSX.Element {
  const turnsWithRuns = turns.filter((t) => t.run !== null);
  const lastIndex = turnsWithRuns.length - 1;

  const [selectedIndex, setSelectedIndex] = useState(0);
  // Map from run index to explicit user toggle (true = expanded, false = collapsed)
  const [userToggles, setUserToggles] = useState<Map<number, boolean>>(new Map());

  const isExpanded = (i: number): boolean => {
    if (userToggles.has(i)) return userToggles.get(i)!;
    // Default: last run expanded while agent is running, all expanded when done
    return i === lastIndex;
  };

  useInput(
    (_input, key) => {
      if (key.upArrow) {
        setSelectedIndex((prev) => Math.max(0, prev - 1));
      } else if (key.downArrow) {
        setSelectedIndex((prev) => Math.min(lastIndex, prev + 1));
      } else if (key.return) {
        const idx = Math.min(selectedIndex, lastIndex);
        setUserToggles((prev) => {
          const next = new Map(prev);
          next.set(idx, !isExpanded(idx));
          return next;
        });
      }
    },
    { isActive: !hasOverlay && turnsWithRuns.length > 0 },
  );

  return (
    <Box flexDirection="column">
      {turnsWithRuns.map((turn, i) => (
        <RunItem
          key={i}
          index={i}
          turn={turn}
          expanded={isExpanded(i)}
          isSelected={i === Math.min(selectedIndex, lastIndex)}
          showContext={showContext}
        />
      ))}
    </Box>
  );
}
