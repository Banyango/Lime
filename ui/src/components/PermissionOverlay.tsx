import React from 'react';
import { Box, Text, useInput } from 'ink';
import type { PendingPermission } from '../types';
import { sendMessage } from '../protocol';

const KIND_LABELS: Record<string, string> = {
  shell: 'Shell command',
  write: 'File write',
  read: 'File read',
  url: 'URL access',
  mcp: 'MCP tool',
  'custom-tool': 'Custom tool',
};

interface PermissionOverlayProps {
  pendingPermission: PendingPermission;
}

export default function PermissionOverlay({
  pendingPermission,
}: PermissionOverlayProps): React.JSX.Element {
  const label = KIND_LABELS[pendingPermission.kind] ?? pendingPermission.kind;

  const details = Object.entries(pendingPermission.details)
    .filter(([k]) => k !== 'kind')
    .map(([k, v]) => `${k}: ${v}`)
    .join('  ');

  useInput((input) => {
    if (input === 'a') {
      sendMessage('permission_response', { approved: true });
    } else if (input === 'd') {
      sendMessage('permission_response', { approved: false });
    }
  });

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor="yellow"
      paddingX={2}
      paddingY={1}
      marginTop={1}
    >
      <Text color="yellow" bold>
        ⚠  Permission request:{'  '}
        <Text color="white">{label}</Text>
      </Text>
      {details && (
        <Box marginTop={1}>
          <Text dimColor>{details}</Text>
        </Box>
      )}
      <Box marginTop={1} gap={4}>
        <Text>
          <Text color="green" bold>
            a
          </Text>
          <Text dimColor> Approve</Text>
        </Text>
        <Text>
          <Text color="red" bold>
            d
          </Text>
          <Text dimColor> Deny</Text>
        </Text>
      </Box>
    </Box>
  );
}
