import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
import json
from .prompts import get_pdf_extraction_prompt

def _load_and_embed_rag_base(handler, rag_sheet_id: str) -> tuple[pd.DataFrame, np.ndarray | None]:
    """
    Carrega a planilha RAG, gera embeddings para a coluna 'question'.
    """
    if not rag_sheet_id or rag_sheet_id == "not_defined":
        st.error("O ID da planilha RAG ('rag_sheet_id') não está definido nos secrets.")
        return pd.DataFrame(), None
        
    try:
        # Reutiliza a função de leitura de dados que já é cacheada pelo handler.
        # Passa o nome da aba diretamente.
        df = handler.get_data_as_df(sheet_name="RAG_Knowledge_Base", rag_sheet_id=rag_sheet_id)

        if df.empty or "question" not in df.columns or "answer_chunk" not in df.columns:
            st.error("A aba 'RAG_Knowledge_Base' está vazia ou não contém as colunas 'question' e 'answer_chunk'.")
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
        st.error(f"Falha ao carregar a base de conhecimento RAG (ID: {rag_sheet_id}): {e}")
        return pd.DataFrame(), None

class RAGAnalyzer:
    def __init__(self, handler, rag_sheet_id: str):
        """
        Inicializa o analisador RAG, configurando o modelo Gemini e
        carregando/indexando a base de conhecimento da planilha.
        """
        try:
            api_key = st.secrets["general"]["GOOGLE_API_KEY"]
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-pro')
        except Exception as e:
            st.error(f"Falha ao configurar o modelo Gemini: {e}")
            st.stop()
        
        # A chamada para carregar a base de conhecimento agora é um método interno
        self.rag_df, self.rag_embeddings = _load_and_embed_rag_base(handler, rag_sheet_id)

    def _find_relevant_chunks(self, query_text: str, top_k: int = 3) -> pd.DataFrame:
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
            st.warning(f"Erro durante a busca semântica: {e}")
            return pd.DataFrame()

    def get_contextual_analysis(self, ia_context: dict) -> str:
        """Gera uma análise contextual e fundamentada sobre o resultado do cálculo da brigada."""
        divisao = ia_context.get("division")
        risco = ia_context.get("risk")
        total_brigade = ia_context.get("total_brigade")
        populations = ia_context.get("populations", [])

        query = f"Como é feito o cálculo de brigadistas para uma planta Divisão {divisao}, Risco {risco} e população de {sum(populations)} pessoas?"
        relevant_rules_df = self._find_relevant_chunks(query)

        if relevant_rules_df.empty:
            return "Não foi possível encontrar regras relevantes na base de conhecimento para gerar uma análise."

        knowledge_context = ""
        for _, row in relevant_rules_df.iterrows():
            knowledge_context += f"Fonte (Ref: {row['norma_referencia']}, Seção: {row['section_number']}):\nRegra: {row['answer_chunk']}\n\n"
        
        prompt = f"""
        **Persona:** Você é um Auditor de Segurança contra Incêndio.
        **Cenário:** Divisão={divisao}, Risco={risco}, População por Turno={populations}, Total Mínimo={total_brigade} brigadistas.
        **Base de Conhecimento:**\n---\n{knowledge_context}---\n
        **Sua Tarefa:** Com base estritamente na Base de Conhecimento, explique o cálculo passo a passo, citando as fontes para cada regra aplicada.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Erro ao gerar a análise da IA: {e}"

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
