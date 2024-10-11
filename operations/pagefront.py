import streamlit as st
from operations.app_brigcal import calcula_brigada, emitir_relatorio, save_to_pdf, ler_json, CAMINHO_JSON
import json
import os

def pagefront():
    st.title('Cálculo de Brigadistas')

    # Carregar dados do JSON usando a função importada
    dados_json = ler_json()

    # Inputs
    col1, col2 = st.columns(2)

    with col1:
        # Usar a divisão do JSON
        divisao = st.selectbox('Divisão', [dados_json['numeros_utilizados']['divisao']])
        
        # Obter níveis de risco do JSON e criar um dicionário de mapeamento
        niveis_risco = list(dados_json['constantes_por_nivel_de_risco'].keys())
        risco_formatado = {
            'risco_baixo': 'Baixo',
            'risco_medio': 'Médio',
            'risco_alto': 'Alto'
        }
        risco_opcoes = [risco_formatado.get(r, r.capitalize()) for r in niveis_risco]
        
        risco_selecionado = st.selectbox('Grau de Risco', risco_opcoes)
        # Converter de volta para o formato original
        risco = next(key for key, value in risco_formatado.items() if value == risco_selecionado)

    with col2:
        pessoas = st.selectbox('Número de Funcionários', dados_json['opcoes_funcionarios'])
        turnos = st.number_input('Número de Turnos', min_value=1, value=dados_json['numeros_utilizados']['turnos'])
        imovel = st.selectbox('Imóvel', [dados_json['local_calculo_brigada']['imovel']])

    if st.button('Calcular Brigadistas'):
        # Atualizar dados_json com os inputs do usuário
        dados_json['numeros_utilizados']['divisao'] = divisao
        dados_json['numeros_utilizados']['risco'] = risco
        dados_json['numeros_utilizados']['pessoas'] = pessoas
        dados_json['numeros_utilizados']['turnos'] = turnos

        # Salvar as alterações no arquivo JSON
        with open(CAMINHO_JSON, 'w', encoding='utf-8') as f:
            json.dump(dados_json, f, ensure_ascii=False, indent=2)

        # Calcular brigadistas
        brigadistas_necessarios = calcula_brigada()

        # Exibir resultado
        st.success(f'Número de brigadistas necessários: {brigadistas_necessarios}')

        # Armazenar os resultados na sessão do Streamlit
        st.session_state['brigadistas_necessarios'] = brigadistas_necessarios

    # Botão para gerar e baixar PDF na barra lateral
    if st.sidebar.button('Gerar e Baixar Relatório PDF'):
        if 'brigadistas_necessarios' in st.session_state:
            # Gerar relatório
            relatorio_text = emitir_relatorio(st.session_state['brigadistas_necessarios'])

            # Gerar e oferecer download do PDF
            pdf_path = 'relatorio_brigada.pdf'
            save_to_pdf(relatorio_text, pdf_path)

            with open(pdf_path, "rb") as pdf_file:
                PDFbyte = pdf_file.read()

            st.sidebar.download_button(
                label="Baixar Relatório PDF",
                data=PDFbyte,
                file_name="relatorio_brigada.pdf",
                mime='application/octet-stream'
            )

            # Remover o arquivo PDF após o download
            os.remove(pdf_path)
        else:
            st.sidebar.warning("Por favor, calcule os brigadistas primeiro.")

def pagina_sobre():
    st.title("Sobre o Cálculo de Brigadistas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("Dados Relevantes")
        st.write("Divisão: M-2 (líquidos inflamáveis, gás inflamável ou combustível).")
        st.write("Risco: Alto.")
        st.write("Número de pessoas: 51.")
        st.write("Número de turnos: 3.")
        
        st.header("Constantes por Nível de Risco")
        st.write("Risco baixo: 20.")
        st.write("Risco médio: 15.")
        st.write("Risco alto: 10 (número de pessoas para cada brigadista adicional).")
    
    with col2:
        st.header("Passo a Passo do Cálculo")
        
        st.subheader("1. Identificação da Base de Brigadistas")
        st.write("Risco alto: base de 8 brigadistas, grupo de 10 pessoas.")
        
        st.subheader("2. Cálculo de Brigadistas")
        st.code("Para 51 pessoas: 8 + ceil((51 - 10) / 10) = 13")
        
        st.subheader("3. Cálculo por Turno")
        st.code("17 pessoas por turno: 8 + ceil((17 - 10) / 10) = 9")
        st.code("Total para 3 turnos: 9 * 3 = 27")
        
        st.subheader("Resultado Final")
        st.code("max(13, 27) = 27 brigadistas necessários")

    st.header("Referências Normativas")
    st.write('''
    - SÃO PAULO (Estado). Instrução Técnica nº 17/2019 – Brigada de Incêndio.
    - ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. NBR 14277: Instalações e equipamentos para treinamento de combate a incêndio.
    - SÃO PAULO (Estado). Decreto Estadual nº 63.911, de 10 de dezembro de 2018.
    - ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. NBR 18801: Gestão de emergências.
    - ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. NBR ISO 45001: Sistemas de gestão de segurança e saúde ocupacional.
    ''')
    
    st.caption('Desenvolvido por: CRISTIAN FERREIRA CARLOS, cristiancarlos@vibraenergia.com.br')
