import streamlit as st
import pandas as pd
from datetime import datetime

# ----------------------------
# KONSTANTEN
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
    st.session_state.num = 0
    st.session_state.balance = {}
    st.session_state.round = 1
    st.session_state.dealer = 0

    st.session_state.history = []

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

st.title("🃏 Schafkopf Rechner (Simple Mode)")

# ----------------------------
# STEP 1
# ----------------------------
if st.session_state.step == 1:

    n = st.selectbox("4 oder 5 Spieler", [4, 5])

    if st.button("Weiter"):
        st.session_state.num = n
        st.session_state.step = 2
        st.rerun()

    st.stop()

# ----------------------------
# STEP 2
# ----------------------------
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

# ----------------------------
# HELPERS
# ----------------------------
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

# ----------------------------
# UI HEADER
# ----------------------------
players, pause = active_players()

st.info(f"Runde: {st.session_state.round}")
if pause:
    st.warning(f"Pause-Spieler: {pause}")

if st.session_state.kreuz_mode:
    st.error(f"🔥 Kreuzrunde aktiv ({st.session_state.kreuz_left}/4)")

# ----------------------------
# SPIELE
# ----------------------------
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

elif game in SOLOS:
    solo = st.selectbox("Solo Spieler", players)

st.session_state.winner = winner
st.session_state.solo = solo

st.session_state.schneider = st.checkbox("Schneider")
st.session_state.schwarz = st.checkbox("Schwarz")
st.session_state.lauf = st.number_input("Laufende", 0, 10, 0)
st.session_state.leger = st.number_input("Leger", 0, 3, 0)
st.session_state.hint = st.text_input("Hinweis")

# ----------------------------
# CALC
# ----------------------------
def base(g):
    if g == "Rufspiel":
        return BASE_RUF
    if g in SOLOS:
        return BASE_SOLO
    return BASE_RAM

# ----------------------------
# ABRECHNUNG
# ----------------------------
if st.button("💰 Abrechnen") and game:

    factor = 1 if result == "Gewonnen" else -1

    b = base(game)

    if st.session_state.schneider:
        b += 0.10
    if st.session_state.schwarz:
        b += 0.10

    b += st.session_state.lauf * LAUF

    pot = b * len(players) * (2 ** st.session_state.leger)
    per = pot / len(players)

    row = {
        "Nr": st.session_state.round,
        "Datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "Spiel": game,
        "Leger": st.session_state.leger,
        "Hinweis": st.session_state.hint
    }

    for p in st.session_state.players:
        row[p] = 0.0

    # Ruf
    if game == "Rufspiel":
        for p in players:
            if p in winner:
                v = per * factor
            else:
                v = -per * factor
            st.session_state.balance[p] += v
            row[p] = v

    # Solo
    elif game in SOLOS:
        for p in players:
            if p == solo:
                v = per * (len(players)-1) * factor
            else:
                v = -per * factor
            st.session_state.balance[p] += v
            row[p] = v

    # Ramsch
    elif game == "Ramsch":
        for p in players:
            v = -per
            st.session_state.balance[p] += v
            row[p] = v

    # Kreuzregel
    if st.session_state.kreuz_mode:
        row["Hinweis"] += " | KREUZ"
        st.session_state.kreuz_left -= 1
        if st.session_state.kreuz_left <= 0:
            st.session_state.kreuz_mode = False

    st.session_state.history.append(row)

    st.session_state.round += 1
    st.session_state.dealer += 1

    # RESET NUR WENN KEIN KREUZ
    if not st.session_state.kreuz_mode:
        reset_inputs()

    st.rerun()

# ----------------------------
# HISTORIE
# ----------------------------
st.subheader("📊 Historie")

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df, use_container_width=True)

# ----------------------------
# KONTO
# ----------------------------
st.subheader("💰 Kontostand")

for p, v in st.session_state.balance.items():
    st.write(f"{p}: {v:.2f} €")

# ----------------------------
# UNDO
# ----------------------------
if st.button("↩️ Undo letzte Runde"):

    if st.session_state.history:
        last = st.session_state.history.pop()

        for p in st.session_state.players:
            st.session_state.balance[p] -= last.get(p, 0)

        st.session_state.round = max(1, st.session_state.round - 1)

        st.warning("Letzte Runde entfernt")
        st.rerun()

# ----------------------------
# END GAME
# ----------------------------
if st.button("🏁 Spieltag beenden"):

    st.download_button(
        "📥 CSV Export",
        data=pd.DataFrame(st.session_state.history).to_csv(index=False),
        file_name="schafkopf.csv"
    )

    st.success("Spieltag beendet")
