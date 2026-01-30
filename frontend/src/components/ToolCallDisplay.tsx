import { useState } from 'react';
import type { ToolCall } from '../types/chat';

interface ToolCallDisplayProps {
  toolCall: ToolCall;
}

export function ToolCallDisplay({ toolCall }: ToolCallDisplayProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const hasResult = toolCall.result !== undefined;
  const isLoading = !hasResult;

  return (
    <div className={`tool-call ${toolCall.success === false ? 'error' : ''}`}>
      <div
        className="tool-call-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="tool-icon">
          {isLoading ? '⏳' : toolCall.success ? '✓' : '✗'}
        </span>
        <span className="tool-name">{toolCall.name}</span>
        <span className="tool-expand">{isExpanded ? '▼' : '▶'}</span>
      </div>

      {isExpanded && (
        <div className="tool-call-details">
          <div className="tool-section">
            <div className="tool-section-title">Arguments:</div>
            <pre className="tool-json">
              {JSON.stringify(toolCall.args, null, 2)}
            </pre>
          </div>

          {hasResult && (
            <div className="tool-section">
              <div className="tool-section-title">Result:</div>
              <pre className="tool-json">
                {JSON.stringify(toolCall.result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
