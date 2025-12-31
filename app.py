import streamlit as st
import json
import os
import hashlib
from datetime import datetime, timedelta

DATA_PATH = "data/game_state.json"


# ------------------ SECURITY ------------------

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ------------------ STATE ------------------

def load_state():
    if not os.path.exists(DATA_PATH):
        return {
            "players": {},
            "actions": {},           # action -> points
            "used_actions": {},      # player -> [actions]
            "history": [],
            "admin_password": None
        }
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    os.makedirs("data", exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


state = load_state()


# ------------------ PAGE ------------------

st.set_page_config(
    page_title="🎆 Fanta Capodanno",
    layout="wide"
)

st.title("🎆 FANTA CAPODANNO 🎆")
st.caption("Bevi, fai cazzate, accumula punti 🍾")


# ------------------ TIMER ------------------

now = datetime.now()
midnight = (now + timedelta(days=1)).replace(
    hour=0, minute=0, second=0, microsecond=0
)
remaining = midnight - now

hours, remainder = divmod(int(remaining.total_seconds()), 3600)
minutes, seconds = divmod(remainder, 60)

st.markdown(
    f"""
    ### ⏰ Countdown alla mezzanotte
    **{hours:02d}:{minutes:02d}:{seconds:02d}**
    """
)

st.markdown("---")


# ------------------ SIDEBAR ------------------

mode = st.sidebar.radio(
    "🎮 Modalità",
    ["Gioco", "Riassunto", "Admin"]
)


# ------------------ ADMIN LOGIN ------------------

def admin_login():
    pwd = st.text_input("🔑 Password admin", type="password")
    if st.button("Login"):
        if hash_password(pwd) == state["admin_password"]:
            st.session_state["admin"] = True
            st.success("Accesso riuscito 😈")
        else:
            st.error("Password sbagliata ❌")


# ------------------ ADMIN MODE ------------------

if mode == "Admin":

    if state["admin_password"] is None:
        st.warning("⚠️ Prima volta: imposta la password admin")
        new_pwd = st.text_input("Nuova password", type="password")
        if st.button("Salva password"):
            state["admin_password"] = hash_password(new_pwd)
            save_state(state)
            st.success("Password impostata 🔐")
        st.stop()

    if not st.session_state.get("admin", False):
        admin_login()
        st.stop()

    st.header("⚙️ MODALITÀ ADMIN")

    col1, col2 = st.columns(2)

    # ---- PLAYERS ----
    with col1:
        st.subheader("👥 Persone")

        new_player = st.text_input("Nome persona")
        if st.button("➕ Aggiungi persona"):
            if new_player and new_player not in state["players"]:
                state["players"][new_player] = 0
                state["used_actions"][new_player] = []
                save_state(state)
                st.success(f"{new_player} aggiunto 🥳")

        st.write("Attuali:")
        st.write(list(state["players"].keys()))

    # ---- ACTIONS ----
    with col2:
        st.subheader("🎭 Azioni")

        name = st.text_input("Nome azione")
        points = st.number_input("Punti", step=1)

        if st.button("➕ Aggiungi azione"):
            if name:
                state["actions"][name] = points
                save_state(state)
                st.success("Azione aggiunta 💥")

        st.write("Azioni disponibili:")
        for a, p in state["actions"].items():
            st.write(f"{a}: {p} pt")

    if st.button("🔥 RESET TOTALE"):
        for p in state["players"]:
            state["players"][p] = 0
            state["used_actions"][p] = []
        state["history"] = []
        save_state(state)
        st.warning("Tutto resettato. Si riparte 🍾")


# ------------------ GAME MODE ------------------

elif mode == "Gioco":
    st.header("🎉 MODALITÀ GIOCO")

    if not state["players"] or not state["actions"]:
        st.warning("⚠️ Mancano persone o azioni (Admin)")
        st.stop()

    col1, col2, col3 = st.columns(3)

    with col1:
        player = st.selectbox("👤 Persona", list(state["players"].keys()))

    available_actions = [
        a for a in state["actions"]
        if a not in state["used_actions"].get(player, [])
    ]

    with col2:
        if available_actions:
            action = st.selectbox("🎭 Azione", available_actions)
        else:
            action = None
            st.warning("🚫 Questa persona ha già fatto tutto!")

    with col3:
        st.markdown("### ")
        if action and st.button("💣 ASSEGNA", use_container_width=True):
            pts = state["actions"][action]
            state["players"][player] += pts
            state["used_actions"][player].append(action)

            state["history"].append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "player": player,
                "action": action,
                "points": pts
            })

            save_state(state)
            st.success(f"💥 {player} → {action} ({pts:+d})")

    st.markdown("---")

    st.subheader("🏆 CLASSIFICA LIVE")

    ranking = sorted(
        state["players"].items(),
        key=lambda x: x[1],
        reverse=True
    )

    for i, (p, s) in enumerate(ranking, 1):
        st.write(f"**{i}. {p}** — {s} punti 🍾")

    if state["history"]:
        st.markdown("---")
        st.subheader("📜 Ultimi eventi")
        for h in reversed(state["history"][-8:]):
            st.caption(
                f"{h['time']} — {h['player']} 💥 {h['action']} ({h['points']:+d})"
            )


# ------------------ SUMMARY MODE ------------------

else:
    st.header("📊 RIASSUNTO GENERALE")

    if not state["players"]:
        st.info("Nessun dato ancora 🤷‍♂️")
        st.stop()

    for player in state["players"]:
        st.subheader(f"👤 {player}")
        st.write(f"⭐ **Punteggio:** {state['players'][player]}")

        used = state["used_actions"].get(player, [])
        if used:
            st.write("🎭 Azioni fatte:")
            st.write(", ".join(used))
        else:
            st.write("😇 Nessuna azione ancora")

        st.markdown("---")
