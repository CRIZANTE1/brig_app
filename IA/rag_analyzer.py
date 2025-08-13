import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import json
from .prompts import get_pdf_extraction_prompt, get_brigade_calculation_prompt, get_report_generation_prompt

@st.cache_data(ttl=3600) # Cache de 1 hora para a base de conhecimento indexada
def load_and_embed_rag_base(_gspread_client, rag_sheet_id: str) -> tuple[pd.DataFrame, np.ndarray | None]:
    """
    Carrega a planilha RAG pelo ID fornecido, gera embeddings para a coluna 'question'
    e armazena os resultados em cache.
    """
    # Validação inicial do ID da planilha
    if not rag_sheet_id or rag_sheet_id == "not_defined":
        st.error("O ID da planilha RAG ('rag_sheet_id') não está definido nos secrets.")
        return pd.DataFrame(), None
        
    try:
        # Abre a planilha RAG e lê a aba de conhecimento
        spreadsheet = _gspread_client.open_by_key(rag_sheet_id)
        worksheet = spreadsheet.worksheet("RAG_Knowledge_Base")
        df = pd.DataFrame(worksheet.get_all_records())

        # Validação das colunas essenciais
        required_columns = ["question", "answer_chunk", "norma_referencia", "section_number"]
        if df.empty or not all(col in df.columns for col in required_columns):
            st.error(f"A aba 'RAG_Knowledge_Base' está vazia ou não contém todas as colunas necessárias: {required_columns}.")
            return pd.DataFrame(), None
        
        with st.spinner(f"Indexando a base de conhecimento da IA ({len(df)} regras)..."):
            questions_to_embed = df["question"].tolist()
            result = genai.embed_content(
                model='models/text-embedding-004',
                content=questions_to_embed,
                task_type="RETRIEVAL_DOCUMENT"
            )
            embeddings = np.array(result['embedding'])
        st.success("Base de conhecimento da IA indexada!")
        return df, embeddings
    except Exception as e:
        st.error(f"Falha ao carregar e indexar a base de conhecimento RAG (ID: {rag_sheet_id}): {e}")
        return pd.DataFrame(), None

class RAGAnalyzer:
    def __init__(self, gspread_client, rag_sheet_id: str):
        """
        Inicializa o analisador RAG.
        - Configura o modelo Gemini.
        - Carrega e indexa a base de conhecimento da planilha, usando a função cacheada.
        """
        try:
            api_key = st.secrets["general"]["GOOGLE_API_KEY"]
            genai.configure(api_key=api_key)
            self.safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            self.model = genai.GenerativeModel('gemini-2.5-pro')
        except Exception as e:
            st.error(f"Falha ao configurar o modelo Gemini: {e}")
            st.stop()
        
        # Chama a função global cacheada, passando os argumentos "hashable"
        self.rag_df, self.rag_embeddings = load_and_embed_rag_base(gspread_client, rag_sheet_id)

    def _find_relevant_chunks(self, query_text: str, top_k: int = 5) -> pd.DataFrame:
        """Encontra as regras mais relevantes na base de conhecimento usando busca semântica."""
        if self.rag_df.empty or self.rag_embeddings is None or self.rag_embeddings.size == 0:
            return pd.DataFrame()
        try:
            query_embedding_result = genai.embed_content(
                model='models/text-embedding-004',
                content=[query_text],
                task_type="RETRIEVAL_QUERY"
            )
            query_embedding = np.array(query_embedding_result['embedding'])
            similarities = cosine_similarity(query_embedding, self.rag_embeddings)[0]
            top_k_indices = similarities.argsort()[-top_k:][::-1]
            return self.rag_df.iloc[top_k_indices]
        except Exception as e:
            st.warning(f"Erro durante a busca semântica na base de conhecimento: {e}")
            return pd.DataFrame()

    def calculate_brigade_with_rag(self, ia_context: dict) -> dict | None:
        """Usa a IA e a base de conhecimento RAG para executar o cálculo da brigada e retornar um JSON."""
        divisao = ia_context.get("division")
        risco = ia_context.get("risk")

        query = f"Regras de cálculo de brigada para Divisão {divisao} e Risco {risco}, incluindo regras base e de acréscimo."
        
        relevant_rules_df = self._find_relevant_chunks(query, top_k=5)
        if relevant_rules_df.empty:
            st.error("Não foram encontradas regras suficientes na base de conhecimento para realizar o cálculo.")
            return None

        knowledge_context = ""
        for _, row in relevant_rules_df.iterrows():
            # Usa .get() para acesso seguro, evitando KeyErrors se a planilha estiver mal formatada
            ref = row.get('norma_referencia', 'N/A')
            sec = row.get('section_number', 'N/A')
            ans = row.get('answer_chunk', 'Conteúdo indisponível.')
            knowledge_context += f"- {ans} (Fonte: {ref}, {sec})\n"
        
        prompt = get_brigade_calculation_prompt(ia_context, knowledge_context)
        
        try:
            generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
            response = self.model.generate_content(prompt, generation_config=generation_config)
            
            return json.loads(response.text)
        except json.JSONDecodeError:
            st.error("A IA não retornou um JSON válido para o cálculo. Verifique a resposta abaixo.")
            st.text_area("Resposta Bruta da IA:", response.text if 'response' in locals() else "Nenhuma resposta recebida.", height=200)
            return None
        except Exception as e:
            st.error(f"Erro ao executar o cálculo com a IA: {e}")
            return None

    def extract_brigadistas_from_pdf(self, pdf_file) -> dict:
        """Usa o Gemini para extrair uma lista de nomes de um PDF."""
        try:
            prompt = get_pdf_extraction_prompt()
            pdf_bytes = pdf_file.read()
            pdf_part = {"mime_type": "application/pdf", "data": pdf_bytes}
            generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
            
            response = self.model.generate_content([prompt, pdf_part], generation_config=generation_config)
            return json.loads(response.text)
        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o PDF com a IA: {e}")
            return {"nomes": []}

    def generate_full_report(self, calculation_json: dict) -> str:
        """
        Usa a IA para gerar um relatório técnico completo em Markdown com base no
        resultado do cálculo (em formato JSON).
        """
        if not calculation_json:
            return "Erro: Dados de cálculo não fornecidos para gerar o relatório."
            
        try:
            # Cria o prompt usando o JSON do cálculo
            prompt = get_report_generation_prompt(calculation_json)
            
            # Chama a IA para gerar o texto do relatório
            response = self.model.generate_content(prompt)
            
            return response.text
        except Exception as e:
            return f"**Erro ao gerar o relatório:**\n\n{str(e)}"
