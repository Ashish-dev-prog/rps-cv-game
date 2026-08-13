# -*- coding: utf-8 -*-
"""
game_logic.py  —  AI opponent, winner resolution, and score tracking.
No UI code here — just the rules of the game and the AI's decision making.
"""

import random
from collections import Counter


ROCK     = "Rock"
PAPER    = "Paper"
SCISSORS = "Scissors"
GESTURES = [ROCK, PAPER, SCISSORS]

# X beats Y
BEATS: dict[str, str] = {
    ROCK:     SCISSORS,
    SCISSORS: PAPER,
    PAPER:    ROCK,
}

RESULT_WIN  = "You Win!"
RESULT_LOSE = "CPU Wins!"
RESULT_DRAW = "Draw!"


class Score:
    def __init__(self) -> None:
        self.player = 0
        self.cpu    = 0
        self.draws  = 0

    def reset(self) -> None:
        self.player = self.cpu = self.draws = 0


class AIPlayer:
    """
    Two modes:

    Random — uniform random pick each round. Fair and unpredictable.

    Smart  — after ≥3 rounds of history, finds the player's most-thrown
             gesture and picks the counter-move. Simple frequency analysis,
             not ML, but it works well against people with habits.
    """

    def __init__(self, smart_mode: bool = False) -> None:
        self.smart_mode   = smart_mode
        self.history: list[str] = []

    def pick_move(self) -> str:
        if self.smart_mode and len(self.history) >= 3:
            predicted = Counter(self.history).most_common(1)[0][0]
            # Return the gesture that beats the predicted one
            for winner, loser in BEATS.items():
                if loser == predicted:
                    return winner
        return random.choice(GESTURES)

    def record(self, gesture: str) -> None:
        if gesture in GESTURES:
            self.history.append(gesture)

    def toggle(self) -> bool:
        self.smart_mode = not self.smart_mode
        return self.smart_mode


class GameLogic:
    """Coordinates one round: AI picks, result determined, score updated."""

    def __init__(self, smart_ai: bool = False) -> None:
        self.score = Score()
        self.ai    = AIPlayer(smart_mode=smart_ai)

    def play_round(self, player: str) -> tuple[str, str]:
        """Returns (ai_gesture, result_string)."""
        ai_move = self.ai.pick_move()
        self.ai.record(player)

        if player == ai_move:
            result = RESULT_DRAW
        elif BEATS.get(player) == ai_move:
            result = RESULT_WIN
        else:
            result = RESULT_LOSE

        if result == RESULT_WIN:
            self.score.player += 1
        elif result == RESULT_LOSE:
            self.score.cpu += 1
        else:
            self.score.draws += 1

        return ai_move, result

    def reset_score(self) -> None:
        self.score.reset()

    def toggle_ai_mode(self) -> bool:
        return self.ai.toggle()
