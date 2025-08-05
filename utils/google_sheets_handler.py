import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# Nomes das abas centralizados aqui
EMPRESAS_SHEET = "Empresas"
DADOS_CALCULO_SHEET = "Dados_Calculo"
BRIGADISTAS_SHEET = "Brigadistas_Treinados"
RESULTADOS_SHEET = "Resultados_Salvos"
ADMIN_SHEET_NAME = "adm"  # Aba para controle de acesso

class GoogleSheetsHandler:
    def __init__(self):
        try:
            self.conn = st.connection("gsheets", type=gspread.GSpreadConnection)
        except Exception as e:
            st.error(f"Falha ao conectar com o Google Sheets. Verifique a configuração em .streamlit/secrets.toml: {e}")
            st.stop()

    @st.cache_data(ttl=300)
    def get_data_as_df(self, sheet_name):
        """Busca dados de uma aba e retorna como DataFrame pandas."""
        try:
            worksheet = self.conn.read(worksheet=sheet_name, usecols=None, ttl=5)
            return worksheet.dropna(how="all")
        except gspread.exceptions.WorksheetNotFound:
            st.error(f"Aba '{sheet_name}' não encontrada na planilha. Verifique o nome da aba.")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Erro ao ler a aba '{sheet_name}': {e}")
            return pd.DataFrame()

    def get_company_list(self):
        df = self.get_data_as_df(EMPRESAS_SHEET)
        if not df.empty and 'Razao_Social' in df.columns:
            return df['Razao_Social'].tolist()
        return []

    def get_calculation_data(self, company_name):
        empresas_df = self.get_data_as_df(EMPRESAS_SHEET)
        dados_df = self.get_data_as_df(DADOS_CALCULO_SHEET)

        if empresas_df.empty or dados_df.empty or 'Razao_Social' not in empresas_df.columns:
            return None

        # Encontra o ID da empresa pelo nome
        id_empresa_series = empresas_df.loc[empresas_df['Razao_Social'] == company_name, 'ID_Empresa']
        if id_empresa_series.empty:
            return None
        
        id_empresa = id_empresa_series.iloc[0]
        company_data = dados_df[dados_df['ID_Empresa'] == id_empresa]
        if not company_data.empty:
            return company_data.iloc[0].to_dict()
        return None

    def get_brigadistas_list(self, company_name):
        empresas_df = self.get_data_as_df(EMPRESAS_SHEET)
        brigadistas_df = self.get_data_as_df(BRIGADISTAS_SHEET)

        if empresas_df.empty or brigadistas_df.empty:
            return pd.DataFrame()
        
        id_empresa_series = empresas_df.loc[empresas_df['Razao_Social'] == company_name, 'ID_Empresa']
        if id_empresa_series.empty:
            return pd.DataFrame()

        id_empresa = id_empresa_series.iloc[0]
        return brigadistas_df[brigadistas_df['ID_Empresa'] == id_empresa]

    def save_calculation_result(self, data: dict):
        try:
            sheet = self.conn.client.open_by_key(st.secrets.connections.gsheets.spreadsheet)
            worksheet = sheet.worksheet(RESULTADOS_SHEET)
            data_row = [
                data.get("id_empresa"), datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                data.get("usuario"), data.get("divisao"), data.get("risco"),
                str(data.get("populacao_turnos")), data.get("total_calculado"),
                str(data.get("detalhe_turnos"))
            ]
            worksheet.append_row(data_row, value_input_option='USER_ENTERED')
            st.success("Resultado salvo com sucesso na planilha!")
        except gspread.exceptions.WorksheetNotFound:
            st.error(f"Aba '{RESULTADOS_SHEET}' não encontrada. Crie-a para salvar os resultados.")
        except Exception as e:
            st.error(f"Erro ao salvar o resultado: {e}")
