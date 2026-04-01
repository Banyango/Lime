export type RunStatusValue = 'starting' | 'running' | 'idle' | 'error' | 'completed';
export type ContentBlockTypeValue =
  | 'reasoning'
  | 'response'
  | 'function_call'
  | 'tool_call'
  | 'input'
  | 'logging'
  | 'other';
export type RunEventValue = 'thinking' | 'running' | 'reasoning' | 'responding' | 'fetching';

export interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  cache_read_tokens: number;
  cache_write_tokens: number;
}

export interface ContentBlock {
  type: ContentBlockTypeValue;
  text: string;
  ref: string | null;
}

export interface ToolCall {
  tool_name: string;
  tool_call_id: string;
  arguments: Record<string, unknown> | null;
  result: string | null;
  success: boolean | null;
  duration_ms: number | null;
  parent_tool_call_id: string | null;
}

export interface RunError {
  message: string;
  code: string | null;
  error_type: string | null;
}

export interface CodeChanges {
  files_modified: string[];
  lines_added: number;
  lines_removed: number;
}

export interface RunData {
  status: RunStatusValue;
  model: string | null;
  provider: string | null;
  duration_ms: number | null;
  event_name: RunEventValue | null;
  tokens: TokenUsage;
  content_blocks: ContentBlock[];
  tool_calls: ToolCall[];
  errors: RunError[];
  code_changes: CodeChanges | null;
  request_count: number;
  total_cost: number;
  prompt: string | null;
}

export interface FunctionCallData {
  method: string;
  params: string;
  result: string | null;
}

export interface TurnData {
  run: RunData | null;
  function_calls: FunctionCallData[];
}

export interface PendingInput {
  prompt: string;
  seq: number;
}

export interface PendingPermission {
  kind: string;
  details: Record<string, string>;
}

export interface StatePayload {
  header: string;
  warnings: string[];
  import_errors: string[];
  metadata: Record<string, string>;
  memory: Record<string, string> | null;
  turns: TurnData[];
  pending_input: PendingInput | null;
  pending_permission: PendingPermission | null;
}
