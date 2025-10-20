import asyncio
import threading
import time
from typing import Dict, List, Set
from fastapi import WebSocket


class EventBroadcaster:
    """
    Thread-safe broadcaster for completion events via WebSocket.
    Manages event history and active WebSocket connections.
    """

    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self._completion_events: List[Dict] = []
        self._active_websockets: Set[WebSocket] = set()
        self._pending_events: List[Dict] = []
        self._lock = threading.Lock()

    def add_event(self, target_group: int) -> None:
        """
        Add a completion event for a targetGroup.

        Args:
            target_group: The track/target group that completed
        """
        event = {
            "targetGroup": target_group,
            "layer": target_group,
            "timestamp": time.time()
        }

        with self._lock:
            self._completion_events.append(event)
            self._pending_events.append(event)

            if len(self._completion_events) > self.max_history:
                self._completion_events.pop(0)

        print(f"✅ Completion event added for targetGroup {target_group}")

    def get_events(self, since: float = None) -> List[Dict]:
        """
        Get completion events, optionally filtered by timestamp.

        Args:
            since: Optional timestamp to filter events after

        Returns:
            List of completion event dictionaries
        """
        with self._lock:
            if since is None:
                return self._completion_events.copy()
            else:
                return [e for e in self._completion_events if e["timestamp"] > since]

    def add_websocket(self, websocket: WebSocket) -> None:
        """
        Register a WebSocket connection for broadcasts.

        Args:
            websocket: WebSocket connection to add
        """
        with self._lock:
            self._active_websockets.add(websocket)
        print(f"🔌 WebSocket client connected (total: {len(self._active_websockets)})")

    def remove_websocket(self, websocket: WebSocket) -> None:
        """
        Unregister a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
        """
        with self._lock:
            self._active_websockets.discard(websocket)
        print(f"🔌 WebSocket client disconnected (total: {len(self._active_websockets)})")

    async def broadcast_pending_events(self) -> None:
        """
        Background task that broadcasts pending events to all connected WebSockets.
        Should be run as an asyncio task.
        """
        while True:
            events_to_send = []
            websockets_to_notify = []

            with self._lock:
                if self._pending_events and self._active_websockets:
                    events_to_send = self._pending_events.copy()
                    self._pending_events.clear()
                    websockets_to_notify = list(self._active_websockets)

            if events_to_send and websockets_to_notify:
                disconnected = set()
                for event in events_to_send:
                    for websocket in websockets_to_notify:
                        try:
                            await websocket.send_json(event)
                        except Exception as e:
                            print(f"WebSocket send error: {e}")
                            disconnected.add(websocket)

                if disconnected:
                    with self._lock:
                        self._active_websockets.difference_update(disconnected)

            await asyncio.sleep(0.01)
