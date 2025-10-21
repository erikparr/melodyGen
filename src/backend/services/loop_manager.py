import threading
from typing import Dict, Optional, Tuple


class LoopManager:
    """
    Thread-safe manager for looping melody state.
    Stores melody data per (targetGroup, oscAddress) combination.
    This allows both /melody and /chord to loop on the same targetGroup.
    """

    def __init__(self):
        # Key: (targetGroup, oscAddress) - e.g. (0, "/melody"), (0, "/chord")
        self._loops: Dict[Tuple[int, str], Dict[str, str]] = {}
        self._lock = threading.Lock()

    def add_loop(self, target_group: int, osc_address: str, json_payload: str) -> None:
        """
        Store loop data for a (targetGroup, oscAddress) combination.

        Args:
            target_group: The track/target group ID
            osc_address: OSC path (/melody or /chord)
            json_payload: Pre-formatted JSON payload string
        """
        key = (target_group, osc_address)
        with self._lock:
            self._loops[key] = {
                "address": osc_address,
                "payload": json_payload
            }
        print(f"🔁 Stored loop: {osc_address} targetGroup {target_group}")

    def get_loop(self, target_group: int, osc_address: str) -> Optional[Dict[str, str]]:
        """
        Retrieve loop data for a specific (targetGroup, oscAddress) combination.

        Args:
            target_group: The track/target group ID
            osc_address: OSC path (/melody or /chord)

        Returns:
            Dict with 'address' and 'payload' keys, or None if not looping
        """
        key = (target_group, osc_address)
        with self._lock:
            return self._loops.get(key)

    def remove_loop(self, target_group: int, osc_address: str) -> None:
        """
        Remove loop data for a specific (targetGroup, oscAddress) combination.

        Args:
            target_group: The track/target group ID
            osc_address: OSC path (/melody or /chord)
        """
        key = (target_group, osc_address)
        with self._lock:
            if key in self._loops:
                del self._loops[key]
                print(f"⏹ Removed loop: {osc_address} targetGroup {target_group}")

    def remove_all_for_target_group(self, target_group: int) -> None:
        """
        Remove all loops (both /melody AND /chord) for a targetGroup.

        Args:
            target_group: The track/target group ID
        """
        with self._lock:
            keys_to_remove = [k for k in self._loops.keys() if k[0] == target_group]
            for key in keys_to_remove:
                del self._loops[key]
        if keys_to_remove:
            print(f"⏹ Removed all loops for targetGroup {target_group}")

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
