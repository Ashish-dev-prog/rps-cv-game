# -*- coding: utf-8 -*-
"""
ui_overlay.py  —  HUD rendering for the RPS game.
All cv2 drawing lives here so main.py stays clean.
"""

import cv2
import math
import time
import numpy as np
from game_logic import Score


# ---------------------------------------------------------------------------
# Palette  (all BGR — OpenCV is BGR, not RGB)
# ---------------------------------------------------------------------------

C = {
    "bg_panel":   (12,  12,  18),    # near-black card background
    "border":     (45,  45,  58),    # subtle panel border
    "border_hi":  (70,  70,  90),    # highlighted border
    "white":      (245, 245, 252),
    "dim":        (120, 120, 135),
    "green":      (75,  235, 105),   # win
    "red":        (65,   65, 230),   # lose
    "amber":      (38,  195, 255),   # draw / warning
    "neon":       (255, 185,  50),   # accent / arcs
    "rock":       (195,  85, 225),   # Rock gesture
    "paper":      (255, 175,  50),   # Paper gesture
    "scissors":   (50,  230, 230),   # Scissors gesture
}

GESTURE_COLOUR = {
    "Rock":     C["rock"],
    "Paper":    C["paper"],
    "Scissors": C["scissors"],
    "Unknown":  C["dim"],
}


FONT        = cv2.FONT_HERSHEY_DUPLEX
FONT_BOLD   = cv2.FONT_HERSHEY_TRIPLEX
FONT_PLAIN  = cv2.FONT_HERSHEY_SIMPLEX


# ---------------------------------------------------------------------------
# Drawing primitives
# ---------------------------------------------------------------------------

def _blend(frame, x1, y1, x2, y2, colour, alpha=0.72):
    """Alpha-blended filled rectangle."""
    h, w = frame.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w - 1, x2), min(h - 1, y2)
    if x1 >= x2 or y1 >= y2:
        return
    roi     = frame[y1:y2, x1:x2]
    overlay = roi.copy()
    overlay[:] = colour
    cv2.addWeighted(overlay, alpha, roi, 1 - alpha, 0, roi)
    frame[y1:y2, x1:x2] = roi


def _border(frame, x1, y1, x2, y2, colour, thick=1):
    cv2.rectangle(frame, (x1, y1), (x2, y2), colour, thick, cv2.LINE_AA)


def _text_center(frame, text, cx, cy, font, scale, colour, thick=1):
    (tw, th), _ = cv2.getTextSize(text, font, scale, thick)
    cv2.putText(frame, text, (cx - tw // 2, cy + th // 2),
                font, scale, colour, thick, cv2.LINE_AA)


def _text_shadow(frame, text, x, y, font, scale, colour, thick=1):
    cv2.putText(frame, text, (x + 1, y + 1), font, scale,
                (8, 8, 10), thick + 1, cv2.LINE_AA)
    cv2.putText(frame, text, (x, y), font, scale, colour, thick, cv2.LINE_AA)


def _glow_dot(frame, cx, cy, outer_r, inner_r, outer_col, inner_col):
    """Bright dot with a glow halo — used on arc tips."""
    cv2.circle(frame, (cx, cy), outer_r, outer_col, -1, cv2.LINE_AA)
    cv2.circle(frame, (cx, cy), inner_r, inner_col,  -1, cv2.LINE_AA)


# ---------------------------------------------------------------------------
# HUD components
# ---------------------------------------------------------------------------

def draw_score_panel(frame: np.ndarray, score: Score, smart: bool) -> None:
    """Top-left score card: player / CPU / draw + mode badge."""
    x1, y1, x2, y2 = 10, 10, 318, 108

    # Panel background with a subtle left accent bar
    _blend(frame, x1, y1, x2, y2, C["bg_panel"], alpha=0.88)
    _border(frame, x1, y1, x2, y2, C["border"])
    cv2.rectangle(frame, (x1, y1), (x1 + 3, y2), C["neon"], -1)

    # Score columns
    cols = [
        ("YOU",  score.player, C["green"],  26),
        ("CPU",  score.cpu,    C["red"],   126),
        ("DRAW", score.draws,  C["amber"], 222),
    ]
    for label, val, col, lx in cols:
        cv2.putText(frame, label,    (lx, 38), FONT_PLAIN, 0.46, C["dim"],  1, cv2.LINE_AA)
        cv2.putText(frame, str(val), (lx, 72), FONT_BOLD,  1.05, col,       2, cv2.LINE_AA)

    # Divider + mode badge
    cv2.line(frame, (x1 + 4, y2 - 28), (x2, y2 - 28), C["border"], 1)
    badge     = "SMART MODE  ON" if smart else "NORMAL MODE"
    badge_col = C["neon"] if smart else C["dim"]
    cv2.putText(frame, badge, (26, y2 - 10), FONT_PLAIN, 0.42, badge_col, 1, cv2.LINE_AA)


def draw_gesture_label(frame: np.ndarray, gesture: str) -> None:
    """Detected gesture badge — top-left, below the score card."""
    x1, y1, x2, y2 = 10, 118, 318, 162
    _blend(frame, x1, y1, x2, y2, C["bg_panel"], alpha=0.82)
    _border(frame, x1, y1, x2, y2, C["border"])
    cv2.rectangle(frame, (x1, y1), (x1 + 3, y2), GESTURE_COLOUR.get(gesture, C["dim"]), -1)

    colour = GESTURE_COLOUR.get(gesture, C["dim"])
    label  = f"GESTURE   {gesture.upper()}"
    cv2.putText(frame, label, (24, 147), FONT_PLAIN, 0.58, colour, 1, cv2.LINE_AA)


def draw_cpu_badge(frame: np.ndarray, gesture: str) -> None:
    """CPU move badge in the top-right corner, shown during result phase."""
    h, w = frame.shape[:2]
    label = f"CPU   {gesture.upper()}"
    (tw, _), _ = cv2.getTextSize(label, FONT_PLAIN, 0.58, 1)
    x1, y1 = w - tw - 52, 10
    x2, y2 = w - 10, 58
    _blend(frame, x1, y1, x2, y2, C["bg_panel"], alpha=0.88)
    _border(frame, x1, y1, x2, y2, C["border"])
    cv2.rectangle(frame, (x2 - 3, y1), (x2, y2),
                  GESTURE_COLOUR.get(gesture, C["white"]), -1)
    colour = GESTURE_COLOUR.get(gesture, C["white"])
    cv2.putText(frame, label, (x1 + 14, y2 - 14), FONT_PLAIN, 0.58, colour, 1, cv2.LINE_AA)


def draw_countdown(frame: np.ndarray, text: str, progress: float) -> None:
    """
    Centred countdown with a sweeping neon arc, glow dot, and animated ring.
    progress is 0.0 → 1.0 over COUNTDOWN_SECS.
    """
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    R = 90

    # Darken a wide strip so the countdown stands out over the webcam
    _blend(frame, 0, cy - 130, w, cy + 130, C["bg_panel"], alpha=0.55)

    # Dim track ring
    cv2.ellipse(frame, (cx, cy), (R, R), -90, 0, 360,
                (30, 30, 42), 5, cv2.LINE_AA)

    # Progress arc — thick dark glow then thinner bright highlight
    end_angle = int(360 * progress)
    if end_angle > 0:
        cv2.ellipse(frame, (cx, cy), (R, R), -90, 0, end_angle,
                    C["neon"], 10, cv2.LINE_AA)
        cv2.ellipse(frame, (cx, cy), (R, R), -90, 0, end_angle,
                    C["white"], 2, cv2.LINE_AA)

        # Glow dot that rides the arc's leading edge
        tip_rad = math.radians(-90 + end_angle)
        tx = cx + int(R * math.cos(tip_rad))
        ty = cy + int(R * math.sin(tip_rad))
        _glow_dot(frame, tx, ty, 9, 5, C["white"], C["neon"])

    # Label inside the ring
    font      = FONT_BOLD if text == "SHOOT!" else FONT
    scale     = 1.85  if text == "SHOOT!" else 1.25
    text_col  = C["green"] if text == "SHOOT!" else C["white"]
    thick     = 2
    _text_center(frame, text, cx, cy, font, scale, text_col, thick)

    # Small percentage below
    pct = f"{int(progress * 100)}%"
    cv2.putText(frame, pct, (cx - 18, cy + R + 22),
                FONT_PLAIN, 0.45, C["dim"], 1, cv2.LINE_AA)


def draw_result_panel(
    frame: np.ndarray,
    player_gesture: str,
    cpu_gesture:    str,
    result:         str,
) -> None:
    """Full-width result banner at the bottom of the frame."""
    h, w = frame.shape[:2]
    panel_h = 148
    y1 = h - panel_h

    # Colour-coded tinted background
    if "Win" in result:
        tint = (18, 52, 18)
    elif "CPU" in result:
        tint = (18, 18, 52)
    else:
        tint = (38, 38, 12)

    _blend(frame, 0, y1, w, h, tint, alpha=0.85)
    cv2.line(frame, (0, y1), (w, y1), C["border_hi"], 1)

    # Decorative accent line at top of panel
    if "Win" in result:
        accent = C["green"]
    elif "CPU" in result:
        accent = C["red"]
    else:
        accent = C["amber"]
    cv2.line(frame, (0, y1), (w, y1), accent, 2)

    # "YOU  Rock  vs  CPU  Paper" line
    player_col = GESTURE_COLOUR.get(player_gesture, C["white"])
    cpu_col    = GESTURE_COLOUR.get(cpu_gesture, C["white"])

    mid = w // 2
    _text_shadow(frame, f"YOU  {player_gesture}", mid - 238, y1 + 46, FONT_PLAIN, 0.74, player_col)
    _text_shadow(frame, "vs",                     mid -  16, y1 + 46, FONT_PLAIN, 0.62, C["dim"])
    _text_shadow(frame, f"CPU  {cpu_gesture}",    mid +  36, y1 + 46, FONT_PLAIN, 0.74, cpu_col)

    cv2.line(frame, (48, y1 + 62), (w - 48, y1 + 62), C["border"], 1)

    # Big result label
    _text_center(frame, result.upper(), mid, y1 + 108, FONT_BOLD, 1.15, accent, 2)


def draw_no_hand_warning(frame: np.ndarray) -> None:
    """Centre-screen prompt when no hand is in view."""
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    text = "Show your hand to start"
    (tw, th), _ = cv2.getTextSize(text, FONT_PLAIN, 0.76, 1)
    pad = 22
    _blend(frame,
           cx - tw // 2 - pad, cy - th - pad,
           cx + tw // 2 + pad, cy + th + pad,
           C["bg_panel"], alpha=0.82)
    _border(frame,
            cx - tw // 2 - pad, cy - th - pad,
            cx + tw // 2 + pad, cy + th + pad,
            C["amber"])
    _text_center(frame, text, cx, cy, FONT_PLAIN, 0.76, C["amber"])


def draw_waiting_indicator(frame: np.ndarray, gesture: str) -> None:
    """Subtle hint while gesture is detected but countdown hasn't fired yet."""
    h, w = frame.shape[:2]
    text = "Hold steady — countdown starting..."
    (tw, _), _ = cv2.getTextSize(text, FONT_PLAIN, 0.55, 1)
    _text_shadow(frame, text, (w - tw) // 2, h - 165, FONT_PLAIN, 0.55, C["dim"])


def draw_controls_hint(frame: np.ndarray) -> None:
    """Keyboard shortcut bar pinned to the very bottom edge."""
    h, w = frame.shape[:2]
    _blend(frame, 0, h - 24, w, h, C["bg_panel"], alpha=0.75)
    hints = "Q  Quit      R  Reset Score      S  Toggle Smart Mode"
    (tw, _), _ = cv2.getTextSize(hints, FONT_PLAIN, 0.40, 1)
    cv2.putText(frame, hints, ((w - tw) // 2, h - 7),
                FONT_PLAIN, 0.40, C["dim"], 1, cv2.LINE_AA)


def draw_fps(frame: np.ndarray, fps: float) -> None:
    """Small FPS readout — bottom-right corner."""
    h, w = frame.shape[:2]
    label = f"{fps:.0f} fps"
    (tw, _), _ = cv2.getTextSize(label, FONT_PLAIN, 0.38, 1)
    cv2.putText(frame, label, (w - tw - 12, h - 32),
                FONT_PLAIN, 0.38, C["dim"], 1, cv2.LINE_AA)


def draw_round_flash(frame: np.ndarray, result: str, age: float) -> None:
    """
    Full-screen colour flash at the moment of SHOOT.
    age = seconds since result (fades over 0.25 s).
    """
    if age > 0.25:
        return
    if "Win" in result:
        tint = C["green"]
    elif "CPU" in result:
        tint = C["red"]
    else:
        tint = C["amber"]
    alpha = 0.48 * (1.0 - age / 0.25)
    _blend(frame, 0, 0, frame.shape[1], frame.shape[0], tint, alpha=alpha)
