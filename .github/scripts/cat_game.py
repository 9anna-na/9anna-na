#!/usr/bin/env python3
"""Tally profile votes and update Joanna's community tic-tac-toe board."""

from __future__ import annotations

import json
import random
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
STATE = ROOT / "game" / "state.json"
START = "<!-- CAT_GAME_START -->"
END = "<!-- CAT_GAME_END -->"
VOTE_API = "https://joanna-tiny-game-break.jls940519.chatgpt.site"
WINS = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)


def winner(board: list[str]) -> str | None:
    for a, b, c in WINS:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None


def best_cat_move(board: list[str]) -> int:
    empty = [i for i, mark in enumerate(board) if not mark]
    for mark in ("cat", "player"):
        for index in empty:
            trial = board.copy()
            trial[index] = mark
            if winner(trial) == mark:
                return index
    if 4 in empty:
        return 4
    corners = [i for i in (0, 2, 6, 8) if i in empty]
    return random.choice(corners or empty)


def fetch_counts() -> list[int]:
    request = Request(f"{VOTE_API}/api/votes", headers={"User-Agent": "joanna-cat-game"})
    with urlopen(request, timeout=20) as response:
        payload = json.load(response)
    counts = payload.get("counts")
    if not isinstance(counts, list) or len(counts) != 9:
        raise RuntimeError("Vote API returned an invalid board")
    return [int(value) for value in counts]


def vote_link(index: int) -> str:
    return f"{VOTE_API}/api/vote?cell={index + 1}"


def render_cell(mark: str, index: int) -> str:
    if mark == "player":
        return "🌸"
    if mark == "cat":
        return "🐾"
    return f"[▫️]({vote_link(index)})"


def render(board: list[str], message: str) -> str:
    cells = [render_cell(mark, i) for i, mark in enumerate(board)]
    return "\n".join([
        START,
        "| | | |",
        "|:---:|:---:|:---:|",
        f"| {cells[0]} | {cells[1]} | {cells[2]} |",
        f"| {cells[3]} | {cells[4]} | {cells[5]} |",
        f"| {cells[6]} | {cells[7]} | {cells[8]} |",
        "",
        f"_{message}_",
        END,
    ])


def replace_game(markdown: str, game: str) -> str:
    before, rest = markdown.split(START, 1)
    _, after = rest.split(END, 1)
    return before + game + after


def main() -> None:
    state = json.loads(STATE.read_text())
    board = state["board"]
    counts = fetch_counts()
    last_counts = state.get("last_counts", [0] * 9)

    if winner(board) or all(board):
        board = [""] * 9
        state["round"] = int(state.get("round", 0)) + 1
        message = "A fresh round is open—pick an empty square."
    else:
        deltas = [max(0, now - before) for now, before in zip(counts, last_counts)]
        candidates = [i for i, votes in enumerate(deltas) if votes and not board[i]]

        if not candidates:
            message = "Voting is open—pick an empty square."
        else:
            top_votes = max(deltas[i] for i in candidates)
            move = random.choice([i for i in candidates if deltas[i] == top_votes])
            board[move] = "player"

            if winner(board) == "player":
                message = "The community wins! The cat requests a rematch."
            elif all(board):
                message = "A very peaceful draw."
            else:
                board[best_cat_move(board)] = "cat"
                if winner(board) == "cat":
                    message = "The cat wins this round—another starts soon."
                elif all(board):
                    message = "A very peaceful draw."
                else:
                    message = "The community played 🌸 and the cat answered 🐾."

    state["board"] = board
    state["last_counts"] = counts
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    README.write_text(replace_game(README.read_text(), render(board, message)))


if __name__ == "__main__":
    main()
