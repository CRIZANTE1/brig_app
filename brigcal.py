import streamlit as st
from operations.pagefront import pagefront, pagina_sobre  
from login.login import load_users_db, login
from login.adm_interface import admin_interface


st.set_page_config(page_title="Cálculo de Brigadistas", page_icon="🧊", layout="wide")

def main():
    try:
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in=False

        if st.session_state.logged_in:
            paginas = ["Cálculo de Brigadistas", "Sobre"]
            if st.session_state.role == "admin":
                paginas.append("Adicionar Usuário")

            pagina = st.sidebar.selectbox("Escolha uma página", paginas)

            if pagina == "Cálculo de Brigadistas":
                    pagefront()  # Chama a função que contém a lógica do cálculo
            if pagina == "Adicionar Usuário":
                admin_interface()
            elif pagina == "Sobre":
                pagina_sobre()
        else:
            users_db = load_users_db()
            login(users_db)
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {str(e)}")
        st.error(f"Erro: {e}")

if __name__ == "__main__":
    main()

