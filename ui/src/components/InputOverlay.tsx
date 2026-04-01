import React, { useState } from 'react';
import { Box, Text } from 'ink';
import TextInput from 'ink-text-input';
import type { PendingInput } from '../types';
import { sendMessage } from '../protocol';

interface InputOverlayProps {
  pendingInput: PendingInput;
}

export default function InputOverlay({ pendingInput }: InputOverlayProps): React.JSX.Element {
  const [value, setValue] = useState('');

  const handleSubmit = (submitted: string) => {
    sendMessage('input_response', { value: submitted, seq: pendingInput.seq });
    setValue('');
  };

  return (
    <Box
      flexDirection="column"
      borderStyle="round"
      borderColor="cyan"
      paddingX={2}
      paddingY={1}
      marginTop={1}
    >
      <Text color="cyan" bold>
        ❯  {pendingInput.prompt}
      </Text>
      <Box marginTop={1}>
        <TextInput
          value={value}
          onChange={setValue}
          onSubmit={handleSubmit}
          placeholder="Type your answer and press Enter…"
        />
      </Box>
    </Box>
  );
}
