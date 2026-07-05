import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ----------------------------
# DB SETUP
# ----------------------------
conn = sqlite3.connect("schafkopf.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_nr INTEGER,
    date TEXT,
    game TEXT,
    data TEXT
)
""")
conn.commit()

# ----------------------------
# CONSTANTS
# ----------------------------
BASE_RUF = 0.10
BASE_SOLO = 0.20
BASE_RAM = 0.10
LAUF = 0.05

SOLOS = ["Farbsolo", "Geier", "Wenz", "Bettel", "Herzsolo"]

# ----------------------------
# STATE
# ----------------------------
if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.players = []
    st.session_state.balance = {}
    st.session_state.round = 1
    st.session_state.dealer = 0
    st.session_state.last_row = None

st.set_page_config(page_title="Schafkopf Poker App", layout="wide")

# ----------------------------
# UI STYLE (Poker-Look simpel)
# ----------------------------
st.markdown("""
<style>
.block {padding:15px; border-radius:15px; background:#111; color:white;}
.big {font-size:20px; font-weight:bold;}
</style>
""", unsafe_allow_html=True)

st.title("🃏 Schafkopf Poker App")

# ============================================================
# SETUP
# ============================================================
if st.session_state.step == 1:

    st.subheader("👥 Spieleranzahl")

    num = st.selectbox("4 oder 5 Spieler", [4, 5])

    if st.button("Weiter"):
        st.session_state.num = num
        st.session_state.step = 2
        st.rerun()

    st.stop()

if st.session_state.step == 2:

    st.subheader("✏️ Namen")

    names = []
    for i in range(st.session_state.num):
        names.append(st.text_input(f"Spieler {i+1}", f"Spieler {i+1}"))

    if st.button("Start"):
        st.session_state.players = names
        st.session_state.balance = {p: 0 for p in names}
        st.session_state.step = 3
        st.rerun()

    st.stop()

# ============================================================
# ACTIVE PLAYERS
# ============================================================
def active_players():
    if len(st.session_state.players) == 5:
        pause = st.session_state.players[st.session_state.dealer % 5]
        return [p for p in st.session_state.players if p != pause], pause
    return st.session_state.players, None

players, pause = active_players()

# ============================================================
# HEADER CARD
# ============================================================
st.markdown(f"""
<div class="block">
<div class="big">Runde {st.session_state.round}</div>
Pause: {pause if pause else "-"} <br>
Datum: {datetime.now().strftime("%d.%m.%Y %H:%M")}
</div>
""", unsafe_allow_html=True)

# ============================================================
# SPIELAUSWAHL (CHECKBOX STYLE)
# ============================================================
st.subheader("🎮 Spiel auswählen")

cols = st.columns(4)

game_states = {}

all_games = ["Rufspiel"] + SOLOS + ["Ramsch"]

for i, g in enumerate(all_games):
    game_states[g] = cols[i % 4].checkbox(g)

selected_game = [g for g, v in game_states.items() if v]

game = selected_game[0] if selected_game else None

# ============================================================
# INPUTS
# ============================================================
result = st.radio("Spielausgang", ["Gewonnen", "Verloren"], horizontal=True)

winner = []
solo = None

if game == "Rufspiel":
    winner = st.multiselect("Gewinner (2)", players)

elif game in SOLOS:
    solo = st.selectbox("Solo Spieler", players)

schneider = st.checkbox("Schneider")
schwarz = st.checkbox("Schwarz")
lauf = st.number_input("Laufende", 0, 10, 0)
leger = st.number_input("Leger", 0, 3, 0)
hint = st.text_input("Hinweis")

# ============================================================
# HELPERS
# ============================================================
def base(g):
    if g == "Rufspiel":
        return BASE_RUF
    if g in SOLOS:
        return BASE_SOLO
    return BASE_RAM

def save_db(row):
    c.execute(
        "INSERT INTO games (round_nr, date, game, data) VALUES (?, ?, ?, ?)",
        (
            st.session_state.round,
            datetime.now().isoformat(),
            game,
            str(row)
        )
    )
    conn.commit()

def load_db():
    df = pd.read_sql("SELECT * FROM games", conn)
    return df

def delete_last():
    c.execute("DELETE FROM games ORDER BY id DESC LIMIT 1")
    conn.commit()

# ============================================================
# ABBRECHNUNG
# ============================================================
if st.button("💰 Abrechnen") and game:

    factor = 1 if result == "Gewonnen" else -1

    b = base(game)
    if schneider:
        b += 0.10
    if schwarz:
        b += 0.10
    b += lauf * LAUF

    pot = b * len(players) * (2 ** leger)
    per = pot / len(players)

    row = {
        "round": st.session_state.round,
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "game": game,
        "leger": leger,
        "hint": hint
    }

    for p in st.session_state.players:
        row[p] = 0

    if game == "Rufspiel":
        for p in players:
            if p in winner:
                val = per * factor
            else:
                val = -per * factor

            st.session_state.balance[p] += val
            row[p] = val

    elif game in SOLOS:
        for p in players:
            if p == solo:
                val = per * (len(players)-1) * factor
            else:
                val = -per * factor

            st.session_state.balance[p] += val
            row[p] = val

    elif game == "Ramsch":
        for p in players:
            val = -per
            st.session_state.balance[p] += val
            row[p] = val

    st.session_state.last_row = row
    save_db(row)

    st.session_state.round += 1
    st.session_state.dealer += 1

    st.success("Abgerechnet!")
    st.rerun()

# ============================================================
# HISTORY (DB)
# ============================================================
st.subheader("📊 Historie (DB)")

df = load_db()
st.dataframe(df)

# ============================================================
# BALANCE
# ============================================================
st.subheader("💰 Kontostand")

for p, v in st.session_state.balance.items():
    st.write(f"{p}: {v:.2f} €")

# ============================================================
# UNDO
# ============================================================
if st.button("↩️ Undo letzte Runde"):

    delete_last()

    if st.session_state.last_row:
        for p in st.session_state.players:
            st.session_state.balance[p] -= st.session_state.last_row.get(p, 0)

    st.session_state.round = max(1, st.session_state.round - 1)

    st.warning("Letzte Runde gelöscht")
    st.rerun()

# ============================================================
# END GAME
# ============================================================
if st.button("🏁 Spieltag beenden"):

    st.success("Spieltag beendet")

    st.download_button(
        "📥 Export DB",
        data=load_db().to_csv(index=False),
        file_name="schafkopf_db.csv"
    )
