#!/usr/bin/env python3
"""Update Joanna's tiny profile tic-tac-toe game from a GitHub Issue."""

from __future__ import annotations

import json
import os
import random
import re
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
STATE = ROOT / "game" / "state.json"
START = "<!-- CAT_GAME_START -->"
END = "<!-- CAT_GAME_END -->"
REPO_URL = "https://github.com/9anna-na/9anna-na"
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
        for i in empty:
            trial = board.copy()
            trial[i] = mark
            if winner(trial) == mark:
                return i
    if 4 in empty:
        return 4
    corners = [i for i in (0, 2, 6, 8) if i in empty]
    if corners:
        return random.choice(corners)
    return random.choice(empty)


def move_link(index: int) -> str:
    title = quote(f"[cat-game] move {index + 1}")
    body = quote(f"Click Create to place your flower in square {index + 1}. 🌸")
    return f"{REPO_URL}/issues/new?title={title}&body={body}"


def render_cell(mark: str, index: int) -> str:
    if mark == "player":
        return "🌸"
    if mark == "cat":
        return "🐾"
    return f"[▫️]({move_link(index)})"


def render(board: list[str], message: str) -> str:
    cells = [render_cell(mark, i) for i, mark in enumerate(board)]
    reset_title = quote("[cat-game] new round")
    reset_body = quote("Click Create to reset the board. 🐱")
    reset_url = f"{REPO_URL}/issues/new?title={reset_title}&body={reset_body}"
    lines = [
        START,
        "| | | |",
        "|:---:|:---:|:---:|",
        f"| {cells[0]} | {cells[1]} | {cells[2]} |",
        f"| {cells[3]} | {cells[4]} | {cells[5]} |",
        f"| {cells[6]} | {cells[7]} | {cells[8]} |",
        "",
        f"_{message}_ · [start a new round]({reset_url})",
        END,
    ]
    return "\n".join(lines)


def replace_game(markdown: str, game: str) -> str:
    before, rest = markdown.split(START, 1)
    _, after = rest.split(END, 1)
    return before + game + after


def main() -> None:
    title = os.environ.get("GAME_ISSUE_TITLE", "").strip()
    state = json.loads(STATE.read_text())
    board = state["board"]
    if title == "[cat-game] new round":
        board = [""] * 9
        state["round"] = int(state.get("round", 0)) + 1
        message = "Your turn — pick a square!"
    else:
        match = re.fullmatch(r"\[cat-game\] move ([1-9])", title)
        if not match:
            raise SystemExit("Not a cat-game command")
        move = int(match.group(1)) - 1
        if board[move]:
            raise SystemExit("That square is already occupied")
        if winner(board) or all(board):
            raise SystemExit("This round is over; start a new round")
        board[move] = "player"
        if winner(board) == "player":
            message = "You won! The cat demands a rematch 😼"
        elif all(board):
            message = "A very peaceful draw 🌷"
        else:
            board[best_cat_move(board)] = "cat"
            if winner(board) == "cat":
                message = "The cat wins this round 🐱"
            elif all(board):
                message = "A very peaceful draw 🌷"
            else:
                message = "Your turn — the cat has made its move!"
    state["board"] = board
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    README.write_text(replace_game(README.read_text(), render(board, message)))


if __name__ == "__main__":
    main()
