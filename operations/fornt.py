
import streamlit as st
from utils.google_sheets_handler import GoogleSheetsHandler
from IA.ai_operations import AIOperations
from utils.calculator import calculate_total_brigade, get_table_divisions
from IA.prompts import get_brigade_analysis_prompt
import re

def is_valid_date_format(date_string: str) -> bool:
    pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")
    return pattern.match(date_string) is not None

def show_brigade_management_page(handler: GoogleSheetsHandler, ai_operator: AIOperations, company_list: list):
    st.title("Gestão de Brigadistas e Atestados")

    if not company_list:
        st.error("A lista de empresas está vazia. Verifique a aba 'Empresas' da sua planilha.")
        return

    st.markdown("Use esta página para adicionar novos brigadistas à sua planilha a partir de um atestado de treinamento em PDF.")
    
    with st.container(border=True):
        st.subheader("1. Selecione a Empresa e o Atestado")
        selected_company = st.selectbox("Para qual empresa este atestado se aplica?", company_list)
        validity_date = st.text_input("Data de Validade (DD/MM/AAAA)", placeholder="Ex: 31/12/2025")
        uploaded_file = st.file_uploader("Carregue o atestado PDF", type="pdf")

    is_date_valid = is_valid_date_format(validity_date)
    
    if st.button("Extrair e Adicionar Brigadistas", disabled=(not all([uploaded_file, selected_company, is_date_valid]))):
        with st.spinner("IA analisando o atestado..."):
            extracted_data = ai_operator.extract_brigadistas_from_pdf(uploaded_file)
        if extracted_data and "nomes" in extracted_data and extracted_data["nomes"]:
            nomes = extracted_data["nomes"]
            st.success(f"IA extraiu {len(nomes)} nomes com sucesso!")
            with st.expander("Ver nomes extraídos"):
                st.write(nomes)
            with st.spinner("Adicionando à planilha..."):
                empresas_df = handler.get_data_as_df("Empresas")
                id_empresa = empresas_df.loc[empresas_df['Razao_Social'] == selected_company, 'ID_Empresa'].iloc[0]
                handler.add_brigadistas_to_sheet(id_empresa, nomes, validity_date)
        else:
            st.error("IA não conseguiu extrair nomes do documento.")
            if extracted_data: st.json(extracted_data)
    elif not is_date_valid and validity_date:
        st.error("Formato de data inválido. Use DD/MM/AAAA.")


def show_calculator_page(handler: GoogleSheetsHandler, ai_operator: AIOperations, user_email: str, company_list: list):
    st.title("Cálculo e Gestão de Brigada de Incêndio")
    
    st.sidebar.header("Seleção da Empresa")
    
    if not company_list:
        st.error("A lista de empresas está vazia. Verifique a aba 'Empresas' da sua planilha.")
        return

    selected_company = st.sidebar.selectbox("Selecione a Empresa", company_list, key="company_selector")

    if st.sidebar.button("Carregar Dados da Empresa"):
        with st.spinner(f"Carregando dados para {selected_company}..."):
            st.session_state.sheet_data = handler.get_calculation_data(selected_company)
            st.rerun() 
    
    default_values = st.session_state.get('sheet_data', {})
    
    with st.form(key='brigade_form'):
        st.header("1. Parâmetros para Cálculo")
        div_options = get_table_divisions()
        div_index = div_options.index(default_values.get("Divisao")) if default_values.get("Divisao") in div_options else 0
        risk_options = ["Baixo", "Médio", "Alto"]
        risk_index = risk_options.index(default_values.get("Risco")) if default_values.get("Risco") in risk_options else 2
        col1, col2 = st.columns(2)
        with col1: division = st.selectbox("Divisão", div_options, index=div_index)
        with col2: risk_level = st.selectbox("Nível de Risco", risk_options, index=risk_index)
        st.subheader("População Fixa por Turno")
        pop_keys = sorted([k for k in default_values.keys() if k.startswith('Pop_Turno')])
        initial_pops = [int(default_values.get(k, 0)) for k in pop_keys]
        if not initial_pops: initial_pops = [0, 0, 0]
        turn_populations = []
        cols_turnos = st.columns(len(initial_pops))
        for i, col in enumerate(cols_turnos):
            with col:
                pop = col.number_input(f"Pop. Turno {i+1}", min_value=0, step=1, value=initial_pops[i])
                turn_populations.append(pop)
        submit_button = st.form_submit_button(label='Calcular e Analisar com IA')

    if submit_button:
        result = calculate_total_brigade(turn_populations, division, risk_level)
        st.session_state.last_result = result
        st.session_state.last_inputs = { "company": selected_company, "division": division, "risk": risk_level, "populations": turn_populations }

    if 'last_result' in st.session_state and st.session_state.last_result:
        result = st.session_state.last_result
        inputs = st.session_state.last_inputs
        st.header(f"2. Resultado para: {inputs['company']}")
        with st.container(border=True):
            st.subheader("Cálculo Mínimo (ABNT NBR 14276)")
            col1, col2 = st.columns(2)
            col1.metric("Total de Brigadistas", result['total_brigadistas'])
            col2.metric("Efetivo Mínimo por Turno", result['maior_turno_necessidade'])
        with st.container(border=True):
            ia_context = { "division": inputs['division'], "risk": inputs['risk'], "total_brigade": result['total_brigadistas'], "maior_turno_necessidade": result['maior_turno_necessidade'] }
            brigadistas_df = handler.get_brigadistas_list(inputs['company'])
            prompt = get_brigade_analysis_prompt(ia_context, brigadistas_df)
            ia_analysis = ai_operator.get_consultant_analysis(prompt)
            st.markdown(ia_analysis)
        if st.button("Salvar Cálculo Oficial na Planilha"):
            empresas_df = handler.get_data_as_df("Empresas")
            id_empresa = empresas_df.loc[empresas_df['Razao_Social'] == inputs['company'], 'ID_Empresa'].iloc[0]
            data_to_save = { "id_empresa": id_empresa, "usuario": user_email, "divisao": inputs['division'], "risco": inputs['risk'], "populacao_turnos": inputs['populations'], "total_calculado": result['total_brigadistas'], "detalhe_turnos": result['brigadistas_por_turno'] }
            handler.save_calculation_result(data_to_save)
