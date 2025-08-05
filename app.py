# app.py
import streamlit as st
import pandas as pd
from utils.calculator import calculate_total_brigade, get_table_divisions
from utils.google_sheets_handler import GoogleSheetsHandler
from about import show_about_page
from auth.login_page import show_login_page, show_logout_button
from auth.auth_utils import is_user_logged_in, get_user_display_name, get_user_email

st.set_page_config(page_title="Cálculo de Brigadistas", page_icon="", layout="wide")

def show_calculator_page(handler: GoogleSheetsHandler):
    """Mostra a página principal da calculadora."""
    st.title("Cálculo e Gestão de Brigada de Incêndio")
    
    # --- Carregamento de Dados da Planilha ---
    st.sidebar.header("Seleção da Empresa")
    company_list = handler.get_company_list()
    if not company_list:
        st.warning("Nenhuma empresa encontrada na aba 'Empresas' da planilha.")
        return

    selected_company = st.sidebar.selectbox("Selecione a Empresa para Calcular", company_list)

    if selected_company:
        if st.sidebar.button("Carregar Dados da Empresa"):
            with st.spinner(f"Carregando dados para {selected_company}..."):
                st.session_state.sheet_data = handler.get_calculation_data(selected_company)
                if st.session_state.sheet_data:
                    st.sidebar.success("Dados carregados!")
                else:
                    st.sidebar.error("Dados não encontrados para esta empresa.")
    
    default_values = st.session_state.get('sheet_data', {})
    
    # --- Formulário de Cálculo ---
    with st.form(key='brigade_form'):
        st.header("1. Parâmetros para Cálculo")
        
        # Preenche os valores com dados da planilha, se carregados
        div_index = get_table_divisions().index(default_values.get("Divisao", "M-2")) if default_values.get("Divisao") in get_table_divisions() else 0
        risk_index = ["Baixo", "Médio", "Alto"].index(default_values.get("Risco", "Alto")) if default_values.get("Risco") in ["Baixo", "Médio", "Alto"] else 2
        
        col1, col2 = st.columns(2)
        with col1:
            division = st.selectbox("Divisão da Edificação", get_table_divisions(), index=div_index)
        with col2:
            risk_level = st.selectbox("Nível de Risco", ["Baixo", "Médio", "Alto"], index=risk_index)

        st.subheader("População Fixa por Turno")
        # Extrai populações dos dados carregados (Pop_Turno1, Pop_Turno2, etc.)
        pop_keys = sorted([k for k in default_values.keys() if k.startswith('Pop_Turno')])
        initial_pops = [int(default_values.get(k, 0)) for k in pop_keys]
        if not initial_pops: initial_pops = [0, 0, 0] # Padrão se não houver dados

        turn_populations = []
        cols_turnos = st.columns(len(initial_pops))
        for i, col in enumerate(cols_turnos):
            with col:
                pop = col.number_input(f"Pop. Turno {i+1}", min_value=0, step=1, value=initial_pops[i])
                turn_populations.append(pop)

        submit_button = st.form_submit_button(label='Calcular Brigada')

    # --- Exibição de Resultados ---
    if submit_button:
        try:
            result = calculate_total_brigade(turn_populations, division, risk_level)
            st.session_state.last_result = result
            st.session_state.last_inputs = {
                "company": selected_company,
                "division": division,
                "risk": risk_level,
                "populations": turn_populations
            }
        except ValueError as e:
            st.error(f"Erro no cálculo: {e}")
            st.session_state.last_result = None

    if 'last_result' in st.session_state and st.session_state.last_result:
        result = st.session_state.last_result
        inputs = st.session_state.last_inputs
        
        st.header(f"2. Resultado do Dimensionamento para: {inputs['company']}")
        col1, col2 = st.columns(2)
        col1.metric("Total de Brigadistas Necessários", result['total_brigadistas'])
        col2.metric("Efetivo Mínimo por Turno (Maior Turno)", result['maior_turno_necessidade'])
        
        with st.expander("Ver Detalhes do Cálculo por Turno"):
            for i, num in enumerate(result['brigadistas_por_turno']):
                st.write(f"- **Turno {i+1}:** Necessita de **{num} brigadistas** (para uma população de {inputs['populations'][i]}) ")
        
        # --- Brigadistas Atuais e Opção de Salvar ---
        st.header("3. Gestão e Ações")
        brigadistas_df = handler.get_brigadistas_list(inputs['company'])
        
        st.subheader("Brigadistas Treinados Atualmente")
        if not brigadistas_df.empty:
            st.dataframe(brigadistas_df[['Nome_Brigadista', 'Validade_Treinamento']])
            st.info(f"Você possui **{len(brigadistas_df)}** brigadistas treinados para esta localidade.")
        else:
            st.warning("Nenhum brigadista treinado encontrado na planilha para esta empresa.")

        if st.button("Salvar este Resultado na Planilha"):
            empresas_df = handler.get_data_as_df(handler, "Empresas")
            id_empresa = empresas_df.loc[empresas_df['Razao_Social'] == inputs['company'], 'ID_Empresa'].iloc[0]
            
            data_to_save = {
                "id_empresa": id_empresa,
                "usuario": get_user_email(),
                "divisao": inputs['division'],
                "risco": inputs['risk'],
                "populacao_turnos": inputs['populations'],
                "total_calculado": result['total_brigadistas'],
                "detalhe_turnos": result['brigadistas_por_turno']
            }
            handler.save_calculation_result(data_to_save)


def main():
    if not is_user_logged_in():
        show_login_page()
        return

    show_logout_button()
    st.sidebar.success(f"Bem-vindo, {get_user_display_name()}!")

    # Inicializa o handler do Google Sheets uma vez
    handler = GoogleSheetsHandler()

    st.sidebar.title("Navegação")
    page = st.sidebar.radio("Selecione uma página", ["Cálculo de Brigadistas", "Sobre"])

    if page == "Cálculo de Brigadistas":
        show_calculator_page(handler)
    elif page == "Sobre":
        show_about_page()

if __name__ == "__main__":
    main()