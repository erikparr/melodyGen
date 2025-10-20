import json
from pythonosc import udp_client
from typing import Dict, List


class OSCService:
    """
    Service for OSC communication with SuperCollider.
    Handles sending melodies and chords to SuperCollider on port 7000.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 7000):
        self.host = host
        self.port = port
        self.client = udp_client.SimpleUDPClient(host, port)

    def send_melody(self, notes: List[Dict], metadata: Dict) -> Dict:
        """
        Send melody or chord to SuperCollider.
        Routes to /chord or /melody based on chordMode flag.

        Args:
            notes: List of note dictionaries {midi, vel, dur}
            metadata: Metadata dictionary including chordMode, loop, targetGroup

        Returns:
            Dict with success status and send details
        """
        is_chord_mode = metadata.get("chordMode", False)
        osc_address = "/chord" if is_chord_mode else "/melody"

        osc_payload = {
            "notes": notes,
            "metadata": metadata
        }

        json_payload = json.dumps(osc_payload)

        print("\n" + "="*80)
        print(f"🎵 SENDING OSC MESSAGE")
        print(f"   Path: {osc_address}")
        print(f"   Target: {self.host}:{self.port}")
        print(f"   Loop: {metadata.get('loop', False)}")
        print(f"   Payload:")
        print(json.dumps(osc_payload, indent=4))
        print("="*80 + "\n")

        self.client.send_message(osc_address, json_payload)

        return {
            "success": True,
            "address": osc_address,
            "targetGroup": metadata.get("targetGroup", 0),
            "note_count": len(notes)
        }

    def resend_message(self, osc_address: str, json_payload: str) -> None:
        """
        Resend a previously formatted OSC message (used for looping).

        Args:
            osc_address: OSC address path (/melody or /chord)
            json_payload: Pre-formatted JSON string
        """
        print(f"🔁 Resending {osc_address} to {self.host}:{self.port}")
        self.client.send_message(osc_address, json_payload)
