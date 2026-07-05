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
# STATE
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

    # inputs
    st.session_state.game = None
    st.session_state.winner = []
    st.session_state.solo = None
    st.session_state.schneider = False
    st.session_state.schwarz = False
    st.session_state.lauf = 0
    st.session_state.leger = 0
    st.session_state.hint = ""

st.title("🃏 Schafkopf Rechner")

# ============================
# SETUP
# ============================
if st.session_state.step == 1:

    n = st.selectbox("4 oder 5 Spieler", [4, 5])

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

def make_pairs(players):
    return [
        (players[0], players[1]),
        (players[2], players[3])
    ]

# ============================
# UI
# ============================
players, pause = active_players()

st.info(f"Runde: {st.session_state.round}")
if pause:
    st.warning(f"Pause: {pause}")

if st.session_state.kreuz_mode:
    st.error(f"🔥 KREUZRUNDE {5 - st.session_state.kreuz_left}/4 AKTIV")

# ============================
# SPIEL LOGIK
# ============================
game = None
winner = []
solo = None

# ----------------------------
# KREUZ MODUS
# ----------------------------
if st.session_state.kreuz_mode:

    st.subheader("🔥 Kreuzspiel – Paardefinition")

    st.info("Wähle die Paare für diese Runde")

    pair1 = st.multiselect("🟦 Paar 1", players)
    pair2 = st.multiselect("🟥 Paar 2", players)

    winner_pair = None

    if len(pair1) == 2 and len(pair2) == 2:

        if set(pair1).isdisjoint(set(pair2)):

            winner_pair = st.radio(
                "Gewonnenes Paar",
                ["Paar 1", "Paar 2"]
            )

        else:
            st.error("❌ Spieler dürfen nicht in beiden Paaren sein")

    game = "KREUZ"

else:

    games = ["Rufspiel", "Farbsolo", "Geier", "Wenz", "Bettel", "Herzsolo", "Ramsch"]

    cols = st.columns(4)
    selected = []

    for i, g in enumerate(games):
        if cols[i % 4].checkbox(g):
            selected.append(g)

    game = selected[0] if selected else None

    result = st.radio("Spielausgang", ["Gewonnen", "Verloren"], horizontal=True)

    winner = []
    solo = None

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
# CALC
# ============================
def base(g):
    if g == "Rufspiel":
        return BASE_RUF
    if g in SOLOS:
        return BASE_SOLO
    return BASE_RAM

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

    for p in st.session_state.players:
        row[p] = 0.0

    # ============================
    # KREUZSPIEL
    # ============================
 if st.session_state.kreuz_mode:

    if winner_pair == "Paar 1":
        win = pair1
        lose = pair2
    else:
        win = pair2
        lose = pair1

    for p in win:
        row[p] = 1
        st.session_state.balance[p] += 1

    for p in lose:
        row[p] = -1
        st.session_state.balance[p] -= 1

    # Speicherung der Paarung!
    row["Hinweis"] += f" | P1:{pair1} P2:{pair2}"

    st.session_state.kreuz_left -= 1

    if st.session_state.kreuz_left <= 0:
        st.session_state.kreuz_mode = False
        reset_inputs()

    # ============================
    # NORMALES SPIEL
    # ============================
    else:

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
    st.session_state.dealer += 1

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
if st.button("↩️ Undo letzte Runde"):

    if st.session_state.history:
        last = st.session_state.history.pop()

        for p in st.session_state.players:
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
