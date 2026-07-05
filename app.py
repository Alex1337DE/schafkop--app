import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime

# ============================
# DB LAYER
# ============================
def conn():
    return sqlite3.connect("schafkopf_pro.db", check_same_thread=False)

def init_db():
    c = conn().cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS days (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        results TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS rounds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day_id INTEGER,
        time TEXT,
        game TEXT,
        data TEXT
    )
    """)

    conn().commit()

init_db()

def save_day(results):
    c = conn().cursor()
    c.execute(
        "INSERT INTO days (date, results) VALUES (?, ?)",
        (datetime.now().strftime("%d.%m.%Y %H:%M"), json.dumps(results))
    )
    conn().commit()

def load_last_day():
    c = conn().cursor()
    c.execute("SELECT date, results FROM days ORDER BY id DESC LIMIT 1")
    return c.fetchone()

def save_round(day_id, game, data):
    c = conn().cursor()
    c.execute(
        "INSERT INTO rounds (day_id, time, game, data) VALUES (?, ?, ?, ?)",
        (day_id, datetime.now().strftime("%H:%M"), game, json.dumps(data))
    )
    conn().commit()

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
# STATE
# ============================
if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.players = []
    st.session_state.balance = {}
    st.session_state.round = 1
    st.session_state.history = []
    st.session_state.kreuz_mode = False
    st.session_state.kreuz_left = 0
    st.session_state.undo_stack = []

st.title("🃏 Schafkopf PRO")

# ============================
# LAST DAY
# ============================
st.subheader("📌 Letzter Spieltag")

last = load_last_day()
if last:
    st.dataframe(pd.DataFrame(json.loads(last[1]).items(), columns=["Spieler", "Ergebnis"]))
else:
    st.info("Noch kein Spieltag")

st.markdown("---")

# ============================
# SETUP
# ============================
if st.session_state.step == 1:

    n = st.selectbox("Spieleranzahl", [4, 5])

    if st.button("Weiter"):
        st.session_state.num = n
        st.session_state.step = 2
        st.rerun()

    st.stop()

if st.session_state.step == 2:

    names = [st.text_input(f"Spieler {i+1}") for i in range(st.session_state.num)]

    if st.button("Start"):
        st.session_state.players = names
        st.session_state.balance = {p: 0 for p in names}
        st.session_state.step = 3
        st.rerun()

    st.stop()

players = st.session_state.players

st.info(f"Runde {st.session_state.round}")

# ============================
# GAME SELECT
# ============================
game = st.radio("Spiel", list(BASE.keys()))

result = st.radio("Ergebnis", ["Gewonnen", "Verloren"], horizontal=True)

winner = []
solo = None
loser = None

if game == "Rufspiel":
    winner = st.multiselect("Gewinner", players)

elif game in SOLOS:
    solo = st.selectbox("Solo Spieler", players)

elif game == "Ramsch":
    loser = st.selectbox("Verlierer", players)

lauf = st.number_input("Laufende", 0, 10, 0)
leger = st.number_input("Leger", 0, 3, 0)

# ============================
# CALC ENGINE
# ============================
def calc(game, players, result, winner, solo, loser, lauf, leger):
    factor = 1 if result == "Gewonnen" else -1

    base = BASE[game] + lauf * LAUF
    base *= (2 ** leger)

    per = base

    out = {}

    if game == "Rufspiel":
        for p in players:
            out[p] = per * factor if p in winner else -per * factor

    elif game in SOLOS:
        for p in players:
            out[p] = per * factor * (len(players)-1) if p == solo else -per * factor

    elif game == "Ramsch":
        for p in players:
            out[p] = per * (len(players)-1) if p == loser else -per

    return out

# ============================
# RUN GAME
# ============================
if st.button("💰 Abrechnen"):

    changes = calc(game, players, result, winner, solo, loser, lauf, leger)

    row = {"time": str(datetime.now()), "game": game, **changes}

    st.session_state.undo_stack.append(dict(st.session_state.balance))

    for p, v in changes.items():
        st.session_state.balance[p] += v

    st.session_state.history.append(row)

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
if st.button("↩️ Undo") and st.session_state.undo_stack:

    st.session_state.balance = st.session_state.undo_stack.pop()
    st.session_state.history.pop()
    st.session_state.round -= 1

    st.rerun()

# ============================
# END DAY
# ============================
if st.button("🏁 Spieltag beenden"):

    save_day(st.session_state.balance)

    st.session_state.balance = {p: 0 for p in players}
    st.session_state.history = []
    st.session_state.undo_stack = []
    st.session_state.round = 1

    st.session_state.step = 1

    st.rerun()
