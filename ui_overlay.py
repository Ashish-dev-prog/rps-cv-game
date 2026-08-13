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
    "bg_panel":   (15,  15,  18),   # near-black card background
    "border":     (50,  50,  60),   # subtle panel border
    "white":      (245, 245, 250),
    "dim":        (130, 130, 140),
    "green":      (80,  230, 110),  # win
    "red":        (70,   70, 235),  # lose
    "amber":      (40,  195, 255),  # draw / warning
    "neon_blue":  (255, 190,  55),  # accent / countdown arc
    "rock":       (190,  90, 220),  # Rock gesture colour
    "paper":      (255, 175,  55),  # Paper
    "scissors":   (55,  225, 225),  # Scissors
}

GESTURE_COLOUR = {
    "Rock":     C["rock"],
    "Paper":    C["paper"],
    "Scissors": C["scissors"],
    "Unknown":  C["dim"],
}

RESULT_COLOUR = {
    "win":  C["green"],
    "lose": C["red"],
    "draw": C["amber"],
}

FONT        = cv2.FONT_HERSHEY_DUPLEX
FONT_BOLD   = cv2.FONT_HERSHEY_TRIPLEX
FONT_PLAIN  = cv2.FONT_HERSHEY_SIMPLEX

GESTURE_ICON = {"Rock": "[R]", "Paper": "[P]", "Scissors": "[S]", "Unknown": "[?]"}


# ---------------------------------------------------------------------------
# Drawing primitives
# ---------------------------------------------------------------------------

def _blend_rect(frame, x1, y1, x2, y2, colour, alpha=0.72):
    """Alpha-blended filled rectangle over the live frame."""
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


def _border_rect(frame, x1, y1, x2, y2, colour, thickness=1):
    """Thin border rectangle — no fill."""
    cv2.rectangle(frame, (x1, y1), (x2, y2), colour, thickness, cv2.LINE_AA)


def _text_centered(frame, text, cx, cy, font, scale, colour, thickness=1):
    """Draw text horizontally centred on cx."""
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    cv2.putText(frame, text, (cx - tw // 2, cy + th // 2),
                font, scale, colour, thickness, cv2.LINE_AA)


def _text_shadowed(frame, text, x, y, font, scale, colour, thickness=1):
    """Text with a dark 1-pixel offset shadow for contrast."""
    cv2.putText(frame, text, (x + 1, y + 1), font, scale,
                (10, 10, 12), thickness + 1, cv2.LINE_AA)
    cv2.putText(frame, text, (x, y), font, scale, colour, thickness, cv2.LINE_AA)


# ---------------------------------------------------------------------------
# HUD components
# ---------------------------------------------------------------------------

def draw_score_panel(frame: np.ndarray, score: Score, ai_smart: bool) -> None:
    """Top-left score card: player score, CPU score, AI mode badge."""
    x1, y1, x2, y2 = 10, 10, 310, 100
    _blend_rect(frame, x1, y1, x2, y2, C["bg_panel"], alpha=0.82)
    _border_rect(frame, x1, y1, x2, y2, C["border"])

    # Score numbers
    cv2.putText(frame, "YOU", (22, 38), FONT_PLAIN, 0.5, C["dim"], 1, cv2.LINE_AA)
    cv2.putText(frame, str(score.player), (22, 65), FONT_BOLD, 1.0, C["green"], 2, cv2.LINE_AA)

    cv2.putText(frame, "CPU", (120, 38), FONT_PLAIN, 0.5, C["dim"], 1, cv2.LINE_AA)
    cv2.putText(frame, str(score.cpu), (120, 65), FONT_BOLD, 1.0, C["red"], 2, cv2.LINE_AA)

    cv2.putText(frame, "DRAW", (210, 38), FONT_PLAIN, 0.5, C["dim"], 1, cv2.LINE_AA)
    cv2.putText(frame, str(score.draws), (210, 65), FONT_BOLD, 1.0, C["amber"], 2, cv2.LINE_AA)

    # Thin separator before AI badge
    cv2.line(frame, (x1, y2 - 26), (x2, y2 - 26), C["border"], 1)
    badge = "SMART AI  ON" if ai_smart else "RANDOM AI"
    badge_col = C["neon_blue"] if ai_smart else C["dim"]
    cv2.putText(frame, badge, (22, y2 - 9), FONT_PLAIN, 0.42, badge_col, 1, cv2.LINE_AA)


def draw_gesture_label(frame: np.ndarray, gesture: str) -> None:
    """Detected gesture badge — top-left, below the score card."""
    x1, y1, x2, y2 = 10, 110, 310, 155
    _blend_rect(frame, x1, y1, x2, y2, C["bg_panel"], alpha=0.78)
    _border_rect(frame, x1, y1, x2, y2, C["border"])

    colour = GESTURE_COLOUR.get(gesture, C["dim"])
    label  = f"GESTURE  {gesture.upper()}"
    cv2.putText(frame, label, (22, 140), FONT_PLAIN, 0.58, colour, 1, cv2.LINE_AA)


def draw_ai_gesture_icon(frame: np.ndarray, gesture: str) -> None:
    """CPU gesture badge in the top-right corner, shown during result phase."""
    h, w = frame.shape[:2]
    label = f"CPU  {gesture.upper()}"
    (tw, _), _ = cv2.getTextSize(label, FONT_PLAIN, 0.58, 1)
    x1, y1 = w - tw - 44, 10
    x2, y2 = w - 10, 55
    _blend_rect(frame, x1, y1, x2, y2, C["bg_panel"], alpha=0.82)
    _border_rect(frame, x1, y1, x2, y2, C["border"])
    colour = GESTURE_COLOUR.get(gesture, C["white"])
    cv2.putText(frame, label, (x1 + 12, y2 - 14), FONT_PLAIN, 0.58, colour, 1, cv2.LINE_AA)


def draw_countdown(frame: np.ndarray, text: str, progress: float) -> None:
    """
    Centred countdown display with a sweeping neon arc and animated glow ring.
    progress is 0.0 → 1.0 over COUNTDOWN_SECS.
    """
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2

    # Darken the entire centre strip so the countdown pops
    _blend_rect(frame, 0, cy - 110, w, cy + 110, C["bg_panel"], alpha=0.55)

    # Outer dim track ring
    cv2.ellipse(frame, (cx, cy), (160, 160), -90, 0, 360,
                C["border"], 3, cv2.LINE_AA)

    # Animated neon arc that fills as time progresses
    end_angle = int(360 * progress)
    # Draw in thick steps for a glow effect — thick dark then thinner bright
    cv2.ellipse(frame, (cx, cy), (160, 160), -90, 0, end_angle,
                C["neon_blue"], 8, cv2.LINE_AA)
    cv2.ellipse(frame, (cx, cy), (160, 160), -90, 0, end_angle,
                C["white"], 2, cv2.LINE_AA)

    # Text sits inside the ring
    font      = FONT_BOLD if text == "SHOOT!" else FONT
    scale     = 1.8 if text == "SHOOT!" else 1.2
    text_col  = C["green"] if text == "SHOOT!" else C["white"]
    _text_centered(frame, text, cx, cy, font, scale, text_col, 2)

    # Small progress percentage below
    pct = f"{int(progress * 100)}%"
    cv2.putText(frame, pct, (cx - 18, cy + 130),
                FONT_PLAIN, 0.45, C["dim"], 1, cv2.LINE_AA)


def draw_result_panel(
    frame: np.ndarray,
    player_gesture: str,
    ai_gesture:     str,
    result:         str,
) -> None:
    """Full-width result banner at the bottom of the frame."""
    h, w = frame.shape[:2]
    panel_h = 140
    y1 = h - panel_h

    # Tinted background — colour-coded by result
    if "Win" in result:
        tint = (20, 55, 20)
    elif "CPU" in result:
        tint = (20, 20, 55)
    else:
        tint = (40, 40, 15)
    _blend_rect(frame, 0, y1, w, h, tint, alpha=0.80)
    cv2.line(frame, (0, y1), (w, y1), C["border"], 1)

    # "YOU  Rock  vs  CPU  Paper" line
    player_col = GESTURE_COLOUR.get(player_gesture, C["white"])
    ai_col     = GESTURE_COLOUR.get(ai_gesture, C["white"])

    mid = w // 2
    _text_shadowed(frame, f"YOU  {player_gesture}", mid - 230, y1 + 42, FONT_PLAIN, 0.72, player_col)
    _text_shadowed(frame, "vs",                     mid -  15, y1 + 42, FONT_PLAIN, 0.6,  C["dim"])
    _text_shadowed(frame, f"CPU  {ai_gesture}",     mid +  32, y1 + 42, FONT_PLAIN, 0.72, ai_col)

    # Separator
    cv2.line(frame, (40, y1 + 58), (w - 40, y1 + 58), C["border"], 1)

    # Big result label
    if "Win" in result:
        r_col  = C["green"]
    elif "CPU" in result:
        r_col  = C["red"]
    else:
        r_col  = C["amber"]

    _text_centered(frame, result.upper(), mid, y1 + 105, FONT_BOLD, 1.1, r_col, 2)


def draw_no_hand_warning(frame: np.ndarray) -> None:
    """Centre-screen prompt when no hand is in view."""
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    text = "Show your hand to start"
    (tw, th), _ = cv2.getTextSize(text, FONT_PLAIN, 0.75, 1)
    pad = 20
    _blend_rect(frame, cx - tw // 2 - pad, cy - th - pad,
                       cx + tw // 2 + pad, cy + th + pad,
                C["bg_panel"], alpha=0.78)
    _border_rect(frame, cx - tw // 2 - pad, cy - th - pad,
                        cx + tw // 2 + pad, cy + th + pad, C["amber"])
    _text_centered(frame, text, cx, cy, FONT_PLAIN, 0.75, C["amber"], 1)


def draw_waiting_indicator(frame: np.ndarray, gesture: str) -> None:
    """Subtle prompt shown while gesture is detected but countdown hasn't fired yet."""
    h, w = frame.shape[:2]
    text = "Hold steady — countdown starting..."
    (tw, _), _ = cv2.getTextSize(text, FONT_PLAIN, 0.55, 1)
    _text_shadowed(frame, text, (w - tw) // 2, h - 160, FONT_PLAIN, 0.55, C["dim"])


def draw_controls_hint(frame: np.ndarray) -> None:
    """Keyboard shortcut bar pinned to the very bottom edge."""
    h, w = frame.shape[:2]
    _blend_rect(frame, 0, h - 22, w, h, C["bg_panel"], alpha=0.70)
    hints = "Q  Quit      R  Reset Score      S  Toggle Smart AI"
    (tw, _), _ = cv2.getTextSize(hints, FONT_PLAIN, 0.40, 1)
    cv2.putText(frame, hints, ((w - tw) // 2, h - 6),
                FONT_PLAIN, 0.40, C["dim"], 1, cv2.LINE_AA)


def draw_fps(frame: np.ndarray, fps: float) -> None:
    """Small FPS readout — bottom-right corner."""
    h, w = frame.shape[:2]
    label = f"{fps:.0f} fps"
    (tw, _), _ = cv2.getTextSize(label, FONT_PLAIN, 0.38, 1)
    cv2.putText(frame, label, (w - tw - 10, h - 28),
                FONT_PLAIN, 0.38, C["dim"], 1, cv2.LINE_AA)


def draw_round_flash(frame: np.ndarray, result: str, age: float) -> None:
    """
    Optional full-screen colour flash right at the moment of SHOOT.
    age = seconds since the result was determined (0 → 0.25 s).
    Fades from 0.45 → 0 alpha quickly.
    """
    if age > 0.25:
        return
    if "Win" in result:
        tint = C["green"]
    elif "CPU" in result:
        tint = C["red"]
    else:
        tint = C["amber"]
    alpha = 0.45 * (1.0 - age / 0.25)
    _blend_rect(frame, 0, 0, frame.shape[1], frame.shape[0], tint, alpha=alpha)
