import streamlit as st

def show_about_page():
    st.title("Sobre o App de Cálculo de Brigadistas")

    st.markdown("""
    Este aplicativo foi desenvolvido para auxiliar no cálculo da quantidade de brigadistas necessários para uma edificação, de acordo com as normas de segurança contra incêndio.

    **Funcionalidades:**

    * **Cálculo de Brigadistas:** Calcula a quantidade de brigadistas com base nos dados da edificação.
    * **Integração com Google Sheets:** Carrega os dados da edificação a partir de uma planilha Google.
    * **Recomendação da IA:** Fornece uma recomendação da IA para a quantidade de brigadistas, com base em um modelo de RAG (Retrieval-Augmented Generation).

    **Desenvolvido por:**

    * **[Seu Nome]([URL do seu perfil no GitHub ou LinkedIn])**
    """)
