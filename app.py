import streamlit as st

# ----------------------------
# KONFIGURATION
# ----------------------------
BASE_RUF = 0.10
BASE_SOLO = 0.20
BASE_RAM = 0.10

LAUFENDEN_WERT = 0.05

SPIELER_LIMIT = 5

SOLO_SPIELE = ["Farbsolo", "Geier", "Wenz", "Bettel"]
ALLE_SPIELE = ["Rufspiel"] + SOLO_SPIELE + ["Ramsch"]

# ----------------------------
# INIT STATE
# ----------------------------
if "players" not in st.session_state:
    st.session_state.players = ["Spieler 1", "Spieler 2", "Spieler 3", "Spieler 4", "Spieler 5"]
    st.session_state.balance = {p: 0.0 for p in st.session_state.players}
    st.session_state.dealer = 0
    st.session_state.round = 1

# ----------------------------
# HELPER
# ----------------------------
def get_active_players():
    # 5 Spieler, aber 1 sitzt pro Runde aus
    pause_player = st.session_state.players[st.session_state.dealer % 5]
    return [p for p in st.session_state.players if p != pause_player], pause_player


def next_round():
    st.session_state.dealer = (st.session_state.dealer + 1) % 5
    st.session_state.round += 1


def apply_result(players_in, pause_player, game_type, winner_team, solo_player,
                 schneider, schwarz, laufende, legers):

    # -------------------------
    # BASISWERT
    # -------------------------
    if game_type == "Rufspiel":
        base = BASE_RUF
    elif game_type in SOLO_SPIELE:
        base = BASE_SOLO
    else:
        base = BASE_RAM

    # -------------------------
    # BONUS SCHNEIDER / SCHWARZ
    # -------------------------
    if schneider:
        base += 0.10
    if schwarz:
        base += 0.10

    # -------------------------
    # LAUFENDE
    # -------------------------
    base += laufende * LAUFENDEN_WERT

    # -------------------------
    # POT (ohne Leger!)
    # -------------------------
    pot = base * len(players_in)

    # -------------------------
    # LEGERS (NACHHER!)
    # -------------------------
    pot *= (2 ** legers)

    # -------------------------
    # VERTEILUNG
    # -------------------------
    per_player = pot / len(players_in)

    # -------------------------
    # AUSZAHLUNG
    # -------------------------
    for p in players_in:
        if game_type == "Rufspiel":
            if p in winner_team:
                st.session_state.balance[p] += per_player
            else:
                st.session_state.balance[p] -= per_player

        elif game_type in SOLO_SPIELE:
            if p == solo_player:
                st.session_state.balance[p] += per_player * (len(players_in) - 1)
            else:
                st.session_state.balance[p] -= per_player

        elif game_type == "Ramsch":
            # simpel: alle gleich
            st.session_state.balance[p] -= per_player


# ----------------------------
# UI
# ----------------------------
st.title("🃏 Schafkopf Rechner")

players_in, pause_player = get_active_players()

st.info(f"🔄 Pause-Spieler diese Runde: **{pause_player}**")

st.subheader(f"Runde {st.session_state.round}")

# ----------------------------
# SPIELWAHL
# ----------------------------
game_type = st.selectbox("Spieltyp", ALLE_SPIELE)

# ----------------------------
# SOLO PLAYER
# ----------------------------
solo_player = None
winner_team = []

if game_type == "Rufspiel":
    st.write("🏆 Gewinnerteam wählen:")
    winner_team = st.multiselect("Gewinner (2 Spieler)", players_in)

elif game_type in SOLO_SPIELE:
    solo_player = st.selectbox("Solo-Spieler", players_in)

# ----------------------------
# PARAMETER
# ----------------------------
schneider = st.checkbox("Schneider (<30 Punkte)")
schwarz = st.checkbox("Schwarz (0 Stiche)")
laufende = st.number_input("Laufende", min_value=0, max_value=10, value=0)
legers = st.number_input("Leger", min_value=0, max_value=3, value=0)

# ----------------------------
# ABSCHLUSS
# ----------------------------
if st.button("💰 Spiel abrechnen"):

    if game_type == "Rufspiel" and len(winner_team) != 2:
        st.error("Bitte genau 2 Gewinner wählen!")
    else:
        apply_result(
            players_in,
            pause_player,
            game_type,
            winner_team,
            solo_player,
            schneider,
            schwarz,
            laufende,
            legers
        )
        st.success("Spiel abgerechnet!")

        next_round()

# ----------------------------
# KONTOSTAND
# ----------------------------
st.subheader("📊 Kontostand")

for p, bal in st.session_state.balance.items():
    st.write(f"{p}: {bal:.2f} €")
