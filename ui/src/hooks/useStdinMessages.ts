import { useEffect, useRef } from 'react';
import * as readline from 'readline';
import type { IncomingMessage } from '../protocol';

export function useStdinMessages(onMessage: (msg: IncomingMessage) => void): void {
  const onMessageRef = useRef(onMessage);

  useEffect(() => {
    onMessageRef.current = onMessage;
  });

  useEffect(() => {
    const rl = readline.createInterface({ input: process.stdin, terminal: false });

    rl.on('line', (line: string) => {
      const trimmed = line.trim();
      if (!trimmed) return;
      try {
        const msg = JSON.parse(trimmed) as IncomingMessage;
        onMessageRef.current(msg);
      } catch {
        // ignore parse errors
      }
    });

    return () => {
      rl.close();
    };
  }, []);
}
