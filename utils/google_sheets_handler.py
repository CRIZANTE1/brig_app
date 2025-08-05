import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials

# Nomes das abas
EMPRESAS_SHEET = "Empresas"
DADOS_CALCULO_SHEET = "Dados_Calculo"
BRIGADISTAS_SHEET = "Brigadistas_Treinados"
RESULTADOS_SHEET = "Resultados_Salvos"
ADMIN_SHEET_NAME = "adm"

# Usamos cache para a conexão, para não re-autenticar a cada interação
@st.cache_resource
def connect_to_gsheets():
    """
    Conecta ao Google Sheets usando as credenciais do st.secrets (método manual).
    """
    try:
        # Define os escopos de permissão necessários
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        
        # Pega as credenciais diretamente do secrets.toml, da seção [connections.gsheets]
        creds_dict = st.secrets["connections"]["gsheets"]
        
        # Cria o objeto de credenciais a partir do dicionário
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        
        # Autoriza e retorna o cliente gspread
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Falha ao conectar com o Google Sheets. Verifique a configuração em .streamlit/secrets.toml: {e}")
        st.stop() # Para a execução do app se a conexão falhar

class GoogleSheetsHandler:
    def __init__(self):
        """Inicializa o handler conectando ao Google Sheets."""
        self.client = connect_to_gsheets()
        try:
            # Abre a planilha pelo ID fornecido nos secrets
            self.spreadsheet = self.client.open_by_key(st.secrets["connections"]["gsheets"]["spreadsheet"])
        except gspread.exceptions.SpreadsheetNotFound:
            st.error("Planilha não encontrada! Verifique o ID da planilha ('spreadsheet') em secrets.toml.")
            st.stop()
        except Exception as e:
            st.error(f"Erro ao abrir a planilha: {e}")
            st.stop()

    @st.cache_data(ttl=300) # Cache para os dados por 5 minutos
    def get_data_as_df(self, sheet_name: str) -> pd.DataFrame:
        """Busca dados de uma aba e retorna como DataFrame pandas."""
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            records = worksheet.get_all_records() # get_all_records() é ótimo para converter para DF
            df = pd.DataFrame(records)
            return df.dropna(how="all")
        except gspread.exceptions.WorksheetNotFound:
            st.error(f"Aba '{sheet_name}' não encontrada na planilha. Verifique o nome da aba.")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Erro ao ler a aba '{sheet_name}': {e}")
            return pd.DataFrame()

    def get_company_list(self) -> list:
        """Retorna uma lista de Razão Social da aba Empresas."""
        df = self.get_data_as_df(EMPRESAS_SHEET)
        if not df.empty and 'Razao_Social' in df.columns:
            return df['Razao_Social'].tolist()
        return []

    def get_calculation_data(self, company_name: str) -> dict | None:
        """Busca os dados de cálculo para uma empresa específica."""
        empresas_df = self.get_data_as_df(EMPRESAS_SHEET)
        dados_df = self.get_data_as_df(DADOS_CALCULO_SHEET)

        if empresas_df.empty or dados_df.empty or 'Razao_Social' not in empresas_df.columns:
            return None

        id_empresa_series = empresas_df.loc[empresas_df['Razao_Social'] == company_name, 'ID_Empresa']
        if id_empresa_series.empty:
            return None
        
        id_empresa = id_empresa_series.iloc[0]
        company_data = dados_df[dados_df['ID_Empresa'] == id_empresa]
        if not company_data.empty:
            return company_data.iloc[0].to_dict()
        return None

    def get_brigadistas_list(self, company_name: str) -> pd.DataFrame:
        """Retorna a lista de brigadistas para uma empresa específica."""
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
        """Salva uma linha com o resultado do cálculo na aba de resultados."""
        try:
            worksheet = self.spreadsheet.worksheet(RESULTADOS_SHEET)
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
