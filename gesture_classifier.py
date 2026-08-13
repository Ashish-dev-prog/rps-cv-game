# -*- coding: utf-8 -*-
"""
gesture_classifier.py  —  Maps 21 hand landmarks to Rock / Paper / Scissors.

Detection logic in one sentence:
    In normalised image space y=0 is the TOP of the frame, so a fingertip
    that sits above its PIP joint has a smaller y-value → finger is extended.
    We check four fingers, get a 4-bit pattern, and look it up in a table.

Finger pattern → gesture:
    [0, 0, 0, 0]  Rock      (all curled)
    [1, 1, 1, 1]  Paper     (all extended)
    [1, 1, 0, 0]  Scissors  (index + middle up)
    anything else → Unknown

The thumb is skipped — it bends sideways, so the vertical tip-vs-PIP
comparison is unreliable. A fist and a thumbs-up both hit [0,0,0,0],
which is fine for this game since both map to Rock.
"""

from hand_tracker import HandTracker

ROCK     = "Rock"
PAPER    = "Paper"
SCISSORS = "Scissors"
UNKNOWN  = "Unknown"


class GestureClassifier:
    """Stateless: call classify() every frame, no side effects."""

    # (tip_index, pip_index) for each non-thumb finger
    _FINGER_PAIRS: list[tuple[int, int]] = [
        (HandTracker.INDEX_TIP,  HandTracker.INDEX_PIP),
        (HandTracker.MIDDLE_TIP, HandTracker.MIDDLE_PIP),
        (HandTracker.RING_TIP,   HandTracker.RING_PIP),
        (HandTracker.PINKY_TIP,  HandTracker.PINKY_PIP),
    ]

    _GESTURE_MAP: dict[tuple[int, ...], str] = {
        (0, 0, 0, 0): ROCK,
        (1, 1, 1, 1): PAPER,
        (1, 1, 0, 0): SCISSORS,
    }

    def classify(self, landmarks: list[tuple[float, float, float]]) -> str:
        if not landmarks or len(landmarks) < 21:
            return UNKNOWN
        pattern = tuple(self._finger_states(landmarks))
        return self._GESTURE_MAP.get(pattern, UNKNOWN)

    def _finger_states(self, lm: list[tuple]) -> list[int]:
        """
        Returns [index, middle, ring, pinky] as 0/1 (0=curled, 1=extended).
        tip.y < pip.y means the tip is higher on screen = finger is up.
        """
        return [1 if lm[tip][1] < lm[pip][1] else 0
                for tip, pip in self._FINGER_PAIRS]
