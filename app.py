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

    st.session_state.kreuz_mode = False
    st.session_state.kreuz_left = 0

    st.session_state.schneider = False
    st.session_state.schwarz = False
    st.session_state.lauf = 0
    st.session_state.leger = 0
    st.session_state.hint = ""

st.title("🃏 Schafkopf Rechner")

# ============================
# LETZTES SPIEL ANZEIGEN
# ============================
if st.session_state.history:
    last = st.session_state.history[-1]
    st.subheader("📌 Letztes Spiel")
    st.write(last)

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
    st.session_state.schneider = False
    st.session_state.schwarz = False
    st.session_state.lauf = 0
    st.session_state.leger = 0
    st.session_state.hint = ""

# ============================
# UI HEADER
# ============================
players = st.session_state.players

st.info(f"Runde: {st.session_state.round}")

if st.session_state.kreuz_mode:
    st.error(f"🔥 KREUZMODUS aktiv ({st.session_state.kreuz_left}/4)")

# ============================
# SPIEL
# ============================
game = None
winner = []
solo = None

# ============================
# KREUZSPIEL (FIXE PAARE)
# ============================
if st.session_state.kreuz_mode:

    st.subheader("🔥 Kreuzspiel")

    pair1 = [players[0], players[2]]  # 1 + 3
    pair2 = [players[1], players[3]]  # 2 + 4

    st.write(f"🟦 Paar 1: {pair1}")
    st.write(f"🟥 Paar 2: {pair2}")

    st.session_state.kreuz_lauf = st.number_input("Laufende", 0, 10, 0)
    st.session_state.kreuz_leger = st.number_input("Leger", 0, 3, 0)
    st.session_state.kreuz_schneider = st.checkbox("Schneider")
    st.session_state.kreuz_schwarz = st.checkbox("Schwarz")

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
        winner = st.multiselect("Gewinner (2)", players)

    elif game in SOLOS:
        solo = st.selectbox("Solo Spieler", players)

    st.session_state.schneider = st.checkbox("Schneider")
    st.session_state.schwarz = st.checkbox("Schwarz")
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
        "Leger": st.session_state.leger,
        "Hinweis": st.session_state.hint
    }

    for p in players:
        row[p] = 0.0

    # ============================
    # KREUZSPIEL
    # ============================
    if st.session_state.kreuz_mode:

        BASE = 0.10

        b = BASE
        b += st.session_state.kreuz_lauf * LAUF

        if st.session_state.kreuz_schneider:
            b += 0.10
        if st.session_state.kreuz_schwarz:
            b += 0.10

        pot = b * len(players) * (2 ** st.session_state.kreuz_leger)
        per = pot / len(players)

        if winner_pair == "Paar 1":
            win = pair1
            lose = pair2
        else:
            win = pair2
            lose = pair1

        for p in win:
            row[p] = per
            st.session_state.balance[p] += per

        for p in lose:
            row[p] = -per
            st.session_state.balance[p] -= per

        row["Hinweis"] += f" | KREUZ"

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

        b = base(game)
        b += st.session_state.lauf * LAUF

        pot = b * len(players) * (2 ** st.session_state.leger)
        per = pot / len(players)

        if game == "Rufspiel":

            for p in players:
                if p in winner:
                    v = per * factor
                else:
                    v = -per * factor
                st.session_state.balance[p] += v
                row[p] = v

        elif game in SOLOS:

            for p in players:
                if p == solo:
                    v = per * (len(players)-1) * factor
                else:
                    v = -per * factor
                st.session_state.balance[p] += v
                row[p] = v

        elif game == "Ramsch":

            for p in players:
                v = -per
                st.session_state.balance[p] += v
                row[p] = v

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
    st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)

# ============================
# KONTO
# ============================
st.subheader("💰 Kontostand")

for p, v in st.session_state.balance.items():
    st.write(f"{p}: {v:.2f} €")

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

# ============================
# EXPORT
# ============================
st.download_button(
    "📥 CSV Export",
    data=pd.DataFrame(st.session_state.history).to_csv(index=False),
    file_name="schafkopf.csv"
)
