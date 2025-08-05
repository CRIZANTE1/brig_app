# utils/google_sheets_handler.py

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# Nomes das abas (pode mover para config.py se preferir)
EMPRESAS_SHEET = "Empresas"
DADOS_CALCULO_SHEET = "Dados_Calculo"
BRIGADISTAS_SHEET = "Brigadistas_Treinados"
RESULTADOS_SHEET = "Resultados_Salvos"

class GoogleSheetsHandler:
    def __init__(self):
        try:
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            # Usa o método de conexão nativo do Streamlit, que é mais simples
            self.conn = st.connection("gsheets", type=gspread.GSpreadConnection)
            self.spreadsheet = self.conn.client
        except Exception as e:
            st.error(f"Falha ao conectar com o Google Sheets. Verifique a configuração em .streamlit/secrets.toml: {e}")
            st.stop()

    @st.cache_data(ttl=300) # Cache para não recarregar a cada interação
    def get_data_as_df(self, _self, sheet_name):
        """Busca dados de uma aba e retorna como DataFrame pandas."""
        try:
            worksheet = _self.conn.read(worksheet=sheet_name, usecols=None, ttl=5)
            return worksheet.dropna(how="all") # Remove linhas totalmente vazias
        except gspread.exceptions.WorksheetNotFound:
            st.error(f"Aba '{sheet_name}' não encontrada na planilha. Verifique o nome da aba.")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Erro ao ler a aba '{sheet_name}': {e}")
            return pd.DataFrame()

    def get_company_list(self):
        """Retorna uma lista de Razão Social da aba Empresas."""
        df = self.get_data_as_df(self, EMPRESAS_SHEET)
        if not df.empty and 'Razao_Social' in df.columns:
            return df['Razao_Social'].tolist()
        return []

    def get_calculation_data(self, company_name):
        """Busca os dados de cálculo para uma empresa específica."""
        empresas_df = self.get_data_as_df(self, EMPRESAS_SHEET)
        dados_df = self.get_data_as_df(self, DADOS_CALCULO_SHEET)

        if empresas_df.empty or dados_df.empty:
            return None

        # Encontra o ID da empresa pelo nome
        id_empresa = empresas_df.loc[empresas_df['Razao_Social'] == company_name, 'ID_Empresa'].iloc[0]

        if id_empresa:
            # Filtra os dados de cálculo pelo ID
            company_data = dados_df[dados_df['ID_Empresa'] == id_empresa]
            if not company_data.empty:
                return company_data.iloc[0].to_dict()
        return None

    def get_brigadistas_list(self, company_name):
        """Retorna a lista de brigadistas para uma empresa específica."""
        empresas_df = self.get_data_as_df(self, EMPRESAS_SHEET)
        brigadistas_df = self.get_data_as_df(self, BRIGADISTAS_SHEET)

        if empresas_df.empty or brigadistas_df.empty:
            return pd.DataFrame()
        
        id_empresa = empresas_df.loc[empresas_df['Razao_Social'] == company_name, 'ID_Empresa'].iloc[0]
        
        if id_empresa:
            return brigadistas_df[brigadistas_df['ID_Empresa'] == id_empresa]
        return pd.DataFrame()

    def save_calculation_result(self, data: dict):
        """Salva uma linha com o resultado do cálculo na aba de resultados."""
        try:
            # Obtém a planilha e a aba
            sheet = self.spreadsheet.open_by_key(st.secrets.connections.gsheets.spreadsheet)
            worksheet = sheet.worksheet(RESULTADOS_SHEET)

            # Prepara a linha de dados para ser inserida
            data_row = [
                data.get("id_empresa"),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                data.get("usuario"),
                data.get("divisao"),
                data.get("risco"),
                str(data.get("populacao_turnos")),
                data.get("total_calculado"),
                str(data.get("detalhe_turnos"))
            ]
            
            # Adiciona a linha na planilha
            worksheet.append_row(data_row, value_input_option='USER_ENTERED')
            st.success("Resultado salvo com sucesso na planilha!")

        except gspread.exceptions.WorksheetNotFound:
            st.error(f"Aba '{RESULTADOS_SHEET}' não encontrada. Crie-a para salvar os resultados.")
        except Exception as e:
            st.error(f"Erro ao salvar o resultado: {e}")