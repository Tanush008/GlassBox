"use client";

import { useCallback, useRef, useState } from "react";
import type {
  AgentResultMessage,
  ContextMessage,
  DoneMessage,
  RunStatus,
  ServerMessage,
} from "./types";

const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/run";

export function useAgentSocket() {
  const [status, setStatus] = useState<RunStatus>("idle");
  const [context, setContext] = useState<ContextMessage | null>(null);
  const [trace, setTrace] = useState<AgentResultMessage[]>([]);
  const [result, setResult] = useState<DoneMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  const run = useCallback((request: string) => {
    socketRef.current?.close();

    setStatus("connecting");
    setContext(null);
    setTrace([]);
    setResult(null);
    setError(null);

    let socket: WebSocket;
    try {
      socket = new WebSocket(WS_URL);
    } catch {
      setStatus("error");
      setError(`Could not reach ${WS_URL}. Is the backend running?`);
      return;
    }
    socketRef.current = socket;

    socket.onopen = () => {
      setStatus("running");
      socket.send(JSON.stringify({ request }));
    };

    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data) as ServerMessage;
      if (msg.type === "context") {
        setContext(msg);
      } else if (msg.type === "agent_result") {
        setTrace((prev) => [...prev, msg]);
      } else if (msg.type === "done") {
        setResult(msg);
        setStatus("done");
      } else if (msg.type === "error") {
        setError(msg.message);
        setStatus("error");
      }
    };

    socket.onerror = () => {
      setStatus("error");
      setError(
        `Couldn't connect to ${WS_URL}. Check that the backend is running and NEXT_PUBLIC_WS_URL is set.`
      );
    };

    socket.onclose = () => {
      setStatus((s) => (s === "running" ? "error" : s));
    };
  }, []);

  const reset = useCallback(() => {
    socketRef.current?.close();
    setStatus("idle");
    setContext(null);
    setTrace([]);
    setResult(null);
    setError(null);
  }, []);

  return { status, context, trace, result, error, run, reset };
}
