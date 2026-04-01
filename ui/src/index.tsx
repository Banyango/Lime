import React from 'react';
import { render } from 'ink';
import * as fs from 'fs';
import * as tty from 'tty';
import App from './App';
import { sendMessage } from './protocol';

function main(): void {
  const isWindows = process.platform === 'win32';
  const ttyPath = isWindows ? '\\\\.\\CON' : '/dev/tty';

  let ttyIn: tty.ReadStream;
  let ttyOut: tty.WriteStream;

  try {
    const fd = fs.openSync(ttyPath, 'r+');
    ttyIn = new tty.ReadStream(fd);
    ttyOut = new tty.WriteStream(fd);
    ttyIn.setRawMode(true);
    ttyIn.resume();
  } catch (err) {
    process.stderr.write(
      `lime-ai: Could not open TTY device (${ttyPath}): ${(err as Error).message}\n`,
    );
    process.exit(1);
  }

  // Render UI to TTY; keep process.stdout free for protocol messages to Python
  render(<App />, {
    stdin: ttyIn as unknown as NodeJS.ReadStream,
    stdout: ttyOut as unknown as NodeJS.WriteStream,
  });

  // Signal that the UI is mounted and ready to receive state updates
  sendMessage('ui_ready');
}

main();
