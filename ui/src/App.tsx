import React, {useState, useRef, useEffect} from 'react';
import {Box, Static, useApp, useInput} from 'ink';
import type {StatePayload, TurnData} from './types';
import type {IncomingMessage} from './protocol';
import {sendMessage} from './protocol';
import {useStdinMessages} from './hooks/useStdinMessages';
import Header from './components/Header';
import RunItem from './components/RunItem';
import ActiveRun from './components/ActiveRun';
import StatusLine from './components/StatusLine';
import InputOverlay from './components/InputOverlay';
import PermissionOverlay from './components/PermissionOverlay';

export default function App(): React.JSX.Element {
    const {exit} = useApp();
    const [state, setState] = useState<StatePayload | null>(null);
    const [agentDone, setAgentDone] = useState(false);
    const [agentError, setAgentError] = useState<string | null>(null);

    const handleMessage = (msg: IncomingMessage) => {
        switch (msg.type) {
            case 'state_update':
                setState(msg.payload as StatePayload);
                break;
            case 'agent_done':
                setAgentDone(true);
                break;
            case 'agent_error':
                setAgentError((msg.payload as { message: string }).message);
                break;
        }
    };

    useStdinMessages(handleMessage);

    const hasPendingInput = !!state?.pending_input;
    const hasPendingPermission = !!state?.pending_permission;
    const hasOverlay = hasPendingInput || hasPendingPermission;

    useInput(
        (input) => {
            if (input === 'q') {
                sendMessage('quit');
                exit();
            }
        },
        {isActive: !hasPendingInput},
    );

    const turnsWithRuns = (state?.turns ?? []).filter((t) => t.run !== null);

    // Committed turns use <Static> — rendered once, never redrawn, scroll up naturally.
    // When agentDone, commit all turns. Otherwise commit all but the last (active) turn.
    const committedTurns: TurnData[] = agentDone
        ? turnsWithRuns
        : turnsWithRuns.slice(0, -1);

    const activeTurn: TurnData | null =
        !agentDone && turnsWithRuns.length > 0
            ? turnsWithRuns[turnsWithRuns.length - 1]
            : null;

    const activeTurnIndex = turnsWithRuns.length - 1;

    return (
        <Box flexDirection="column">
            {state && <Header state={state}/>}
            <Static items={committedTurns}>
                {(turn, i) => (
                    <RunItem
                        key={i}
                        index={i}
                        turn={turn}
                        expanded={true}
                        showContext={false}
                    />
                )}
            </Static>
            {activeTurn && (
                <ActiveRun
                    turn={activeTurn}
                    index={activeTurnIndex}
                    hasOverlay={hasOverlay}
                    showContext={false}
                />
            )}

            <StatusLine turns={state?.turns ?? []} agentDone={agentDone} agentError={agentError}/>

            {state?.pending_input && <InputOverlay pendingInput={state.pending_input}/>}
            {state?.pending_permission && (
                <PermissionOverlay pendingPermission={state.pending_permission}/>
            )}
        </Box>
    );
}
