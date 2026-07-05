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
