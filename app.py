import streamlit as st
from google_sheets import authenticate_gspread, get_sheet_data
from rag_model import get_rag_recommendation
from about import show_about_page
from auth.login_page import show_login_page, show_logout_button
from auth.auth_utils import is_user_logged_in, get_user_display_name

def calculate_brigade(classification, area, population, risk_level, floors, has_flammable_liquids):
    # Base calculation
    if risk_level == "Baixo":
        base_brigade = area / 1000
    elif risk_level == "Médio":
        base_brigade = area / 750
    else:  # Alto
        base_brigade = area / 500

    brigade_size = base_brigade

    # Population factor
    brigade_size += population / 100

    # Floors factor
    if floors > 1:
        brigade_size += (floors - 1) / 3

    total_brigade = brigade_size

    # Classification factor
    if classification == "Hospitalar":
        total_brigade *= 1.25
    elif classification == "Industrial":
        total_brigade *= 1.20
    elif classification == "Escolar":
        total_brigade *= 1.15
    elif classification == "Comercial":
        total_brigade *= 1.10

    # Flammable liquids factor
    if has_flammable_liquids:
        total_brigade *= 1.20

    # Minimums and final rounding
    final_size = max(2, int(round(total_brigade)))

    return final_size

st.set_page_config(page_title="Cálculo de Brigadistas", page_icon="🔥", layout="wide")

def main():
    if not is_user_logged_in():
        show_login_page()
        return

    show_logout_button()
    st.sidebar.write(f"Bem-vindo, {get_user_display_name()}!")

    st.sidebar.title("Navegação")
    page = st.sidebar.radio("Selecione uma página", ["Cálculo de Brigadistas", "Sobre"])

    if page == "Cálculo de Brigadistas":
        st.title("Cálculo de Brigada de Incêndio")

        # Google Sheets Integration
        st.subheader("Integração com Google Sheets")
        spreadsheet_id = st.text_input("ID da Planilha Google")
        sheet_name = st.text_input("Nome da Aba")

        if st.button("Carregar Dados da Planilha"):
            gc = authenticate_gspread()
            if gc:
                data = get_sheet_data(gc, spreadsheet_id, sheet_name)
                if data:
                    st.session_state.sheet_data = data[0]  # Assuming first row has the data
                    st.success("Dados carregados com sucesso!")

        with st.form(key='brigade_form'):
            st.subheader("Dados da Edificação")

            # Pre-fill form with data from Google Sheets if available
            default_values = st.session_state.get('sheet_data', {})

            col1, col2 = st.columns(2)

            with col1:
                classification = st.selectbox("Classificação da Edificação", ["Residencial", "Comercial", "Industrial", "Hospitalar", "Escolar"], index=["Residencial", "Comercial", "Industrial", "Hospitalar", "Escolar"].index(default_values.get("Classificação da Edificação", "Residencial")))
                area = st.number_input("Área Total da Edificação (m²)", min_value=0.0, step=10.0, value=float(default_values.get("Área Total da Edificação (m²)", 0.0)))
                population = st.number_input("População Fixa", min_value=0, step=1, value=int(default_values.get("População Fixa", 0)))

            with col2:
                risk_level = st.selectbox("Nível de Risco", ["Baixo", "Médio", "Alto"], index=["Baixo", "Médio", "Alto"].index(default_values.get("Nível de Risco", "Baixo")))
                floors = st.number_input("Número de Pavimentos", min_value=1, step=1, value=int(default_values.get("Número de Pavimentos", 1)))
                has_flammable_liquids = st.checkbox("Possui Líquidos Inflamáveis?", value=bool(default_values.get("Possui Líquidos Inflamáveis?", False)))

            submit_button = st.form_submit_button(label='Calcular')

        if submit_button:
            brigade_size = calculate_brigade(classification, area, population, risk_level, floors, has_flammable_liquids)
            st.success(f"O número de brigadistas recomendado é: {brigade_size}")

            # Get and display RAG recommendation
            rag_data = {
                "risk_level": risk_level,
                "area": area,
                "has_flammable_liquids": has_flammable_liquids,
                "brigade_size": brigade_size
            }
            rag_recommendation = get_rag_recommendation(rag_data)
            st.markdown(rag_recommendation)

    elif page == "Sobre":
        show_about_page()

if __name__ == "__main__":
    main()
