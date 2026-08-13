# -*- coding: utf-8 -*-
"""
hand_tracker.py  —  MediaPipe 1.0 Tasks API wrapper for hand landmark detection.

MediaPipe 1.0 dropped the legacy mp.solutions API entirely. The replacement
is the Tasks API, which requires a pre-built .task model file and explicit
timestamps per frame (VIDEO mode tracks between frames; IMAGE mode doesn't).
We auto-download the model on first run so there's nothing for the user to do.
"""

import cv2
import time
import os
import urllib.request
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
from dataclasses import dataclass
from typing import Optional


MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")


def _ensure_model() -> None:
    if os.path.exists(MODEL_PATH):
        return
    print("[INFO] Downloading hand landmarker model (~5 MB)...")
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print(f"[INFO] Saved to {MODEL_PATH}")
    except Exception as exc:
        raise RuntimeError(
            f"Model download failed ({MODEL_URL}).\n"
            "Check your internet connection or download it manually."
        ) from exc


@dataclass
class HandResult:
    """Slim container for one detected hand."""
    landmarks:  list[tuple[float, float, float]]  # 21 normalised (x, y, z) points
    handedness: str                                # "Left" or "Right" (camera POV)


class HandTracker:
    """
    Wraps HandLandmarker in VIDEO mode for per-frame detection with tracking.

    Landmark index constants are defined here so the classifier can reference
    them by name rather than magic numbers.
    """

    # Landmark indices — standard MediaPipe numbering
    WRIST        = 0
    THUMB_CMC    = 1;  THUMB_MCP   = 2;  THUMB_IP    = 3;  THUMB_TIP   = 4
    INDEX_MCP    = 5;  INDEX_PIP   = 6;  INDEX_DIP   = 7;  INDEX_TIP   = 8
    MIDDLE_MCP   = 9;  MIDDLE_PIP  = 10; MIDDLE_DIP  = 11; MIDDLE_TIP  = 12
    RING_MCP     = 13; RING_PIP    = 14; RING_DIP    = 15; RING_TIP    = 16
    PINKY_MCP    = 17; PINKY_PIP   = 18; PINKY_DIP   = 19; PINKY_TIP   = 20

    # Bone connections for manual skeleton drawing
    CONNECTIONS: list[tuple[int, int]] = [
        (0, 1), (1, 2), (2, 3), (3, 4),
        (0, 5), (5, 6), (6, 7), (7, 8),
        (5, 9), (9, 10), (10, 11), (11, 12),
        (9, 13), (13, 14), (14, 15), (15, 16),
        (13, 17), (17, 18), (18, 19), (19, 20),
        (0, 17), (1, 5),
    ]

    def __init__(
        self,
        max_num_hands:            int   = 1,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence:  float = 0.7,
    ) -> None:
        _ensure_model()
        options = vision.HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.landmarker    = vision.HandLandmarker.create_from_options(options)
        self._start_ms     = int(time.time() * 1000)

    def process_frame(
        self,
        frame: np.ndarray,
        draw_landmarks: bool = True,
    ) -> tuple[np.ndarray, Optional[HandResult]]:
        """
        Detect landmarks in a BGR frame. Returns the (possibly annotated) frame
        and a HandResult, or None if no hand is visible.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts_ms  = int(time.time() * 1000) - self._start_ms  # must increase monotonically
        result = self.landmarker.detect_for_video(mp_img, ts_ms)

        if not result.hand_landmarks:
            return frame, None

        lms        = result.hand_landmarks[0]
        handedness = result.handedness[0][0].display_name
        landmarks  = [(lm.x, lm.y, lm.z) for lm in lms]

        if draw_landmarks:
            self._draw_skeleton(frame, landmarks)

        return frame, HandResult(landmarks=landmarks, handedness=handedness)

    def release(self) -> None:
        self.landmarker.close()

    def _draw_skeleton(self, frame: np.ndarray, landmarks: list[tuple]) -> None:
        """
        Manual landmark rendering — mp.solutions.drawing_utils was removed in 1.0.
        Normalised coords are scaled to pixel space by multiplying by frame w/h.
        """
        h, w = frame.shape[:2]
        pts = [(int(lm[0] * w), int(lm[1] * h)) for lm in landmarks]

        for a, b in self.CONNECTIONS:
            cv2.line(frame, pts[a], pts[b], (60, 210, 90), 2, cv2.LINE_AA)

        for pt in pts:
            cv2.circle(frame, pt, 6, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(frame, pt, 3, (0, 150, 255),   -1, cv2.LINE_AA)
