import streamlit as st
from utils.calculator import calculate_total_brigade, get_table_divisions
from utils.google_sheets_handler import GoogleSheetsHandler
from IA.ai_operations import AIOperations
from IA.prompts import get_brigade_analysis_prompt

def show_page(handler: GoogleSheetsHandler, ai_operator: AIOperations):
    """
    Desenha e gerencia toda a interface e lógica da página da calculadora.
    """
    st.title("Cálculo e Gestão de Brigada de Incêndio")
    
    # --- Carregamento de Dados da Planilha ---
    st.sidebar.header("Seleção da Empresa")
    company_list = handler.get_company_list()
    if not company_list:
        st.warning("Nenhuma empresa encontrada na aba 'Empresas' da planilha.")
        return

    selected_company = st.sidebar.selectbox("Selecione a Empresa para Calcular", company_list, key="company_selector")

    if selected_company:
        if st.sidebar.button("Carregar Dados da Empresa"):
            with st.spinner(f"Carregando dados para {selected_company}..."):
                st.session_state.sheet_data = handler.get_calculation_data(selected_company)
                st.rerun() 
    
    default_values = st.session_state.get('sheet_data', {})
    
    # --- Formulário de Cálculo ---
    with st.form(key='brigade_form'):
        st.header("1. Parâmetros para Cálculo")
        
        div_options = get_table_divisions()
        div_index = div_options.index(default_values.get("Divisao")) if default_values.get("Divisao") in div_options else 0
        risk_options = ["Baixo", "Médio", "Alto"]
        risk_index = risk_options.index(default_values.get("Risco")) if default_values.get("Risco") in risk_options else 2
        
        col1, col2 = st.columns(2)
        with col1:
            division = st.selectbox("Divisão da Edificação", div_options, index=div_index)
        with col2:
            risk_level = st.selectbox("Nível de Risco", risk_options, index=risk_index)

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

    # --- Lógica de Processamento e Exibição de Resultados ---
    if submit_button:
        try:
            result = calculate_total_brigade(turn_populations, division, risk_level)
            st.session_state.last_result = result
            st.session_state.last_inputs = {
                "company": selected_company, "division": division, "risk": risk_level, "populations": turn_populations
            }
        except ValueError as e:
            st.error(f"Erro no cálculo: {e}")
            st.session_state.last_result = None

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
            ia_context = {
                "division": inputs['division'], "risk": inputs['risk'],
                "total_brigade": result['total_brigadistas'],
                "maior_turno_necessidade": result['maior_turno_necessidade']
            }
            brigadistas_df = handler.get_brigadistas_list(inputs['company'])
            
            prompt = get_brigade_analysis_prompt(ia_context, brigadistas_df)
            ia_analysis = ai_operator.get_consultant_analysis(prompt)
            
            st.markdown(ia_analysis)
        
        if st.button("Salvar Cálculo Oficial na Planilha"):
            empresas_df = handler.get_data_as_df("Empresas")
            id_empresa = empresas_df.loc[empresas_df['Razao_Social'] == inputs['company'], 'ID_Empresa'].iloc[0]
            data_to_save = {
                "id_empresa": id_empresa, "usuario": get_user_email(), "divisao": inputs['division'],
                "risco": inputs['risk'], "populacao_turnos": inputs['populations'],
                "total_calculado": result['total_brigadistas'], "detalhe_turnos": result['brigadistas_por_turno']
            }
            handler.save_calculation_result(data_to_save)
