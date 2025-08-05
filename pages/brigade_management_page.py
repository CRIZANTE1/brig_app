import streamlit as st
from utils.google_sheets_handler import GoogleSheetsHandler
from IA.ai_operations import AIOperations

def show_page(handler: GoogleSheetsHandler, ai_operator: AIOperations):
    """
    Desenha a página para gerenciamento de brigadistas, incluindo o upload de atestados.
    """
    st.title("Gestão de Brigadistas e Atestados")
    st.markdown("Use esta página para adicionar novos brigadistas à sua planilha a partir de um atestado de treinamento em PDF.")

    with st.container(border=True):
        st.subheader("1. Selecione a Empresa e o Atestado")

        company_list = handler.get_company_list()
        if not company_list:
            st.warning("Nenhuma empresa cadastrada. Adicione empresas na aba 'Empresas' da sua planilha.")
            return

        selected_company = st.selectbox("Para qual empresa este atestado se aplica?", company_list)
        
        # O usuário informa a data de validade, que é mais confiável do que a IA extrair.
        validity_date = st.text_input("Data de Validade do Treinamento (formato DD/MM/AAAA)", placeholder="Ex: 31/12/2025")

        # Uploader para o arquivo PDF
        uploaded_file = st.file_uploader(
            "Carregue o atestado de brigada em formato PDF",
            type="pdf",
            accept_multiple_files=False
        )

    if st.button("Extrair e Adicionar Brigadistas com IA", disabled=(not uploaded_file or not selected_company or not validity_date)):
        if uploaded_file and selected_company and validity_date:
            with st.spinner("IA analisando o atestado... Este processo pode levar um momento."):
                # Chama a nova função da IA para extrair os nomes
                extracted_data = ai_operator.extract_brigadistas_from_pdf(uploaded_file)

            if extracted_data and "nomes" in extracted_data and extracted_data["nomes"]:
                nomes = extracted_data["nomes"]
                st.success(f"IA extraiu {len(nomes)} nomes do atestado com sucesso!")
                
                with st.expander("Ver nomes extraídos antes de salvar"):
                    st.write(nomes)

                # Chama a nova função do handler para salvar os dados na planilha
                with st.spinner("Adicionando brigadistas à planilha..."):
                    empresas_df = handler.get_data_as_df("Empresas")
                    id_empresa = empresas_df.loc[empresas_df['Razao_Social'] == selected_company, 'ID_Empresa'].iloc[0]
                    
                    handler.add_brigadistas_to_sheet(id_empresa, nomes, validity_date)

            else:
                st.error("A IA não conseguiu extrair uma lista de nomes válida do documento. Verifique o PDF ou tente novamente.")
                st.json(extracted_data) # Mostra o que a IA retornou para debug
