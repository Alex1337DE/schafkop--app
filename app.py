import streamlit as st
import pandas as pd

# ----------------------------
# KONSTANTEN
# ----------------------------
BASE_RUF = 0.10
BASE_SOLO = 0.20
BASE_RAM = 0.10
LAUF = 0.05

SOLOS = ["Farbsolo", "Geier", "Wenz", "Bettel", "Herzsolo"]
ALLE = ["Rufspiel"] + SOLOS + ["Ramsch"]

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

st.title("🃏 Schafkopf Rechner")

# ============================================================
# STEP 1
# ============================================================
if st.session_state.step == 1:

    st.subheader("👥 Anzahl Spieler")

    n = st.selectbox("4 oder 5 Spieler", [4, 5])

    if st.button("Weiter"):
        st.session_state.num = n
        st.session_state.step = 2
        st.rerun()

    st.stop()

# ============================================================
# STEP 2
# ============================================================
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
# HELPER
# ============================================================
def active_players():
    if len(st.session_state.players) == 5:
        pause = st.session_state.players[st.session_state.dealer % 5]
        return [p for p in st.session_state.players if p != pause], pause
    return st.session_state.players, None


def base(game):
    if game == "Rufspiel":
        return BASE_RUF
    if game in SOLOS:
        return BASE_SOLO
    return BASE_RAM


# ============================================================
# GAME UI
# ============================================================
players, pause = active_players()

st.info(f"Runde: {st.session_state.round}")
if pause:
    st.warning(f"Pause-Spieler: {pause}")

if st.session_state.kreuz_mode:
    st.error(f"🔥 Kreuzrunde aktiv ({st.session_state.kreuz_left}/4)")

game = st.selectbox("Spiel", ALLE)

# 🟢 NEU: Spielausgang
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
# ABBRECHNUNG
# ============================================================
if st.button("💰 Abrechnen"):

    factor = 1 if result == "Gewonnen" else -1

    base_val = base(game)

    if schneider:
        base_val += 0.10
    if schwarz:
        base_val += 0.10

    base_val += lauf * LAUF

    pot = base_val * len(players)
    pot *= (2 ** leger)

    per = pot / len(players)

    row = {
        "Nr": st.session_state.round,
        "Spiel": game,
        "Leger": leger,
        "Hinweis": hint + (" | VERLOREN" if factor == -1 else "")
    }

    for p in st.session_state.players:
        row[p] = 0.0

    # ----------------------------
    # RUF
    # ----------------------------
    if game == "Rufspiel":
        for p in players:
            if p in winner:
                st.session_state.balance[p] += per * factor
                row[p] = per * factor
            else:
                st.session_state.balance[p] -= per * factor
                row[p] = -per * factor

    # ----------------------------
    # SOLO
    # ----------------------------
    elif game in SOLOS:
        for p in players:
            if p == solo:
                st.session_state.balance[p] += per * (len(players) - 1) * factor
                row[p] = per * (len(players) - 1) * factor
            else:
                st.session_state.balance[p] -= per * factor
                row[p] = -per * factor

        if game == "Herzsolo" and len(players) == 4:
            st.session_state.kreuz_mode = True
            st.session_state.kreuz_left = 4

    # ----------------------------
    # RAMSCH
    # ----------------------------
    elif game == "Ramsch":
        for p in players:
            st.session_state.balance[p] -= per
            row[p] = -per

    # ----------------------------
    # KREUZ
    # ----------------------------
    if st.session_state.kreuz_mode:
        row["Hinweis"] += " | Kreuzrunde"
        st.session_state.kreuz_left -= 1
        if st.session_state.kreuz_left <= 0:
            st.session_state.kreuz_mode = False

    st.session_state.history.append(row)
    st.session_state.round += 1
    st.session_state.dealer += 1

    st.success("Abgerechnet!")
    st.rerun()

# ============================================================
# HISTORIE
# ============================================================
st.subheader("📊 Historie")

if st.session_state.history:
    st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)

# ============================================================
# STAND
# ============================================================
st.subheader("💰 Kontostand")

for p, v in st.session_state.balance.items():
    st.write(f"{p}: {v:.2f} €")

# ============================================================
# ENDE
# ============================================================
if st.button("🏁 Spieltag beenden"):

    st.subheader("📊 Endstand")

    for p, v in st.session_state.balance.items():
        st.write(f"{p}: {v:.2f} €")

    st.download_button(
        "📥 CSV Export",
        data=pd.DataFrame(st.session_state.history).to_csv(index=False),
        file_name="schafkopf_spieltag.csv"
    )

    st.success("Spieltag beendet")
