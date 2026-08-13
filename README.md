# ✊✋✌️ Rock Paper Scissors — Computer Vision Edition

> Play Rock Paper Scissors using **real hand gestures** captured live from your webcam — no keyboard, no mouse, just your hand.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green?logo=opencv)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Hands-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## ✨ Features

| Feature | Details |
|---|---|
| 🎥 **Live Webcam Feed** | Real-time video capture via OpenCV |
| ✋ **Hand Gesture Detection** | MediaPipe 21-landmark hand model |
| ✊ ✋ ✌️ **Rock / Paper / Scissors** | Rule-based finger-state classifier |
| ⏱️ **3-Second Countdown** | Animated "Rock… Paper… Scissors… SHOOT!" |
| 🖥️ **CPU Opponent** | Random mode OR Smart frequency-prediction mode |
| 📊 **Live Scoreboard** | Persistent across rounds in a session |
| 🎨 **HUD Overlays** | Gesture label, countdown arc, result banner |
| ⌨️ **Keyboard Controls** | `Q` quit · `R` reset · `S` toggle Smart Mode |

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **OpenCV** (`opencv-python`) — webcam capture, frame rendering, drawing
- **MediaPipe** — real-time hand landmark detection (21 keypoints per hand)
- **NumPy** — array operations for frame processing

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/Ashish-dev-prog/rps-cv-game.git
cd rps-cv-game
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ How to Run

```bash
python main.py
```

> **Requirements:** A working webcam connected to your machine.
> If your camera doesn't open, edit `CAMERA_INDEX` in `main.py` (try `0`, `1`, or `2`).

---

## 🕹️ How to Play

1. Run `python main.py` — the webcam window opens.
2. **Show your hand** to the camera.
3. The countdown begins: **Rock… Paper… Scissors… SHOOT!**
4. Hold your gesture steady — it is captured at **"SHOOT!"**.
5. See your gesture vs. the CPU's move, and the round result.
6. A new round starts automatically after 3 seconds.

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Q` | Quit the game |
| `R` | Reset the score |
| `S` | Toggle Smart Mode on/off |

---

## 🧠 How Gesture Detection Works

### MediaPipe Hand Landmarks

MediaPipe's hand model returns **21 3D landmark points** per detected hand, numbered 0–20:

```
                  8   12  16  20
                  |   |   |   |
              7   11  15  19
              |   |   |   |
          6   10  14  18
          |   |   |   |
      5   9   13  17
      |   |   |   |
  4   |   |   |   |
  |   MCP MCP MCP MCP
  3
  |
  2
  |
  1
  |
  0 (WRIST)
```

Key indices used:
- `TIP` = fingertip (8, 12, 16, 20 for Index → Pinky)
- `PIP` = proximal interphalangeal joint, the "middle knuckle" (6, 10, 14, 18)

### The Finger-State Rule

MediaPipe uses **normalised image coordinates** — `(0, 0)` is the **top-left** of the frame, so **larger `y` = lower on screen**.

```
FINGER EXTENDED:                  FINGER CURLED:

  TIP  ← small y (high up)         PIP  ← small y (high up)
   |                                 |
  PIP  ← large y (lower down)       TIP  ← large y (lower down)
```

**Rule:**
```
tip.y  <  pip.y   →   finger is UP   (extended) = 1
tip.y  >  pip.y   →   finger is DOWN (curled)   = 0
```

### Gesture Lookup Table

We check all 4 non-thumb fingers and build a **4-bit pattern**:

| Index | Middle | Ring | Pinky | Gesture   |
|:-----:|:------:|:----:|:-----:|-----------|
|   0   |   0    |  0   |   0   | ✊ Rock    |
|   1   |   1    |  1   |   1   | ✋ Paper   |
|   1   |   1    |  0   |   0   | ✌️ Scissors |
| other | other  | other|other  | Unknown   |

> **Why skip the thumb?**  
> The thumb bends *sideways* rather than up/down, making a vertical y-comparison unreliable.

---

## 🔮 Smart Mode

Press **`S`** to enable Smart Mode.

Instead of picking randomly, the CPU:
1. Tracks every gesture you've thrown this session.
2. Finds your **most frequent** gesture.
3. Picks the counter-move against it.

> **Example:** You throw Rock 6 times, Paper 2, Scissors 1 → CPU predicts Rock → CPU plays Paper.

Activates after ≥ 3 rounds of history.

---

## 📁 Project Structure

```
rps-cv-game/
├── main.py                # Entry point — game loop + state machine
├── hand_tracker.py        # MediaPipe wrapper, landmark indices, HandResult
├── gesture_classifier.py  # Finger-state logic → Rock / Paper / Scissors
├── game_logic.py          # CPU opponent, winner rules, scoring
├── ui_overlay.py          # All cv2 drawing helpers (HUD, countdown, result)
├── test_logic.py          # Unit tests (no webcam needed)
├── requirements.txt
└── README.md
```

---

## 🖼️ Screenshots / Demo

> _Run the game and capture a screenshot here!_

---

## 🔮 Future Improvements

- **Multiplayer mode** — detect two hands simultaneously and let two humans play.
- **Gesture confidence score** — display a percentage so the player knows when detection is uncertain.
- **Sound effects** — countdown beeps and win/lose sounds with `pygame`.
- **Round history log** — save each round's result to a CSV for post-game review.

---

## 📄 License

MIT License — feel free to use, modify, and share.

---

## 🙏 Acknowledgements

- [MediaPipe](https://mediapipe.dev/) by Google for the hand landmark model.
- [OpenCV](https://opencv.org/) for webcam capture and image processing.
