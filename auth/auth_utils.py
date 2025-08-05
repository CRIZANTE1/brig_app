# auth/auth_utils.py
import streamlit as st
import pandas as pd
from utils.google_sheets_handler import GoogleSheetsHandler, ADMIN_SHEET_NAME

def is_oidc_available():
    return hasattr(st, 'user') and hasattr(st.user, 'is_logged_in')

def is_user_logged_in():
    return is_oidc_available() and st.user.is_logged_in

def get_user_display_name():
    if is_user_logged_in():
        return st.user.name or st.user.email
    return "Usuário"

def get_user_email():
    if is_user_logged_in():
        return st.user.email
    return None

@st.cache_data(ttl=600)
def get_admin_users_by_email():
    try:
        handler = GoogleSheetsHandler()
        df = handler.get_data_as_df(ADMIN_SHEET_NAME)
        
        if df.empty:
            st.warning(f"Aba de administradores ('{ADMIN_SHEET_NAME}') não encontrada ou vazia.")
            return []

        email_col = next((col for col in df.columns if col.strip().lower() == 'email'), None)
        if email_col:
            return [str(email).strip().lower() for email in df[email_col].dropna() if email]
        else:
            st.error(f"A aba '{ADMIN_SHEET_NAME}' precisa de uma coluna chamada 'Email'.")
            return []
    except Exception as e:
        st.error(f"Erro ao buscar lista de administradores: {e}")
        return []

def is_admin_user():
    user_email = get_user_email()
    if not user_email:
        return False
    return user_email.strip().lower() in get_admin_users_by_email()


