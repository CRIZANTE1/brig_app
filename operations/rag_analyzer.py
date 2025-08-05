import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai

@st.cache_data(ttl=3600) # Cache de 1 hora
def load_and_embed_rag_base(handler) -> tuple[pd.DataFrame, np.ndarray | None]:
    """
    Carrega a planilha RAG, gera embeddings para a coluna 'question' e armazena em cache.
    """
    try:
        df = handler.get_data_as_df("RAG_Knowledge_Base")

        if df.empty or "question" not in df.columns or "answer_chunk" not in df.columns:
            st.error("A aba 'RAG_Knowledge_Base' está vazia ou não contém as colunas 'question' e 'answer_chunk'.")
            return pd.DataFrame(), None

        with st.spinner(f"Indexando a base de conhecimento da IA ({len(df)} regras)..."):
            # Gera embeddings com base nas perguntas da base de conhecimento
            questions_to_embed = df["question"].tolist()
            result = genai.embed_content(
                model='models/text-embedding-004',
                content=questions_to_embed,
                task_type="RETRIEVAL_DOCUMENT" # Embedamos as perguntas como "documentos" para busca
            )
            embeddings = np.array(result['embedding'])
        
        st.success("Base de conhecimento da IA indexada!")
        return df, embeddings

    except Exception as e:
        st.error(f"Falha ao carregar a base de conhecimento RAG: {e}")
        st.warning("Verifique sua chave de API e se a aba 'RAG_Knowledge_Base' está correta.")
        return pd.DataFrame(), None

class RAGAnalyzer:
    def __init__(self, handler):
        self.rag_df, self.rag_embeddings = load_and_embed_rag_base(handler)

    def _find_relevant_chunks(self, query_text: str, top_k: int = 3) -> pd.DataFrame:
        """
        Encontra as regras mais relevantes na base de conhecimento usando busca semântica.
        Retorna um DataFrame com as linhas correspondentes.
        """
        if self.rag_df.empty or self.rag_embeddings is None or self.rag_embeddings.size == 0:
            return pd.DataFrame()
        try:
            query_embedding_result = genai.embed_content(
                model='models/text-embedding-004',
                content=[query_text],
                task_type="RETRIEVAL_QUERY" # A pergunta do usuário é uma "query"
            )
            query_embedding = np.array(query_embedding_result['embedding'])
            similarities = cosine_similarity(query_embedding, self.rag_embeddings)[0]
            top_k_indices = similarities.argsort()[-top_k:][::-1]
            return self.rag_df.iloc[top_k_indices]
        except Exception as e:
            st.warning(f"Erro durante a busca semântica na base de conhecimento: {e}")
            return pd.DataFrame()

    def get_contextual_analysis(self, ia_context: dict) -> str:
        """
        Gera uma análise contextual e fundamentada sobre o resultado do cálculo da brigada.
        """
        divisao = ia_context.get("division")
        risco = ia_context.get("risk")
        total_brigade = ia_context.get("total_brigade")
        populations = ia_context.get("populations", [])

        # 1. Cria uma consulta para a busca semântica
        query = f"Como é feito o cálculo de brigadistas para uma planta Divisão {divisao}, com Risco {risco} e uma população de {sum(populations)} pessoas distribuídas em turnos?"
        
        # 2. Busca os chunks de conhecimento mais relevantes
        relevant_rules_df = self._find_relevant_chunks(query)

        if relevant_rules_df.empty:
            return "Não foi possível encontrar regras relevantes na base de conhecimento para gerar uma análise detalhada."

        # 3. Formata o conhecimento encontrado para o prompt do LLM
        knowledge_context = ""
        for _, row in relevant_rules_df.iterrows():
            knowledge_context += (
                f"Fonte (Referência: {row['norma_referencia']}, Seção: {row['section_number']}):\n"
                f"Regra: {row['answer_chunk']}\n\n"
            )
        
        # 4. Monta o prompt final para o modelo generativo
        prompt = f"""
        **Persona:** Você é um Auditor de Segurança contra Incêndio. Sua tarefa é explicar o cálculo de brigadistas de forma clara e fundamentada.

        **Cenário:**
        - Divisão da Planta: {divisao}
        - Nível de Risco: {risco}
        - População por Turno: {populations}
        - Resultado do Cálculo (Total Mínimo): {total_brigade} brigadistas

        **Base de Conhecimento (Sua única fonte da verdade):**
        ---
        {knowledge_context}
        ---

        **Sua Tarefa (Seja preciso e didático):**
        1.  Inicie com um parágrafo de resumo sobre o resultado.
        2.  Explique o cálculo passo a passo, aplicando as regras da Base de Conhecimento aos números do cenário.
        3.  Para cada regra que você usar, **cite a referência e a seção** exatamente como aparecem na Base de Conhecimento.
        4.  Finalize com uma breve conclusão sobre a importância de seguir este dimensionamento.

        **Exemplo de Resposta:**
        "O cálculo resultou em um total de X brigadistas. Isso se deve à aplicação das seguintes regras:
        Para o turno com 28 pessoas, a norma (Referência: NBR 14276, Seção: Tabela A.1) exige que 'Todos' sejam brigadistas para os 10 primeiros... Além disso, para o excedente, a regra (Referência: NBR 14276, Seção: Tabela A.1, Nota 5) determina que..."
        """
        
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Erro ao gerar a análise da IA: {e}"
