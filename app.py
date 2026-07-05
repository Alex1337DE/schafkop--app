import streamlit as st
import pandas as pd
from datetime import datetime

# ============================
# KONSTANTEN
# ============================
BASE_RUF = 0.10
BASE_SOLO = 0.20
BASE_RAM = 0.10
LAUF = 0.05

SOLOS = ["Farbsolo", "Geier", "Wenz", "Bettel", "Herzsolo"]

# ============================
# STATE INIT
# ============================
if "step" not in st.session_state:
    st.session_state.step = 1
    st.session_state.players = []
    st.session_state.num = 0
    st.session_state.balance = {}
    st.session_state.round = 1
    st.session_state.dealer = 0
    st.session_state.history = []

    # 👉 NEU: letzter abgeschlossener Spieltag
    st.session_state.last_day_result = None

    # Kreuzmodus
    st.session_state.kreuz_mode = False
    st.session_state.kreuz_left = 0

    # Inputs
    st.session_state.lauf = 0
    st.session_state.leger = 0
    st.session_state.hint = ""

st.title("🃏 Schafkopf Rechner")

# ============================
# 🔥 LETZTES SPIELTAGERGEBNIS (GANZ OBEN!)
# ============================
if st.session_state.last_day_result:
    st.subheader("📌 Letzter Spieltag")
    st.dataframe(pd.DataFrame(st.session_state.last_day_result))

# ============================
# SETUP: SPIELERANZAHL
# ============================
if st.session_state.step == 1:

    n = st.selectbox("Spieleranzahl", [4, 5])

    if st.button("Weiter"):
        st.session_state.num = n
        st.session_state.step = 2
        st.rerun()

    st.stop()

# ============================
# SETUP: NAMEN
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
def reset_inputs():
    st.session_state.lauf = 0
    st.session_state.leger = 0
    st.session_state.hint = ""

players = st.session_state.players

st.info(f"Runde: {st.session_state.round}")

# ============================
# KREUZSPIEL (fixe Paare)
# ============================
if st.session_state.kreuz_mode:

    st.subheader("🔥 Kreuzspiel")

    pair1 = players[:2]
    pair2 = players[2:4]

    st.write(f"🟦 Paar 1: {pair1}")
    st.write(f"🟥 Paar 2: {pair2}")

    kreuz_lauf = st.number_input("Laufende", 0, 10, 0)
    kreuz_leger = st.number_input("Leger", 0, 3, 0)
    kreuz_schneider = st.checkbox("Schneider")
    kreuz_schwarz = st.checkbox("Schwarz")

    winner_pair = st.radio("Gewonnenes Paar", ["Paar 1", "Paar 2"])

    game = "KREUZ"

# ============================
# NORMALE SPIELE
# ============================
else:

    games = ["Rufspiel", "Farbsolo", "Geier", "Wenz", "Bettel", "Herzsolo", "Ramsch"]

    cols = st.columns(4)
    selected = []

    for i, g in enumerate(games):
        if cols[i % 4].checkbox(g):
            selected.append(g)

    game = selected[0] if selected else None

    result = st.radio("Ergebnis", ["Gewonnen", "Verloren"], horizontal=True)

    if game == "Rufspiel":
        winner = st.multiselect("Gewinner", players)

    elif game in SOLOS:
        solo = st.selectbox("Solo Spieler", players)

    st.session_state.lauf = st.number_input("Laufende", 0, 10, 0)
    st.session_state.leger = st.number_input("Leger", 0, 3, 0)
    st.session_state.hint = st.text_input("Hinweis")

# ============================
# ABRECHNUNG
# ============================
if st.button("💰 Abrechnen") and game:

    row = {
        "Nr": st.session_state.round,
        "Zeit": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "Spiel": game,
        "Hinweis": st.session_state.hint
    }

    for p in players:
        row[p] = 0.0

    # ============================
    # KREUZSPIEL
    # ============================
    if st.session_state.kreuz_mode:

        BASE = 0.10

        b = BASE + kreuz_lauf * LAUF

        if kreuz_schneider:
            b += 0.10
        if kreuz_schwarz:
            b += 0.10

        pot = b * len(players) * (2 ** kreuz_leger)
        per = pot / len(players)

        if winner_pair == "Paar 1":
            win, lose = pair1, pair2
        else:
            win, lose = pair2, pair1

        for p in win:
            row[p] = per
            st.session_state.balance[p] += per

        for p in lose:
            row[p] = -per
            st.session_state.balance[p] -= per

        st.session_state.kreuz_left -= 1

        if st.session_state.kreuz_left <= 0:
            st.session_state.kreuz_mode = False
            reset_inputs()

    # ============================
    # NORMALE SPIELE
    # ============================
    else:

        def base(g):
            if g == "Rufspiel":
                return BASE_RUF
            if g in SOLOS:
                return BASE_SOLO
            return BASE_RAM

        factor = 1 if result == "Gewonnen" else -1

        b = base(game) + st.session_state.lauf * LAUF
        pot = b * len(players) * (2 ** st.session_state.leger)
        per = pot / len(players)

        for p in players:
            row[p] = per * factor if p in (winner if game == "Rufspiel" else [solo]) else -per * factor
            st.session_state.balance[p] += row[p]

        if game == "Herzsolo" and len(players) == 4:
            st.session_state.kreuz_mode = True
            st.session_state.kreuz_left = 4

        reset_inputs()

    st.session_state.history.append(row)
    st.session_state.round += 1

    st.rerun()

# ============================
# HISTORIE
# ============================
st.subheader("📊 Historie")

if st.session_state.history:
    # ============================
# 📌 LETZTER SPIELTAG
# ============================
if st.session_state.last_day_result:

    st.subheader("📌 Letzter Spieltag")

    df_last = pd.DataFrame(
        list(st.session_state.last_day_result.items()),
        columns=["Spieler", "Ergebnis"]
    )

    st.dataframe(df_last, use_container_width=True)

# ============================
# 📊 HISTORIE
# ============================
st.subheader("📊 Historie")

if st.session_state.history:
    st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)

# ============================
# KONTO
# ============================
st.subheader("💰 Kontostand")

for p, v in st.session_state.balance.items():
    st.write(f"{p}: {v:.2f} €")

# ============================
# ENDE SPIELTAG
# ============================
if st.button("🏁 Spieltag beenden"):

    st.session_state.last_day_result = st.session_state.balance.copy()

    st.session_state.history = []
    st.session_state.round = 1

    st.rerun()

# ============================
# UNDO
# ============================
if st.button("↩️ Undo"):

    if st.session_state.history:
        last = st.session_state.history.pop()

        for p in players:
            st.session_state.balance[p] -= last.get(p, 0)

        st.session_state.round -= 1

        st.rerun()
