import streamlit as st
import pandas as pd
from datetime import datetime

# ============================
# RULES
# ============================
BASE = {
    "Rufspiel": 0.10,
    "Farbsolo": 0.20,
    "Geier": 0.20,
    "Wenz": 0.20,
    "Bettel": 0.20,
    "Herzsolo": 0.20,
    "Ramsch": 0.10
}

LAUF = 0.05
SOLOS = ["Farbsolo", "Geier", "Wenz", "Bettel", "Herzsolo"]

# ============================
# CROSS ENGINE (FIXED)
# ============================
def create_cross_pairs(players, solo_player):
    A, B, C, D = players[:4]

    seats = {A: 0, B: 1, C: 2, D: 3}
    s = seats.get(solo_player, 0)

    if s == 0:
        return [[A, D], [B, C]]
    elif s == 1:
        return [[B, C], [A, D]]
    elif s == 2:
        return [[C, D], [A, B]]
    else:
        return [[D, A], [B, C]]

# ============================
# CALC CROSS
# ============================
def calc_cross(players, data):
    pair1, pair2 = st.session_state.kreuz_pairs

    base = 0.10 + data.get("lauf", 0) * LAUF
    base *= (2 ** data.get("leger", 0))

    out = {}

    if data.get("winner_pair") == "Paar 1":
        win, lose = pair1, pair2
    else:
        win, lose = pair2, pair1

    for p in win:
        out[p] = base
    for p in lose:
        out[p] = -base

    return out

# ============================
# CALC NORMAL
# ============================
def calc(game, players, data):

    out = {}

    base = BASE.get(game, 0) + data.get("lauf", 0) * LAUF
    base *= (2 ** data.get("leger", 0))

    per = base

    if game == "Rufspiel":
        winners = set(data.get("winner", []))
        for p in players:
            out[p] = per if p in winners else -per

    elif game in SOLOS:
        solo = data.get("solo")
        for p in players:
            out[p] = per * (len(players) - 1) if p == solo else -per

    elif game == "Ramsch":
        loser = data.get("loser")
        for p in players:
            out[p] = per * (len(players) - 1) if p == loser else -per

    return out

# ============================
# STATE INIT
# ============================
if "state" not in st.session_state:
    st.session_state.state = "SETUP"
    st.session_state.players = []
    st.session_state.balance = {}
    st.session_state.round = 1
    st.session_state.history = []

    st.session_state.days = []
    st.session_state.last_day = None

    st.session_state.kreuz_active = False
    st.session_state.kreuz_rounds_left = 0
    st.session_state.kreuz_pairs = None
    st.session_state.kreuz_solo = None

st.title("🃏 Schafkopfrechner")

players = [p for p in st.session_state.get("players", []) if p.strip()]

# ============================
# LAST DAY
# ============================
if st.session_state.last_day:
    st.subheader("📌 Letzter Spieltag")

    st.write("💰 Endstände")
    st.dataframe(pd.DataFrame([st.session_state.last_day["balance"]]))

    st.write("📊 Spielverlauf")
    st.dataframe(pd.DataFrame(st.session_state.last_day["history"]))

# ============================
# SETUP
# ============================
if st.session_state.state == "SETUP":

    n = st.selectbox("Spieleranzahl", [4, 5])
    names = [st.text_input(f"Spieler {i+1}") for i in range(n)]

    if st.button("Start"):
        st.session_state.players = names
        st.session_state.balance = {p: 0 for p in names if p.strip()}
        st.session_state.state = "GAME"
        st.rerun()

    st.stop()

# ============================
# GAME
# ============================
if st.session_state.state == "GAME":

    st.info(f"Runde {st.session_state.round}")

    # CROSS MODE
    if st.session_state.kreuz_active:

        st.subheader("🔥 Kreuzmodus")

        pair1, pair2 = st.session_state.kreuz_pairs

        st.write("🟦", pair1)
        st.write("🟥", pair2)

        kreuz_lauf = st.number_input("Laufende", 0, 10, 0)
        kreuz_leger = st.number_input("Leger", 0, 3, 0)

        winner_pair = st.radio("Gewonnenes Paar", ["Paar 1", "Paar 2"])

        game_mode = "KREUZ"

        data = {
            "lauf": kreuz_lauf,
            "leger": kreuz_leger,
            "winner_pair": winner_pair
        }

    else:

        game_mode = st.radio("Spiel", list(BASE.keys()))
        data = {}

        if game_mode == "Rufspiel":
            data["winner"] = st.multiselect("Gewinner", players)

        elif game_mode in SOLOS:
            data["solo"] = st.selectbox("Solo", players)

        elif game_mode == "Ramsch":
            data["loser"] = st.selectbox("Verlierer", players)

        data["lauf"] = st.number_input("Laufende", 0, 10, 0)
        data["leger"] = st.number_input("Leger", 0, 3, 0)

    # ============================
    # ABRECHNUNG
    # ============================
    if st.button("💰 Abrechnen"):

        if st.session_state.kreuz_active:
            changes = calc_cross(players, data)

            st.session_state.kreuz_rounds_left -= 1

            if st.session_state.kreuz_rounds_left <= 0:
                st.session_state.kreuz_active = False
                st.session_state.kreuz_pairs = None
                st.session_state.kreuz_solo = None

        else:
            changes = calc(game_mode, players, data)

            if game_mode == "Herzsolo" and len(players) == 4:
                solo = data.get("solo", players[0])
                st.session_state.kreuz_active = True
                st.session_state.kreuz_rounds_left = 4
                st.session_state.kreuz_pairs = create_cross_pairs(players, solo)

        for p, v in changes.items():
            st.session_state.balance[p] += v

        st.session_state.history.append({
            "time": str(datetime.now()),
            "game": game_mode,
            **changes
        })

        st.session_state.round += 1
        st.rerun()

# ============================
# HISTORY
# ============================
st.subheader("📊 Historie")
if st.session_state.history:
    st.dataframe(pd.DataFrame(st.session_state.history))

# ============================
# BALANCE
# ============================
st.subheader("💰 Kontostand")
for p, v in st.session_state.balance.items():
    st.write(f"{p}: {v:.2f}")

# ============================
# UNDO
# ============================
if st.button("↩️ Undo letzte Runde"):

    if st.session_state.history:
        last = st.session_state.history.pop()

        for p in st.session_state.balance:
            st.session_state.balance[p] -= last.get(p, 0)

        st.session_state.round -= 1
        st.rerun()

# ============================
# END DAY
# ============================
if st.button("🏁 Spieltag beenden"):

    day = {
        "time": str(datetime.now()),
        "balance": st.session_state.balance.copy(),
        "history": st.session_state.history.copy()
    }

    st.session_state.days.append(day)
    st.session_state.last_day = day

    st.session_state.balance = {p: 0 for p in st.session_state.players}
    st.session_state.history = []
    st.session_state.round = 1

    st.session_state.kreuz_active = False
    st.session_state.kreuz_rounds_left = 0
    st.session_state.kreuz_pairs = None
    st.session_state.kreuz_solo = None

    st.rerun()
