export type IncomingMessageType = 'state_update' | 'agent_done' | 'agent_error';
export type OutgoingMessageType = 'ui_ready' | 'input_response' | 'permission_response' | 'quit';

export interface IncomingMessage {
  type: IncomingMessageType;
  payload: unknown;
}

export function sendMessage(type: OutgoingMessageType, payload: unknown = {}): void {
  process.stdout.write(JSON.stringify({ type, payload }) + '\n');
}
