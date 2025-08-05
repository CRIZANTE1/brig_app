
import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials

EMPRESAS_SHEET = "Empresas"
DADOS_CALCULO_SHEET = "Dados_Calculo"
BRIGADISTAS_SHEET = "Brigadistas_Treinados"
RESULTADOS_SHEET = "Resultados_Salvos"


# --- Funções Globais com Cache ---

@st.cache_resource
def connect_to_gsheets():
    """
    Conecta ao Google Sheets usando as credenciais do st.secrets e retorna o cliente gspread.
    Usa @st.cache_resource para que a conexão seja criada apenas uma vez por sessão.
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
def get_sheet_data_as_df(_gspread_client, sheet_id: str, sheet_name: str) -> pd.DataFrame:
    """
    Busca dados de uma aba específica de uma planilha (identificada pelo sheet_id)
    e retorna como um DataFrame pandas. Esta função é cacheada.
    """
    try:
        spreadsheet = _gspread_client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        return df.dropna(how="all")
    except gspread.exceptions.SpreadsheetNotFound:
         st.error(f"Planilha com ID '{sheet_id}' não encontrada ou sem permissão. Verifique os secrets e o compartilhamento.")
         return pd.DataFrame()
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Aba '{sheet_name}' não encontrada na planilha. Por favor, verifique o nome da aba.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao ler dados da aba '{sheet_name}': {e}")
        return pd.DataFrame()



class GoogleSheetsHandler:
    """
    Classe que orquestra as operações com o Google Sheets, gerenciando as
    duas planilhas (dados e RAG) e utilizando as funções globais cacheadas.
    """
    def __init__(self):
        """Inicializa o handler obtendo a conexão cacheada e o ID da planilha de dados."""
        self.client = connect_to_gsheets()
        try:
            # Armazena o ID da planilha principal de DADOS
            self.spreadsheet_id = st.secrets["connections"]["gsheets"]["spreadsheet"]
        except KeyError:
            st.error("O ID da planilha de dados ('spreadsheet') não foi encontrado em [connections.gsheets] nos seus secrets.")
            st.stop()

    def get_data_as_df(self, sheet_name: str, rag_sheet_id: str = None) -> pd.DataFrame:
        """
        Busca dados de uma aba. Se `rag_sheet_id` for fornecido, usa esse ID para
        buscar na planilha RAG. Caso contrário, usa o ID da planilha de dados padrão.
        """
        target_sheet_id = rag_sheet_id if rag_sheet_id else self.spreadsheet_id
        return get_sheet_data_as_df(self.client, target_sheet_id, sheet_name)

    def get_company_list(self) -> list:
        """Retorna uma lista com a Razão Social de todas as empresas da planilha de dados."""
        df = self.get_data_as_df(EMPRESAS_SHEET)
        if not df.empty and 'Razao_Social' in df.columns:
            return df['Razao_Social'].tolist()
        return []

    def get_company_info(self, company_name: str) -> dict | None:
        empresas_df = self.get_data_as_df(EMPRESAS_SHEET)
        if empresas_df.empty or 'Razao_Social' not in empresas_df.columns: return None
        
        company_data = empresas_df[empresas_df['Razao_Social'] == company_name]
        
        if not company_data.empty:
            return company_data.iloc[0].to_dict()
        return None

    def get_calculation_data(self, company_name: str) -> dict | None:
        empresas_df = self.get_data_as_df(EMPRESAS_SHEET)
        dados_df = self.get_data_as_df(DADOS_CALCULO_SHEET)

        if empresas_df.empty or dados_df.empty or 'Razao_Social' not in empresas_df.columns: return None

        id_empresa_series = empresas_df.loc[empresas_df['Razao_Social'] == company_name, 'ID_Empresa']
        
        if not id_empresa_series.empty:
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

    def add_brigadistas_to_sheet(self, id_empresa: str, nomes: list, validade: str):
        """Adiciona uma lista de novos brigadistas à aba 'Brigadistas_Treinados'."""
        try:
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            worksheet = spreadsheet.worksheet(BRIGADISTAS_SHEET)
            
            rows_to_add = []
            for nome in nomes:
                new_row = [id_empresa, nome.strip(), "email@naoinformado.com", validade]
                rows_to_add.append(new_row)
            
            if rows_to_add:
                worksheet.append_rows(rows_to_add, value_input_option='USER_ENTERED')
                st.success(f"{len(rows_to_add)} brigadistas foram adicionados com sucesso à planilha!")
        except Exception as e:
            st.error(f"Ocorreu um erro ao tentar adicionar brigadistas à planilha: {e}")

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
        except Exception as e:
            st.error(f"Ocorreu um erro ao tentar salvar o resultado na planilha: {e}")
