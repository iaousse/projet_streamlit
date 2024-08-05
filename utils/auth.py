# utils/auth.py
import bcrypt
import streamlit as st

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def authenticate(username, password):
    if username in st.secrets["users"]:
        hashed_password = st.secrets["users"][username]
        if check_password(password, hashed_password):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            return True
    return False

def login():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    if st.session_state["authenticated"]:
        st.title("Performance enquêtes")
        st.write("Bienvenue dans le tableau de bord de performance des enquêtes.")
        return True

    st.title("Login")
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        if authenticate(username, password):
            st.success("Connexion réussie")
            return True
        else:
            st.error("Échec de la connexion")
    return False

def logout():
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
