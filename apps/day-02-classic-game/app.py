from __future__ import annotations

import streamlit as st

WIN_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


def init_state() -> None:
    st.session_state.setdefault("board", [""] * 9)
    st.session_state.setdefault("current_player", "X")
    st.session_state.setdefault("winner", "")
    st.session_state.setdefault("is_draw", False)


def check_winner(board: list[str]) -> str:
    for a, b, c in WIN_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return ""


def play(index: int) -> None:
    if st.session_state.winner or st.session_state.is_draw:
        return

    board = st.session_state.board
    if board[index]:
        return

    board[index] = st.session_state.current_player
    winner = check_winner(board)
    if winner:
        st.session_state.winner = winner
        return

    if all(cell for cell in board):
        st.session_state.is_draw = True
        return

    st.session_state.current_player = "O" if st.session_state.current_player == "X" else "X"


def reset_game() -> None:
    st.session_state.board = [""] * 9
    st.session_state.current_player = "X"
    st.session_state.winner = ""
    st.session_state.is_draw = False


st.set_page_config(page_title="Day 02 - Tic-Tac-Toe", page_icon="🎮")
init_state()

st.title("Day 02 - Tic-Tac-Toe")
st.caption("Minimal classic game built with Streamlit.")

if st.session_state.winner:
    st.success(f"Player {st.session_state.winner} wins.")
elif st.session_state.is_draw:
    st.info("Draw game.")
else:
    st.write(f"Current player: **{st.session_state.current_player}**")

for row in range(3):
    cols = st.columns(3)
    for col in range(3):
        index = row * 3 + col
        label = st.session_state.board[index] or " "
        cols[col].button(
            label,
            key=f"cell_{index}",
            use_container_width=True,
            on_click=play,
            args=(index,),
            disabled=bool(st.session_state.board[index] or st.session_state.winner or st.session_state.is_draw),
        )

st.button("New game", on_click=reset_game)
