import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ============================
# DB SETUP
# ============================
conn = sqlite3.connect("schafkopf.db", check_same_thread=False)
c = conn.cursor()

# ----------------------------
# STATE INIT
# ----------------------------
if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.players = []
    st.session_state.num = 0
    st.session_state.balance = {}
    st.session_state.round = 1
    st.session_state.dealer = 0

    st.session_state.kreuz_mode = False
    st.session_state.kreuz_left = 0

    # inputs
    st.session_state.game = None
    st.session_state.winner = []
    st.session_state.solo = None
    st.session_state.schneider = False
    st.session_state.schwarz = False
    st.session_state.lauf = 0
    st.session_state.leger = 0
    st.session_state.hint = ""

st.title("🃏 Schafkopf App")

# ============================
# STEP 1: PLAYERS
# ============================
if st.session_state.step == 1:

    n = st.selectbox("4 oder 5 Spieler", [4, 5])

    if st.button("Weiter"):
        st.session_state.num = n
        st.session_state.step = 2
        st.rerun()

    st.stop()

# ============================
# STEP 2: NAMEN
# ============================
if st.session_state.step == 2:

    names = []
    for i in range(st.session_state.num):
        names.append(st.text_input(f"Spieler {i+1}", f"Spieler {i+1}"))

    if st.button("Start"):
        st.session_state.players = names
        st.session_state.balance = {p: 0 for p in names}
        st.session_state.step = 3
        st.rerun()

    st.stop()

# ============================
# HELPERS
# ============================
def active_players():
    if len(st.session_state.players) == 5:
        pause = st.session_state.players[st.session_state.dealer % 5]
        return [p for p in st.session_state.players if p != pause], pause
    return st.session_state.players, None


def reset_inputs():
    st.session_state.game = None
    st.session_state.winner = []
    st.session_state.solo = None
    st.session_state.schneider = False
    st.session_state.schwarz = False
    st.session_state.lauf = 0
    st.session_state.leger = 0
    st.session_state.hint = ""

# ============================
# DB CREATE (DYNAMIC)
# ============================
def ensure_table():
    cols = ["id INTEGER PRIMARY KEY AUTOINCREMENT",
            "round_nr INTEGER",
            "date TEXT",
            "game TEXT",
            "leger INTEGER",
            "hint TEXT"]

    for p in st.session_state.players:
        cols.append(f'"{p}" REAL')

    c.execute(f"CREATE TABLE IF NOT EXISTS games ({', '.join(cols)})")
    conn.commit()

ensure_table()

# ============================
# UI HEADER
# ============================
players, pause = active_players()

st.info(f"Runde: {st.session_state.round}")
if pause:
    st.warning(f"Pause: {pause}")

if st.session_state.kreuz_mode:
    st.error(f"🔥 Kreuzrunde aktiv ({st.session_state.kreuz_left}/4)")

# ============================
# GAME INPUTS (CHECKBOX STYLE)
# ============================
games = ["Rufspiel", "Farbsolo", "Geier", "Wenz", "Bettel", "Herzsolo", "Ramsch"]

cols = st.columns(4)
selected = []

for i, g in enumerate(games):
    if cols[i % 4].checkbox(g):
        selected.append(g)

game = selected[0] if selected else None
st.session_state.game = game

result = st.radio("Spielausgang", ["Gewonnen", "Verloren"], horizontal=True)

winner = []
solo = None

if game == "Rufspiel":
    winner = st.multiselect("Gewinner (2)", players)

elif game in ["Farbsolo", "Geier", "Wenz", "Bettel", "Herzsolo"]:
    solo = st.selectbox("Solo Spieler", players)

st.session_state.winner = winner
st.session_state.solo = solo

st.session_state.schneider = st.checkbox("Schneider")
st.session_state.schwarz = st.checkbox("Schwarz")
st.session_state.lauf = st.number_input("Laufende", 0, 10, 0)
st.session_state.leger = st.number_input("Leger", 0, 3, 0)
st.session_state.hint = st.text_input("Hinweis")

# ============================
# CALC HELPERS
# ============================
BASE = {"Rufspiel": 0.10, "Ramsch": 0.10}
SOLOS = ["Farbsolo", "Geier", "Wenz", "Bettel", "Herzsolo"]

def base(game):
    if game in SOLOS:
        return 0.20
    return BASE.get(game, 0.10)

def save(row):
    cols = ",".join(row.keys())
    vals = list(row.values())
    q = ",".join(["?"] * len(vals))
    c.execute(f"INSERT INTO games ({cols}) VALUES ({q})", vals)
    conn.commit()

# ============================
# ABBRECHNUNG
# ============================
if st.button("💰 Abrechnen") and game:

    factor = 1 if result == "Gewonnen" else -1

    b = base(game)
    if st.session_state.schneider:
        b += 0.10
    if st.session_state.schwarz:
        b += 0.10

    b += st.session_state.lauf * 0.05

    pot = b * len(players) * (2 ** st.session_state.leger)
    per = pot / len(players)

    row = {
        "round_nr": st.session_state.round,
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "game": game,
        "leger": st.session_state.leger,
        "hint": st.session_state.hint + (" | VERLOREN" if factor == -1 else "")
    }

    for p in st.session_state.players:
        row[p] = 0.0

    # -------------------------
    # RUF
    # -------------------------
    if game == "Rufspiel":
        for p in players:
            if p in winner:
                v = per * factor
            else:
                v = -per * factor
            st.session_state.balance[p] += v
            row[p] = v

    # -------------------------
    # SOLO
    # -------------------------
    elif game in SOLOS:
        for p in players:
            if p == solo:
                v = per * (len(players)-1) * factor
            else:
                v = -per * factor
            st.session_state.balance[p] += v
            row[p] = v

        if game == "Herzsolo" and len(players) == 4:
            st.session_state.kreuz_mode = True
            st.session_state.kreuz_left = 4

    # -------------------------
    # RAMSCH
    # -------------------------
    elif game == "Ramsch":
        for p in players:
            v = -per
            st.session_state.balance[p] += v
            row[p] = v

    # -------------------------
    # KREUZ LOGIK
    # -------------------------
    if st.session_state.kreuz_mode:
        row["hint"] += " | KREUZ"
        st.session_state.kreuz_left -= 1
        if st.session_state.kreuz_left <= 0:
            st.session_state.kreuz_mode = False

    save(row)

    st.session_state.round += 1
    st.session_state.dealer += 1

    # ============================
    # RESET (WICHTIG)
    # ============================
    if not st.session_state.kreuz_mode:
        reset_inputs()

    st.rerun()

# ============================
# HISTORY
# ============================
st.subheader("📊 Historie")

df = pd.read_sql("SELECT * FROM games", conn)
st.dataframe(df, use_container_width=True)

# ============================
# BALANCE
# ============================
st.subheader("💰 Kontostand")

for p, v in st.session_state.balance.items():
    st.write(f"{p}: {v:.2f} €")

# ============================
# UNDO
# ============================
if st.button("↩️ Undo letzte Runde"):

    c.execute("DELETE FROM games ORDER BY id DESC LIMIT 1")
    conn.commit()

    st.session_state.round = max(1, st.session_state.round - 1)

    st.warning("Letzte Runde gelöscht")
    st.rerun()

# ============================
# END GAME
# ============================
if st.button("🏁 Spieltag beenden"):

    st.success("Spieltag beendet")

    st.download_button(
        "📥 Export CSV",
        data=df.to_csv(index=False),
        file_name="schafkopf.csv"
    )
