# Copilot session events — report

Generated: 2026-02-13

Summary
-------
This report inspects the installed `copilot` Python package at
`.venv/lib/python3.12/site-packages/copilot` and documents all session event
shapes, their serialization, how events flow through the SDK (producers and
consumers), and typical runtime sequences (message send, streaming deltas,
tool invocation, session lifecycle). It focuses on the generated
`generated/session_events.py` types together with how `CopilotClient`,
`CopilotSession`, and the JSON-RPC layer produce/consume these events.

Repository paths referenced in this report are absolute to the workspace:
- .venv/lib/python3.12/site-packages/copilot/
- .venv/lib/python3.12/site-packages/copilot/generated/session_events.py
- .venv/lib/python3.12/site-packages/copilot/session.py
- .venv/lib/python3.12/site-packages/copilot/client.py
- .venv/lib/python3.12/site-packages/copilot/jsonrpc.py
- .venv/lib/python3.12/site-packages/copilot/tools.py
- .venv/lib/python3.12/site-packages/copilot/types.py

Files in the `copilot` package (high-level)
-----------------------------------------
The package root contains (non-exhaustive listing):
- __init__.py
- bin/ (bundled CLI binary may be present)
- client.py  — CopilotClient implementation (connection/session mgmt)
- jsonrpc.py — minimal JSON-RPC client used for stdio/TCP transport
- session.py — CopilotSession (per-session event subscription and helpers)
- tools.py   — define_tool decorator & helpers
- types.py   — public typed defs and re-exports (imports generated.SessionEvent)
- generated/session_events.py — AUTO-GENERATED: dataclasses/enums for session events

Key artifacts from generated/session_events.py
---------------------------------------------
This generated module contains:
- dataclasses for many event-adjacent payloads (Attachment, CodeChanges, Data,
  Result, Repository, Usage, ModelMetric, QuotaSnapshot, etc.)
- enums: AttachmentType, Role, ShutdownType, SourceType, ToolRequestType
- a large `Data` dataclass that is the typed container for the event payload
  (very many optional fields such as content, delta_content, tool_requests,
  tool_name, tool_call_id, message_id, error, success, attachments, etc.)
- `SessionEventType` enum enumerating event type strings such as:
  - ASSISTANT_MESSAGE, ASSISTANT_MESSAGE_DELTA, ASSISTANT_REASONING, ASSISTANT_REASONING_DELTA
  - ASSISTANT_TURN_START / ASSISTANT_TURN_END
  - TOOL_EXECUTION_START / TOOL_EXECUTION_PARTIAL_RESULT / TOOL_EXECUTION_COMPLETE / TOOL_USER_REQUESTED
  - SESSION_START / SESSION_RESUME / SESSION_IDLE / SESSION_SHUTDOWN / SESSION_ERROR / SESSION_INFO / SESSION_TRUNCATION / SESSION_MODEL_CHANGE
  - HOOK_START / HOOK_END, SUBAGENT_* events, SKILL_INVOKED, SYSTEM_MESSAGE, USER_MESSAGE
  - PENDING_MESSAGES_MODIFIED, SESSION_COMPACTION_START/COMPLETE, SESSION_USAGE_INFO
  - UNKNOWN used for forward compatibility (see _missing_ override)
- `SessionEvent` dataclass: fields are
  - data: Data
  - id: UUID
  - timestamp: datetime
  - type: SessionEventType
  - ephemeral: Optional[bool]
  - parent_id: Optional[UUID]
- serializer helpers: from_dict / to_dict helpers for each dataclass
  and global helpers `session_event_from_dict` and `session_event_to_dict`.

Notable implementation details in the generated code
- Date/time handling: uses dateutil.parser.parse for parsing timestamps.
- UUIDs: Event id and parentId are converted to/from strings via `UUID(...)` and
  `str(...)`.
- Enums: `SessionEventType._missing_` returns SessionEventType.UNKNOWN to
  handle forward-compatible unknown event types (server introduces new event
  kinds without breaking client parsing).
- Serialization guards: many `from_*` helpers assert input types (e.g., from_str,
  from_int) — invalid wire payloads will raise AssertionError in the generated
  code.

SessionEvent data shape (high-level)
------------------------------------
`SessionEvent.data: Data` is the main payload. Because `Data` is a broad union
with many optional fields, a small subset commonly seen in session flows:
- content: str  — full assistant message content
- delta_content: str — streaming chunk for assistant message (assistant.message_delta)
- partial_output / progress_message — tool partials / progress
- tool_requests: List[ToolRequest] — when the assistant requests tools
- tool_name / tool_call_id / arguments — for TOOL_USER_REQUESTED or other tool events
- message_id / turn_id / reasoning_id — correlation IDs for threads/turns
- error / error_type / stack / status_code — error details
- attachments: List[Attachment]
- session-related fields: session_id, start_time, resume_time, checkpoint_*, compaction data

How events are serialized and transported
----------------------------------------
- JSON-RPC transport: `jsonrpc.JsonRpcClient` implements the wire layer over a
  subprocess's stdio (or a socket). Messages are sent with Content-Length header
  + JSON payload and read in a blocking background thread.
- Notification: server-side session events are sent as JSON-RPC notifications
  (no id). Client's JsonRpcClient invokes a notification handler on arrival and
  schedules it onto the async event loop.
- Conversion: the Copilot client code converts the incoming event dict directly
  to `SessionEvent` objects using `generated.session_events.session_event_from_dict`.
  This performs type validation, dataclass construction, datetime parsing and
  enum mapping.

Relevant code references (producers and consumers)
--------------------------------------------------
Producers (how events get created/emitted):
- The authoritative producer is the Copilot CLI server (external binary).
- From the SDK side, events can be produced when `session.get_messages` is
  requested (returns historical events), or when the SDK sends messages which
  cause the server to emit events back.

Copilot SDK code that receives events and dispatches them locally:
- `copilot/client.py` (function `_connect_via_stdio` and `_connect_via_tcp`):
  sets up a notification handler in the JsonRpcClient that does:
    - if method == "session.event":
      - extract `sessionId` and `event` dict
      - call `session_event_from_dict(event_dict)` to construct a SessionEvent
      - look up the corresponding `CopilotSession` and call `session._dispatch_event(event)`
  (See: .venv/.../copilot/client.py _connect_via_stdio and handle_notification.)

- `copilot/session.py`:
  - `CopilotSession.on(handler)` — application code registers event handlers.
  - `CopilotSession._dispatch_event(event)` — iterates registered handlers and
    calls them with the SessionEvent instance.
  - `CopilotSession.send` and `send_and_wait` — send requests to the server
    ("session.send") which cause server-side processing and subsequent events
    to be emitted streamingly (deltas) and finally SESSION_IDLE.
  - `CopilotSession.get_messages` — calls "session.getMessages" and converts
    returned dicts using `session_event_from_dict`.

- `copilot/jsonrpc.py` handles the low-level transport (notifications vs
  requests), scheduling notification handler on the loop with
  loop.call_soon_threadsafe.

Consumers (where application logic handles events):
- Example consumer in this workspace: `src/libs/copilot/copilot_agent.py`
  - Registers a handler via `session.on(handle_event)` and maps a subset of
    SessionEventType values to UI methods:
      - TOOL_USER_REQUESTED -> ui.on_tool_requested(event.data.tool_name, event.data.tool_input)
      - ASSISTANT_REASONING_DELTA -> ui.on_reasoning_added(event.data.delta_content)
      - ASSISTANT_MESSAGE_DELTA -> ui.on_text_added(event.data.delta_content)
      - SESSION_IDLE -> ui.on_text_terminated()
  - This shows an application-level mapping from event type -> UI actions.

- UI layer: `src/app/writers/writer.py` implements the `UI` interface and
  provides on_text_added, on_text_terminated, on_tool_requested, and other
  methods used by the consumer above.

Tool invocation path (request from server -> SDK -> local tool handler):
- Server sends a JSON-RPC request `tool.call` (not a notification) to the SDK.
- `CopilotClient` registers a request handler for "tool.call":
  - `JsonRpcClient` receives the request, calls the registered handler on the
    SDK event loop via `_dispatch_request`.
  - `CopilotClient._handle_tool_call_request` locates the CopilotSession, looks
    up the tool handler from `session._get_tool_handler(name)`.
  - The SDK executes the tool handler (wrapped in `tools.define_tool` ->
    `wrapped_handler`) which returns a ToolResult (normalized by
    CopilotClient._normalize_tool_result).
  - The result is returned to the server as the JSON-RPC response.

Event sequences (typical flows)
-----------------------------
1) Create session and send a message (streaming deltas)
   - App calls: `session = await client.create_session(config)` (copilot/client.py)
   - App registers: `unsubscribe = session.on(handler)` (copilot/session.py)
   - App calls: `await session.send_and_wait(MessageOptions(prompt="..."))`
     (copilot/session.py -> CopilotClient.request("session.send")).
   - Server processes message; while generating assistant output, the server
     sends repeated JSON-RPC notifications:
       method: "session.event"
       params: { sessionId, event: { id, timestamp, type: "assistant.message_delta", data: { deltaContent } } }
   - `JsonRpcClient` receives notification, schedules notification handler.
   - `CopilotClient` notification handler converts event dict -> SessionEvent
     (`session_event_from_dict`) and calls `session._dispatch_event(event)`.
   - App's `handler` receives events and handles deltas (e.g., append to UI)
   - When done, server emits `assistant.message` or `session.idle` event; app
     may treat SESSION_IDLE as completion (see `send_and_wait` which waits
     for SESSION_IDLE).

2) Tool invocation (assistant requests a tool and server asks SDK to execute it)
   - Assistant decides it needs a tool -> server emits a session event
     `tool.user_requested` (or includes a `tool_requests` entry inside an event)
     and/or sends a `tool.call` JSON-RPC request.
   - SDK receives `tool.call` request in `JsonRpcClient._handle_request` and
     dispatches to `CopilotClient._handle_tool_call_request`.
   - CopilotClient finds registered handler via `session._get_tool_handler(tool_name)`
     and invokes the handler (tools.define_tool wraps the user function into a
     handler which validates input via Pydantic and serializes outputs).
   - SDK returns the result to the server; server may then emit tool-related
     events (TOOL_EXECUTION_START, TOOL_EXECUTION_PARTIAL_RESULT,
     TOOL_EXECUTION_COMPLETE) as notifications.

3) Session lifecycle notifications
   - `session.lifecycle` notifications are handled specially by the client in
     `CopilotClient._connect_via_stdio` and converted to `SessionLifecycleEvent`
     and dispatched to lifecycle subscribers via `client._dispatch_lifecycle_event`.

Public API surface for session events
-------------------------------------
- `copilot.generated.session_events.SessionEvent`, `SessionEventType`, and
  `Data` are the canonical types for session event payloads (auto-generated).
- `CopilotSession.on(handler: Callable[[SessionEvent], None])` — register
  handlers that receive typed SessionEvent objects.
- `CopilotSession.get_messages()` returns a `list[SessionEvent]` reconstructed
  from historical event dictionaries returned by the server.
- `session_event_from_dict` and `session_event_to_dict` functions in
  generated/session_events.py provide explicit conversion helpers.

Edge cases, robustness notes, and recommendations
-----------------------------------------------
1) Forward-compatibility: `SessionEventType._missing_` returns UNKNOWN so new
   server-side event types won't crash parsing. Recommendation: handlers
   should log/inspect UNKNOWN events (and capture raw type string if available)
   so developers can adapt to new event kinds.

2) Strict assertions during deserialization: the generated `from_*` helpers use
   `assert` and will raise on unexpected shapes. If the server sends slightly
   different shapes (e.g., missing optional keys or nulls), this can raise
   AssertionError. Recommendation: consider wrapping deserialization in a try/except
   in the higher-level notification handler and logging (or preserving the raw
   dict) to avoid taking down the event dispatch path.

3) Date parsing uses `dateutil.parser.parse` — any non-ISO timestamps will raise
   parse errors. Keep an eye on server timestamp format; add defensive handling
   if needed.

4) Performance: constructing many dataclasses for high-volume streams (e.g.,
   high-frequency assistant.message_delta) is convenient but could be heavier
   than using a small dict-based representation for extremely high throughput.
   Consider providing a config switch or a lightweight parsing path for
   performance-sensitive consumers.

5) Missing documentation: the generated types contain very many optional fields
   (Data). It would be helpful to maintain a short human-owned summary of the
   fields most likely to appear in streaming responses (content, delta_content,
   tool_requests, tool_name, tool_call_id, message_id, error) — to ease app
   developer onboarding.

6) Tool execution semantics: `tool.call` is synchronous from the SDK's view
   (server awaits the JSON-RPC response). Long-running tool handlers should be
   written as async and respect timeouts; otherwise they will block the server
   until completion.

Quality gates & coverage mapping
--------------------------------
- Inspect generated types: Done (read `generated/session_events.py`) — Done
- Trace producers/consumers: Done (client.jsonrpc -> client.handle_notification -> session.dispatch -> app handler) — Done
- Serialization explanation: Done (dataclasses, to_dict/from_dict, dateutil, UUIDs) — Done
- Typical flows: Done (send/send_and_wait streaming, tool invocation, lifecycle) — Done
- Recommendations: Done (forward compat, assert handling, perf)

Appendix: Important code references (short)
------------------------------------------
- JSON-RPC read & dispatch: .venv/.../copilot/jsonrpc.py (JsonRpcClient._read_loop,
  _handle_message, _dispatch_request)
- Notification handling & conversion to SessionEvent: .venv/.../copilot/client.py
  (in _connect_via_stdio/_connect_via_tcp: handle_notification ->
  session_event_from_dict -> session._dispatch_event)
- Session event subscription and dispatch: .venv/.../copilot/session.py
  (CopilotSession.on, CopilotSession._dispatch_event, send_and_wait behavior)
- Generated types: .venv/.../copilot/generated/session_events.py
  (SessionEvent, SessionEventType, Data, session_event_from_dict)
- Tool decorator & normalization: .venv/.../copilot/tools.py (define_tool,
  wrapped_handler, _normalize_result)
- Example consumer: src/libs/copilot/copilot_agent.py (handle_event mapping to UI)

If you want, I can:
- Add a compact event-type cheat-sheet (table of important SessionEventType
  values and expected Data fields) as a human-friendly quick reference.
- Generate small unit tests that exercise the parsing of a few representative
  event payloads (delta message, assistant message, tool request, session idle),
  using the generated session_event_from_dict function.


Checklist (task mapping)
- Inspect copilot package files: Done
- Extract and document session event classes and data: Done (generated/session_events.py summary)
- Trace flow of events: Done (client.jsonrpc -> client -> session -> app)
- Map producers/consumers with references: Done (see code reference section)
- Document serialization and helpers: Done
- Provide recommendations: Done


End of report.

