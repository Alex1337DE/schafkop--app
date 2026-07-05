import streamlit as st
import pandas as pd
from datetime import datetime

# ============================
# RULES / ENGINE CONFIG
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
# ENGINE (MUSS VOR DER NUTZUNG STEHEN)
# ============================
def calc(game, players, data):

    base = BASE[game] + data.get("lauf", 0) * LAUF
    base *= (2 ** data.get("leger", 0))
    per = base

    out = {}

    # ----------------------------
    # RUF
    # ----------------------------
    if game == "Rufspiel":

        for p in players:
            out[p] = per if p in data.get("winner", []) else -per

    # ----------------------------
    # SOLO
    # ----------------------------
    elif game in SOLOS:

        for p in players:
            out[p] = per * (len(players) - 1) if p == data.get("solo") else -per

    # ----------------------------
    # RAMSCH
    # ----------------------------
    elif game == "Ramsch":

        for p in players:
            out[p] = per * (len(players) - 1) if p == data.get("loser") else -per

    # ----------------------------
    # KREUZ
    # ----------------------------
    elif game == "KREUZ":

        pair1, pair2 = st.session_state.kreuz_pairs

        if data["winner_pair"] == "Paar 1":
            win, lose = pair1, pair2
        else:
            win, lose = pair2, pair1

        for p in win:
            out[p] = per

        for p in lose:
            out[p] = -per

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

    # Kreuz-State
    st.session_state.kreuz_active = False
    st.session_state.kreuz_round = 0
    st.session_state.kreuz_pairs = None

st.title("🧠 Schafkopf STATE ENGINE")

players = st.session_state.players

# ============================
# SETUP STATE
# ============================
if st.session_state.state == "SETUP":

    n = st.selectbox("Spieleranzahl", [4, 5])

    names = [st.text_input(f"Spieler {i+1}") for i in range(n)]

    if st.button("Start"):

        st.session_state.players = names
        st.session_state.balance = {p: 0 for p in names}

        st.session_state.state = "GAME"
        st.rerun()

    st.stop()

# ============================
# GAME STATE
# ============================
if st.session_state.state == "GAME":

    st.info(f"Runde {st.session_state.round}")

    # ============================
    # KREUZ MODE
    # ============================
    if st.session_state.kreuz_active:

        st.subheader("🔥 Kreuzrunde aktiv")

        pair1, pair2 = st.session_state.kreuz_pairs

        st.write(f"🟦 Paar 1: {pair1}")
        st.write(f"🟥 Paar 2: {pair2}")

        kreuz_lauf = st.number_input("Laufende", 0, 10, 0)
        kreuz_leger = st.number_input("Leger", 0, 3, 0)

        winner_pair = st.radio("Gewonnenes Paar", ["Paar 1", "Paar 2"])

        game = "KREUZ"

        data = {
            "lauf": kreuz_lauf,
            "leger": kreuz_leger,
            "winner_pair": winner_pair
        }

    # ============================
    # NORMAL GAME
    # ============================
    else:

        game = st.radio("Spiel", list(BASE.keys()))

        data = {}

        if game == "Rufspiel":
            data["winner"] = st.multiselect("Gewinner", players)

        elif game in SOLOS:
            data["solo"] = st.selectbox("Solo Spieler", players)

        elif game == "Ramsch":
            data["loser"] = st.selectbox("Verlierer", players)

        data["result"] = st.radio("Ergebnis", ["Gewonnen", "Verloren"], horizontal=True)

        data["lauf"] = st.number_input("Laufende", 0, 10, 0)
        data["leger"] = st.number_input("Leger", 0, 3, 0)

    # ============================
    # ABRECHNUNG
    # ============================
    if st.button("💰 Abrechnen"):

        changes = calc(game, players, data)

        for p, v in changes.items():
            st.session_state.balance[p] += v

        st.session_state.history.append({
            "time": str(datetime.now()),
            "game": game,
            **changes
        })

        # ============================
        # HERZSOLO → KREUZ START
        # ============================
        if game == "Herzsolo" and len(players) == 4:
            st.session_state.kreuz_active = True
            st.session_state.kreuz_round = 4
            st.session_state.kreuz_pairs = [
                players[:2],
                players[2:4]
            ]

        # ============================
        # KREUZ COUNTDOWN
        # ============================
        elif game == "KREUZ":
            st.session_state.kreuz_round -= 1

            if st.session_state.kreuz_round <= 0:
                st.session_state.kreuz_active = False
                st.session_state.kreuz_pairs = None

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
