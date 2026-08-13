import cv2
import time
from enum import Enum, auto

from hand_tracker       import HandTracker
from gesture_classifier import GestureClassifier, UNKNOWN
from game_logic         import GameLogic
from ui_overlay         import (
    draw_score_panel,
    draw_gesture_label,
    draw_countdown,
    draw_result_panel,
    draw_controls_hint,
    draw_no_hand_warning,
    draw_ai_gesture_icon,
    draw_fps,
    draw_waiting_indicator,
    draw_round_flash,
)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CAMERA_INDEX        = 1      # index 1 = real webcam (0 is grabbed by Smart Connect)
FRAME_WIDTH         = 960
FRAME_HEIGHT        = 540
COUNTDOWN_SECS      = 3.0
RESULT_DISPLAY_SECS = 3.0

# Text shown at each quarter of the countdown timer
COUNTDOWN_LABELS = [
    (0.00, "Rock..."),
    (0.25, "Paper..."),
    (0.50, "Scissors..."),
    (0.75, "SHOOT!"),
]


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

class GameState(Enum):
    WAITING   = auto()
    COUNTDOWN = auto()
    SHOOT     = auto()
    RESULT    = auto()


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------

class RPSGame:
    """Top-level class: wires the webcam, detector, classifier, logic and HUD."""

    def __init__(self) -> None:
        self.tracker    = HandTracker()
        self.classifier = GestureClassifier()
        self.game       = GameLogic(smart_ai=False)

        self.state           = GameState.WAITING
        self.countdown_start = 0.0
        self.result_start    = 0.0

        self.player_gesture = UNKNOWN
        self.ai_gesture     = UNKNOWN
        self.round_result   = ""

        self.prev_frame_time = time.time()
        self.fps             = 0.0

    def run(self) -> None:
        cap = self._open_camera()
        if cap is None:
            return

        print("[INFO] Game running. Q=quit  R=reset  S=smart AI toggle")

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("[ERROR] Camera read failed — exiting.")
                    break

                frame = cv2.flip(frame, 1)  # mirror so it feels natural

                frame, hand_result = self.tracker.process_frame(frame, draw_landmarks=True)
                current_gesture = UNKNOWN
                if hand_result:
                    current_gesture = self.classifier.classify(hand_result.landmarks)

                self._update_state(current_gesture)
                self._render(frame, current_gesture)

                now = time.time()
                self.fps = 1.0 / max(now - self.prev_frame_time, 1e-6)
                self.prev_frame_time = now

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    self.game.reset_score()
                    self.state = GameState.WAITING
                    print("[INFO] Score reset.")
                elif key == ord('s'):
                    smart = self.game.toggle_ai_mode()
                    print(f"[INFO] AI mode: {'SMART' if smart else 'RANDOM'}")
        finally:
            cap.release()
            self.tracker.release()
            cv2.destroyAllWindows()

    # -----------------------------------------------------------------------
    # State transitions
    # -----------------------------------------------------------------------

    def _update_state(self, gesture: str) -> None:
        now = time.time()

        if self.state == GameState.WAITING:
            if gesture != UNKNOWN:
                self.state           = GameState.COUNTDOWN
                self.countdown_start = now

        elif self.state == GameState.COUNTDOWN:
            elapsed = now - self.countdown_start
            if gesture == UNKNOWN:
                # Hand left the frame — cancel and go back to idle
                self.state = GameState.WAITING
            elif elapsed / COUNTDOWN_SECS >= 1.0:
                self.state = GameState.SHOOT

        elif self.state == GameState.SHOOT:
            # Latch whatever gesture is visible right now
            self.player_gesture = gesture if gesture != UNKNOWN else "Rock"
            self.ai_gesture, self.round_result = self.game.play_round(self.player_gesture)
            self.result_start = now
            self.state = GameState.RESULT

        elif self.state == GameState.RESULT:
            if now - self.result_start >= RESULT_DISPLAY_SECS:
                self.state = GameState.WAITING

    # -----------------------------------------------------------------------
    # Rendering
    # -----------------------------------------------------------------------

    def _render(self, frame, gesture: str) -> None:
        now = time.time()

        # Persistent HUD elements
        draw_score_panel(frame, self.game.score, self.game.ai.smart_mode)
        draw_gesture_label(frame, gesture)
        draw_controls_hint(frame)
        draw_fps(frame, self.fps)

        # State-specific overlays
        if self.state == GameState.WAITING:
            if gesture == UNKNOWN:
                draw_no_hand_warning(frame)
            else:
                draw_waiting_indicator(frame, gesture)

        elif self.state == GameState.COUNTDOWN:
            progress = min((now - self.countdown_start) / COUNTDOWN_SECS, 1.0)
            label = "Rock..."
            for threshold, text in COUNTDOWN_LABELS:
                if progress >= threshold:
                    label = text
            draw_countdown(frame, label, progress)

        elif self.state == GameState.RESULT:
            age = now - self.result_start
            draw_round_flash(frame, self.round_result, age)   # brief colour flash
            draw_result_panel(frame, self.player_gesture, self.ai_gesture, self.round_result)
            draw_ai_gesture_icon(frame, self.ai_gesture)

        cv2.imshow("Rock Paper Scissors — CV Edition", frame)

    # -----------------------------------------------------------------------
    # Camera
    # -----------------------------------------------------------------------

    def _open_camera(self):
        """
        Open the webcam. cv2.VideoCapture doesn't raise — it returns a dud
        object on failure, so we always check isOpened().
        CAP_DSHOW forces Windows DirectShow, which respects the device index
        reliably when virtual cameras (Smart Connect, OBS, etc.) are present.
        """
        try:
            cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
            if not cap.isOpened():
                print(
                    f"[ERROR] Cannot open camera index {CAMERA_INDEX}.\n"
                    "  Check that it's connected and not in use, or change CAMERA_INDEX."
                )
                return None
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"[INFO] Camera {CAMERA_INDEX} opened at {w}x{h}")
            return cap
        except Exception as e:
            print(f"[ERROR] Camera open failed: {e}")
            return None


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    RPSGame().run()
