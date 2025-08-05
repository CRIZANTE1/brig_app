import streamlit as st
from utils.calculator import calculate_total_brigade, get_table_divisions
from utils.google_sheets_handler import GoogleSheetsHandler
from IA.rag_analyzer import RAGAnalyzer
import re


def is_valid_date_format(date_string: str) -> bool:
    """
    Verifica se a string de data fornecida está no formato DD/MM/AAAA.
    Retorna True se o formato for válido, False caso contrário.
    """
    # Garante que a entrada é uma string antes de tentar a validação
    if not isinstance(date_string, str):
        return False
    # Expressão regular para validar o formato DD/MM/AAAA
    pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")
    return pattern.match(date_string) is not None



def show_brigade_management_page(handler: GoogleSheetsHandler, rag_analyzer: RAGAnalyzer, company_list: list):
    """
    Desenha e gerencia a interface da página de Gestão de Brigadistas,
    permitindo o upload de atestados para extração de dados com IA.
    """
    st.title("Gestão de Brigadistas e Atestados")

    # Verifica se a lista de empresas foi carregada. Se não, exibe um erro e para.
    if not company_list:
        st.error("A lista de empresas está vazia. Verifique a aba 'Empresas' da sua planilha.")
        return

    st.markdown("Use esta página para adicionar novos brigadistas à sua planilha a partir de um atestado de treinamento em PDF.")
    
    with st.container(border=True):
        st.subheader("1. Selecione a Empresa e o Atestado")
        selected_company = st.selectbox(
            "Para qual empresa este atestado se aplica?", 
            company_list, 
            key="mgmt_company_selector"
        )
        validity_date = st.text_input(
            "Data de Validade do Treinamento (DD/MM/AAAA)", 
            placeholder="Ex: 31/12/2025"
        )
        uploaded_file = st.file_uploader(
            "Carregue o atestado de brigada (PDF)", 
            type="pdf", 
            key="pdf_uploader"
        )

    is_date_valid = is_valid_date_format(validity_date)
    
    # O botão só é habilitado se todos os campos estiverem preenchidos corretamente
    if st.button("Extrair e Adicionar Brigadistas com IA", disabled=(not all([uploaded_file, selected_company, is_date_valid]))):
        with st.spinner("IA analisando o atestado... Este processo pode levar um momento."):
            extracted_data = rag_analyzer.extract_brigadistas_from_pdf(uploaded_file)

        if extracted_data and "nomes" in extracted_data and extracted_data["nomes"]:
            nomes = extracted_data["nomes"]
            st.success(f"IA extraiu {len(nomes)} nomes do atestado com sucesso!")
            
            with st.expander("Ver nomes extraídos antes de salvar"):
                st.write(nomes)
                
            with st.spinner("Adicionando brigadistas à planilha..."):
                empresas_df = handler.get_data_as_df("Empresas")
                id_empresa = empresas_df.loc[empresas_df['Razao_Social'] == selected_company, 'ID_Empresa'].iloc[0]
                handler.add_brigadistas_to_sheet(id_empresa, nomes, validity_date)
        else:
            st.error("A IA não conseguiu extrair uma lista de nomes válida do documento. Verifique o PDF ou tente novamente.")
            if extracted_data:
                st.json(extracted_data) # Mostra a resposta da IA para depuração
    elif not is_date_valid and validity_date:
        # Mostra um erro se o usuário digitou algo, mas o formato está errado
        st.error("Formato de data inválido. Por favor, use DD/MM/AAAA.")

# ==============================================================================
# LÓGICA DA PÁGINA DA CALCULADORA
# ==============================================================================

def show_calculator_page(handler: GoogleSheetsHandler, rag_analyzer: RAGAnalyzer, user_email: str, company_list: list):
    """
    Desenha e gerencia a interface da página principal de Cálculo de Brigada.
    """
    st.title("Cálculo e Análise de Brigada de Incêndio")
    
    st.sidebar.header("Seleção da Empresa")
    
    if not company_list:
        st.error("A lista de empresas está vazia. Verifique a aba 'Empresas' da sua planilha.")
        return

    selected_company = st.sidebar.selectbox("Selecione a Empresa", company_list, key="calc_company_selector")

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
        with col1:
            division = st.selectbox("Divisão da Edificação", div_options, index=div_index)
        with col2:
            risk_level = st.selectbox("Nível de Risco", risk_options, index=risk_index)
            
        st.subheader("População Fixa por Turno")
        pop_keys = sorted([k for k in default_values.keys() if k.startswith('Pop_Turno')])
        initial_pops = [int(default_values.get(k, 0)) for k in pop_keys]
        if not initial_pops:
            initial_pops = [0, 0, 0] # Padrão de 3 turnos se nenhum dado for carregado
            
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
            col1.metric("Total de Brigadistas Necessários", result['total_brigadistas'])
            col2.metric("Efetivo Mínimo por Turno (Maior Turno)", result['maior_turno_necessidade'])

        with st.container(border=True):
            st.subheader("Análise Fundamentada da IA (RAG)")
            with st.spinner("IA consultando a base de conhecimento e elaborando a análise..."):
                ia_context = { 
                    "division": inputs['division'], 
                    "risk": inputs['risk'], 
                    "total_brigade": result['total_brigadistas'],
                    "populations": inputs['populations']
                }
                contextual_analysis = rag_analyzer.get_contextual_analysis(ia_context)
                st.markdown(contextual_analysis)
        
        if st.button("Salvar Cálculo Oficial na Planilha"):
            empresas_df = handler.get_data_as_df("Empresas")
            id_empresa = empresas_df.loc[empresas_df['Razao_Social'] == inputs['company'], 'ID_Empresa'].iloc[0]
            data_to_save = { 
                "id_empresa": id_empresa, 
                "usuario": user_email, 
                "divisao": inputs['division'], 
                "risco": inputs['risk'], 
                "populacao_turnos": inputs['populations'], 
                "total_calculado": result['total_brigadistas'], 
                "detalhe_turnos": result['brigadistas_por_turno'] 
            }
            handler.save_calculation_result(data_to_save)
