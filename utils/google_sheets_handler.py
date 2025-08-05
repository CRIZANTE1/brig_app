import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials

# --- Nomes das Abas ---
# A constante ADMIN_SHEET_NAME foi removida.
EMPRESAS_SHEET = "Empresas"
DADOS_CALCULO_SHEET = "Dados_Calculo"
BRIGADISTAS_SHEET = "Brigadistas_Treinados"
RESULTADOS_SHEET = "Resultados_Salvos"


# --- Funções Globais com Cache ---

@st.cache_resource
def connect_to_gsheets():
    """
    Conecta ao Google Sheets usando as credenciais do st.secrets e retorna o cliente gspread.
    Usa @st.cache_resource porque a conexão é um "recurso" que não deve ser recriado a cada interação.
    """
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds_dict = st.secrets["connections"]["gsheets"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Falha fatal ao conectar com o Google Sheets: {e}. Verifique a configuração em .streamlit/secrets.toml.")
        st.stop()


@st.cache_data(ttl=300) # Cache de 5 minutos para os dados
def get_sheet_data_as_df(_gspread_client, spreadsheet_id: str, sheet_name: str) -> pd.DataFrame:
    """
    Busca dados de uma aba específica e retorna como um DataFrame pandas.
    Esta função é global para que o @st.cache_data funcione corretamente.
    """
    try:
        spreadsheet = _gspread_client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        return df.dropna(how="all")
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Aba '{sheet_name}' não encontrada na planilha. Por favor, verifique o nome da aba.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao ler dados da aba '{sheet_name}': {e}")
        return pd.DataFrame()


# --- Classe Handler ---

class GoogleSheetsHandler:
    """
    Uma classe que orquestra as operações com o Google Sheets,
    utilizando as funções globais cacheadas para eficiência.
    """
    def __init__(self):
        """Inicializa o handler obtendo a conexão cacheada e o ID da planilha."""
        self.client = connect_to_gsheets()
        try:
            self.spreadsheet_id = st.secrets["connections"]["gsheets"]["spreadsheet"]
        except KeyError:
            st.error("O ID da planilha ('spreadsheet') não foi encontrado em [connections.gsheets] nos seus secrets.")
            st.stop()

    def get_data_as_df(self, sheet_name: str) -> pd.DataFrame:
        """
        Método de conveniência que chama a função global cacheada para obter os dados.
        """
        return get_sheet_data_as_df(self.client, self.spreadsheet_id, sheet_name)

    def get_company_list(self) -> list:
        """Retorna uma lista com a Razão Social de todas as empresas."""
        df = self.get_data_as_df(EMPRESAS_SHEET)
        if not df.empty and 'Razao_Social' in df.columns:
            return df['Razao_Social'].tolist()
        return []

    def get_calculation_data(self, company_name: str) -> dict | None:
        """Busca os dados de cálculo para uma empresa específica pelo nome."""
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
        """Retorna um DataFrame com a lista de brigadistas de uma empresa específica."""
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
        """Salva uma nova linha com o resultado do cálculo na aba de resultados."""
        try:
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            worksheet = spreadsheet.worksheet(RESULTADOS_SHEET)
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
            worksheet.append_row(data_row, value_input_option='USER_ENTERED')
            st.success("Resultado do cálculo salvo com sucesso na planilha!")
        except gspread.exceptions.WorksheetNotFound:
            st.error(f"Aba de resultados ('{RESULTADOS_SHEET}') não foi encontrada. Por favor, crie-a para salvar o histórico.")
        except Exception as e:
            st.error(f"Ocorreu um erro ao tentar salvar o resultado na planilha: {e}")
