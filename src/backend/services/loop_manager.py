import threading
from typing import Dict, Optional


class LoopManager:
    """
    Thread-safe manager for looping melody state.
    Stores melody data per targetGroup for automatic re-triggering.
    """

    def __init__(self):
        self._loops: Dict[int, Dict[str, str]] = {}
        self._lock = threading.Lock()

    def add_loop(self, target_group: int, osc_address: str, json_payload: str) -> None:
        """
        Store loop data for a targetGroup.

        Args:
            target_group: The track/target group ID
            osc_address: OSC path (/melody or /chord)
            json_payload: Pre-formatted JSON payload string
        """
        with self._lock:
            self._loops[target_group] = {
                "address": osc_address,
                "payload": json_payload
            }
        print(f"🔁 Stored loop data for targetGroup {target_group}")

    def get_loop(self, target_group: int) -> Optional[Dict[str, str]]:
        """
        Retrieve loop data for a targetGroup.

        Args:
            target_group: The track/target group ID

        Returns:
            Dict with 'address' and 'payload' keys, or None if not looping
        """
        with self._lock:
            return self._loops.get(target_group)

    def remove_loop(self, target_group: int) -> None:
        """
        Remove loop data for a targetGroup (stops looping).

        Args:
            target_group: The track/target group ID
        """
        with self._lock:
            if target_group in self._loops:
                del self._loops[target_group]
                print(f"⏹ Removed loop data for targetGroup {target_group}")

    def has_loop(self, target_group: int) -> bool:
        """
        Check if a targetGroup is currently looping.

        Args:
            target_group: The track/target group ID

        Returns:
            True if looping, False otherwise
        """
        with self._lock:
            return target_group in self._loops

    def clear_all(self) -> None:
        """Clear all loop data (stops all loops)."""
        with self._lock:
            self._loops.clear()
        print("⏹ Cleared all loop data")
