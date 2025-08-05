import streamlit as st
from utils.google_sheets_handler import GoogleSheetsHandler
from IA.ai_operations import AIOperations
import re

def is_valid_date_format(date_string: str) -> bool:
    """Verifica se a string está no formato DD/MM/AAAA."""
    # Expressão regular para o formato DD/MM/AAAA
    pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")
    return pattern.match(date_string) is not None

def show_page(handler: GoogleSheetsHandler, ai_operator: AIOperations):
    """
    Desenha a página para gerenciamento de brigadistas, incluindo o upload de atestados.
    Lê a lista de empresas do st.session_state.
    """
    st.title("Gestão de Brigadistas e Atestados")
    
    # --- Carregamento de Dados da Sessão ---
    # Lê a lista de empresas diretamente do session_state, que foi carregada pelo app.py
    company_list = st.session_state.get('company_list', [])

    # Barreira de segurança: se a lista de empresas não estiver na sessão, exibe um erro.
    if not company_list:
        st.error("Falha ao carregar a lista de empresas da sessão.")
        st.warning(
            "Retorne à página principal ou recarregue a aplicação. Se o erro persistir, verifique os seguintes pontos:\n"
            "1. A aba 'Empresas' existe e não está vazia.\n"
            "2. A primeira linha da aba 'Empresas' contém a coluna 'Razao_Social'.\n"
            "3. O e-mail da conta de serviço tem permissão de 'Editor' na planilha."
        )
        return

    # O resto da página só é renderizado se a lista de empresas for carregada com sucesso.
    st.markdown("Use esta página para adicionar novos brigadistas à sua planilha a partir de um atestado de treinamento em PDF.")
    
    with st.container(border=True):
        st.subheader("1. Selecione a Empresa e o Atestado")

        selected_company = st.selectbox("Para qual empresa este atestado se aplica?", company_list)
        
        validity_date = st.text_input("Data de Validade do Treinamento (formato DD/MM/AAAA)", placeholder="Ex: 31/12/2025")

        uploaded_file = st.file_uploader(
            "Carregue o atestado de brigada em formato PDF",
            type="pdf",
            accept_multiple_files=False
        )

    # Verifica se a data está no formato correto antes de habilitar o botão
    is_date_valid = is_valid_date_format(validity_date)
    
    if st.button("Extrair e Adicionar Brigadistas com IA", disabled=(not uploaded_file or not selected_company or not is_date_valid)):
        if uploaded_file and selected_company and is_date_valid:
            with st.spinner("IA analisando o atestado... Este processo pode levar um momento."):
                extracted_data = ai_operator.extract_brigadistas_from_pdf(uploaded_file)

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
                    st.json(extracted_data) # Mostra o que a IA retornou para debug
        elif not is_date_valid:
            st.error("Formato de data inválido. Por favor, use DD/MM/AAAA.")
