import { useCallback, useRef, useState } from 'react';
import type { StepMessage } from '../types';

export function useWebSocket(url: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const [messages, setMessages] = useState<StepMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  const connect = useCallback((initPayload: Record<string, any>) => {
    setMessages([]);
    setIsComplete(false);

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}${url}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      ws.send(JSON.stringify(initPayload));
    };

    ws.onmessage = (event) => {
      const msg: StepMessage = JSON.parse(event.data);
      if (msg.stage === 'done') {
        setIsComplete(true);
        ws.close();
        return;
      }
      setMessages((prev) => [...prev, msg]);
    };

    ws.onerror = () => {
      setIsConnected(false);
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;
    };
  }, [url]);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setIsConnected(false);
  }, []);

  return { messages, isConnected, isComplete, connect, disconnect };
}
