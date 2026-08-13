"""Quick unit tests for gesture classifier and game logic."""
import sys
sys.path.insert(0, '.')

from gesture_classifier import GestureClassifier, ROCK, PAPER, SCISSORS, UNKNOWN
from game_logic import GameLogic, RESULT_WIN, RESULT_LOSE, RESULT_DRAW

clf = GestureClassifier()

def make_landmarks():
    return [(0.5, 0.5, 0.0)] * 21

# Rock: all fingers curled (tip y > pip y)
lm = make_landmarks()
lm[8]  = (0.5, 0.8, 0.0);  lm[6]  = (0.5, 0.5, 0.0)  # index
lm[12] = (0.5, 0.8, 0.0);  lm[10] = (0.5, 0.5, 0.0)  # middle
lm[16] = (0.5, 0.8, 0.0);  lm[14] = (0.5, 0.5, 0.0)  # ring
lm[20] = (0.5, 0.8, 0.0);  lm[18] = (0.5, 0.5, 0.0)  # pinky
assert clf.classify(lm) == ROCK, f"Expected Rock, got {clf.classify(lm)}"
print("PASS: Rock detection")

# Paper: all fingers extended (tip y < pip y)
lm2 = make_landmarks()
lm2[8]  = (0.5, 0.2, 0.0); lm2[6]  = (0.5, 0.5, 0.0)
lm2[12] = (0.5, 0.2, 0.0); lm2[10] = (0.5, 0.5, 0.0)
lm2[16] = (0.5, 0.2, 0.0); lm2[14] = (0.5, 0.5, 0.0)
lm2[20] = (0.5, 0.2, 0.0); lm2[18] = (0.5, 0.5, 0.0)
assert clf.classify(lm2) == PAPER, f"Expected Paper, got {clf.classify(lm2)}"
print("PASS: Paper detection")

# Scissors: index+middle up, ring+pinky down
lm3 = make_landmarks()
lm3[8]  = (0.5, 0.2, 0.0); lm3[6]  = (0.5, 0.5, 0.0)  # index UP
lm3[12] = (0.5, 0.2, 0.0); lm3[10] = (0.5, 0.5, 0.0)  # middle UP
lm3[16] = (0.5, 0.8, 0.0); lm3[14] = (0.5, 0.5, 0.0)  # ring DOWN
lm3[20] = (0.5, 0.8, 0.0); lm3[18] = (0.5, 0.5, 0.0)  # pinky DOWN
assert clf.classify(lm3) == SCISSORS, f"Expected Scissors, got {clf.classify(lm3)}"
print("PASS: Scissors detection")

# Unknown: alternating pattern
lm4 = make_landmarks()
lm4[8]  = (0.5, 0.2, 0.0); lm4[6]  = (0.5, 0.5, 0.0)  # index UP
lm4[12] = (0.5, 0.8, 0.0); lm4[10] = (0.5, 0.5, 0.0)  # middle DOWN
lm4[16] = (0.5, 0.2, 0.0); lm4[14] = (0.5, 0.5, 0.0)  # ring UP
lm4[20] = (0.5, 0.8, 0.0); lm4[18] = (0.5, 0.5, 0.0)  # pinky DOWN
assert clf.classify(lm4) == UNKNOWN, f"Expected Unknown, got {clf.classify(lm4)}"
print("PASS: Unknown detection")

# Game logic tests
g = GameLogic()
_, result = g.play_round(ROCK)
print(f"PASS: play_round() returned: {result!r}")
g.reset_score()
assert g.score.player == 0 and g.score.cpu == 0
print("PASS: Score reset")

# Smart Mode toggle
prev = g.ai.smart_mode
smart = g.toggle_ai_mode()
assert smart != prev
print(f"PASS: AI mode toggled to smart={smart}")

print()
print("All logic tests passed!")
