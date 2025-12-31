import streamlit as st
import json
import os
import hashlib
from datetime import datetime

DATA_PATH = "data/game_state.json"


# ------------------ SECURITY ------------------

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# ------------------ STATE ------------------

def load_state():
    if not os.path.exists(DATA_PATH):
        return {
            "players": {},
            "actions": {},  # name -> {"points": int, "used": bool}
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
st.caption("Più caos, più punti, più gloria 🍾")


# ------------------ SIDEBAR ------------------

mode = st.sidebar.radio(
    "🎮 Modalità",
    ["Gioco", "Admin"]
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
                save_state(state)
                st.success(f"{new_player} aggiunto 🥳")

        st.write("Attuali:")
        st.write(list(state["players"].keys()))

    # ---- ACTIONS ----
    with col2:
        st.subheader("🎭 Azioni (una sola volta!)")

        name = st.text_input("Nome azione")
        points = st.number_input("Punti", step=1)

        if st.button("➕ Aggiungi azione"):
            state["actions"][name] = {
                "points": points,
                "used": False
            }
            save_state(state)
            st.success("Azione aggiunta 💥")

        st.write("Azioni:")
        for a, v in state["actions"].items():
            status = "❌ USATA" if v["used"] else "✅ DISPONIBILE"
            st.write(f"{a}: {v['points']} pt — {status}")

    if st.button("🔥 RESET TOTALE"):
        for p in state["players"]:
            state["players"][p] = 0
        for a in state["actions"]:
            state["actions"][a]["used"] = False
        state["history"] = []
        save_state(state)
        st.warning("Tutto resettato. Caos pronto 🔥")


# ------------------ GAME MODE ------------------

else:
    st.header("🎉 MODALITÀ GIOCO")

    available_actions = [
        a for a, v in state["actions"].items() if not v["used"]
    ]

    if not state["players"] or not available_actions:
        st.warning("⚠️ Manca qualcosa (persone o azioni disponibili)")
        st.stop()

    col1, col2, col3 = st.columns(3)

    with col1:
        player = st.selectbox("👤 Persona", list(state["players"].keys()))

    with col2:
        action = st.selectbox("🎭 Azione", available_actions)

    with col3:
        st.markdown("### ")
        if st.button("💣 ASSEGNA", use_container_width=True):
            pts = state["actions"][action]["points"]
            state["players"][player] += pts
            state["actions"][action]["used"] = True

            state["history"].append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "player": player,
                "action": action,
                "points": pts
            })

            save_state(state)
            st.success(f"💥 {player} → {action} ({pts:+d})")

    st.markdown("---")

    st.subheader("🏆 CLASSIFICA")
    ranking = sorted(state["players"].items(), key=lambda x: x[1], reverse=True)

    for i, (p, s) in enumerate(ranking, 1):
        st.write(f"**{i}. {p}** — {s} punti 🍾")

    if state["history"]:
        st.markdown("---")
        st.subheader("📜 Ultimi disastri")
        for h in reversed(state["history"][-8:]):
            st.caption(
                f"{h['time']} — {h['player']} 💥 {h['action']} ({h['points']:+d})"
            )
