
import streamlit as st
from utils.google_sheets_handler import GoogleSheetsHandler
from IA.rag_analyzer import RAGAnalyzer
import re
from operations.pdf_generator import generate_pdf_report_abnt




@st.dialog("Adicionar Nova Instalação")
def add_installation_dialog(handler: GoogleSheetsHandler):
    """
    Mostra um diálogo (modal) para o usuário preencher os dados de uma nova instalação.
    """
    # Usamos um formulário dentro do diálogo para agrupar os inputs.
    with st.form("new_installation_dialog_form"):
        st.subheader("Dados da Instalação")
        # Usamos chaves únicas para os widgets dentro do diálogo para evitar conflitos.
        new_id = st.text_input("ID da Empresa (Ex: RJO-02)", key="dialog_id")
        new_razao = st.text_input("Razão Social", key="dialog_razao")
        new_cnpj = st.text_input("CNPJ", key="dialog_cnpj")
        new_imovel = st.text_input("Nome do Imóvel/Instalação", key="dialog_imovel")

        st.subheader("Parâmetros de Cálculo")
        new_divisao = st.selectbox("Divisão", get_table_divisions(), key="dialog_div")
        new_risco = st.selectbox("Risco", ["Baixo", "Médio", "Alto"], key="dialog_risk")
        
        col1, col2, col3 = st.columns(3)
        with col1: new_t1 = st.number_input("Pop T1", 0, key="dialog_t1")
        with col2: new_t2 = st.number_input("Pop T2", 0, key="dialog_t2")
        with col3: new_t3 = st.number_input("Pop T3", 0, key="dialog_t3")

        submitted = st.form_submit_button("Salvar Nova Instalação")
        if submitted:
            # Validação simples dos campos obrigatórios.
            if not all([new_id, new_razao, new_imovel]):
                st.warning("Preencha pelo menos ID, Razão Social e Imóvel.")
            else:
                company_data = {
                    "ID_Empresa": new_id, "Razao_Social": new_razao,
                    "CNPJ": new_cnpj, "Imovel": new_imovel
                }
                calculation_data = {
                    "ID_Empresa": new_id, "Divisao": new_divisao, "Risco": new_risco,
                    "Pop_Turno1": new_t1, "Pop_Turno2": new_t2, "Pop_Turno3": new_t3
                }
                # Chama a função do handler para salvar os dados na planilha.
                if handler.add_new_installation(company_data, calculation_data):
                    # st.rerun() fecha o diálogo e recarrega a página inteira.
                    st.rerun()
                        
def is_valid_date_format(date_string: str) -> bool:
    """
    Verifica se a string de data fornecida está no formato DD/MM/AAAA.
    Retorna True se o formato for válido, False caso contrário.
    """
    if not isinstance(date_string, str):
        return False
    # Expressão regular para validar o formato DD/MM/AAAA
    pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")
    return pattern.match(date_string) is not None


def get_table_divisions():
    """Retorna uma lista fixa de divisões para o selectbox."""
    return ["M-2", "D-2", "I-1", "I-2", "I-3", "J-4", "C-1", "C-2"]

def render_sidebar(handler: GoogleSheetsHandler, company_list: list) -> str:
    """
    Desenha a barra lateral completa, incluindo seleção de empresa e botão de adicionar.
    Retorna o nome da empresa selecionada.
    """
    st.sidebar.header("Seleção da Empresa")
    
    col1, col2 = st.sidebar.columns([4, 1])
    
    with col1:
        # Usamos uma chave única para o selectbox que será usado em todo o app
        selected_company = st.selectbox(
            "Selecione a Empresa", 
            company_list, 
            key="global_company_selector", 
            label_visibility="collapsed"
        )
    
    with col2:
        if st.button("➕", help="Adicionar Nova Instalação"):
            add_installation_dialog(handler)

    if st.sidebar.button("Carregar Dados da Empresa", use_container_width=True):
        with st.spinner(f"Carregando dados para {selected_company}..."):
            st.session_state.sheet_data = handler.get_calculation_data(selected_company)
            st.session_state.company_info = handler.get_company_info(selected_company)
            # Limpa resultados antigos ao carregar nova empresa
            if 'last_result' in st.session_state:
                del st.session_state.last_result
            if 'generated_report' in st.session_state:
                del st.session_state.generated_report
            st.rerun()
            
    return selected_company


def show_brigade_management_page(handler: GoogleSheetsHandler, rag_analyzer: RAGAnalyzer, company_list: list):
    """
    Desenha e gerencia a interface da página de Gestão de Brigadistas.
    """
    st.title("Gestão de Brigadistas e Atestados")
    
    selected_company = render_sidebar(handler, company_list)

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
                st.json(extracted_data)
    elif not is_date_valid and validity_date:
        st.error("Formato de data inválido. Por favor, use DD/MM/AAAA.")


def show_calculator_page(handler: GoogleSheetsHandler, rag_analyzer: RAGAnalyzer, user_email: str, company_list: list):
    """
    Desenha e gerencia a interface da página principal de Cálculo de Brigada via IA.
    """
    st.title("Cálculo e Análise de Brigada de Incêndio por IA")
    
    st.sidebar.header("Seleção da Empresa")

    selected_company = render_sidebar(handler, company_list)
    
    if not company_list:
        st.error("A lista de empresas está vazia. Verifique a aba 'Empresas' da sua planilha.")
        return

    selected_company_name = st.sidebar.selectbox("Selecione a Empresa", company_list, key="calc_company_selector")

    if st.sidebar.button("Carregar Dados da Empresa"):
        with st.spinner(f"Carregando dados para {selected_company_name}..."):
            st.session_state.sheet_data = handler.get_calculation_data(selected_company_name)
            st.session_state.company_info = handler.get_company_info(selected_company_name)
            st.rerun() 
    
    default_values = st.session_state.get('sheet_data', {})
    company_info = st.session_state.get('company_info', {})
    
    if company_info:
        st.subheader(f"Analisando Instalação: {company_info.get('Imovel', 'N/A')}")
    
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
            initial_pops = [0, 0, 0]
            
        turn_populations = []
        cols_turnos = st.columns(len(initial_pops))
        for i, col in enumerate(cols_turnos):
            with col:
                pop = col.number_input(f"Pop. Turno {i+1}", min_value=0, step=1, value=initial_pops[i])
                turn_populations.append(pop)
                
        submit_button = st.form_submit_button(label='Calcular e Analisar com IA')

    if submit_button:
        ia_context = {
            "installation_info": company_info,
            "division": division,
            "risk": risk_level,
            "populations": turn_populations
        }
        with st.spinner("IA está consultando a norma e realizando o cálculo..."):
            calculation_result = rag_analyzer.calculate_brigade_with_rag(ia_context)
        
        if calculation_result:
            st.session_state.last_result = calculation_result
            st.session_state.last_inputs = { 
                "company_info": company_info,
                "division": division, 
                "risk": risk_level, 
                "populations": turn_populations
            }
        else:
            st.session_state.last_result = None
            st.error("Não foi possível obter o resultado do cálculo da IA.")

    if 'last_result' in st.session_state and st.session_state.last_result:
        result_json = st.session_state.last_result
        inputs = st.session_state.last_inputs
        instalacao = result_json.get("dados_da_instalacao", {})
        
        st.header(f"2. Resultado do Cálculo via IA para: {instalacao.get('imovel', 'N/A')}")
        
        with st.container(border=True):
            st.subheader("Resumo do Dimensionamento")
            resumo = result_json.get("resumo_final", {})
            total_geral = resumo.get("total_geral_brigadistas", "N/A")
            maior_turno = resumo.get("maior_turno_necessidade", "N/A")
            
            col1, col2 = st.columns(2)
            col1.metric("Total de Brigadistas (Soma dos Turnos)", total_geral)
            col2.metric("Efetivo Mínimo por Turno (Maior Turno)", maior_turno)

        with st.expander("Ver Detalhamento do Cálculo da IA (JSON)"):
            st.json(result_json)
        
        st.subheader("3. Ações e Relatórios")
        col_save, col_pdf = st.columns(2)

        with col_save:
            if st.button("Salvar Cálculo na Planilha", use_container_width=True):
                empresas_df = handler.get_data_as_df("Empresas")
                razao_social = instalacao.get("razao_social")

                id_empresa_series = empresas_df.loc[empresas_df['Razao_Social'] == razao_social, 'ID_Empresa']
                if not id_empresa_series.empty:
                    id_empresa = id_empresa_series.iloc[0]
                    
                    calculo_info = result_json.get("calculo_por_turno", [])
                    populacoes = [t.get("populacao") for t in calculo_info]
                    detalhes_turnos = [t.get("total_turno") for t in calculo_info]

                    data_to_save = { 
                        "id_empresa": id_empresa, 
                        "usuario": user_email, 
                        "divisao": inputs.get("division"), 
                        "risco": inputs.get("risk"), 
                        "populacao_turnos": str(populacoes),
                        "total_calculado": resumo.get("total_geral_brigadistas"), 
                        "detalhe_turnos": str(detalhes_turnos)
                    }
                    handler.save_calculation_result(data_to_save)
                else:
                    st.error(f"Não foi possível encontrar o ID da empresa para '{razao_social}'. Resultado não salvo.")
        
        with col_pdf:
            pdf_bytes = generate_pdf_report_abnt(result_json)
            if pdf_bytes:
                st.download_button(
                    label="Baixar Relatório ABNT (PDF)",
                    data=pdf_bytes,
                    file_name=f"Relatorio_ABNT_Brigada_{instalacao.get('imovel', 'local').replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
