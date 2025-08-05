# IA/ai_operations.py

import streamlit as st
import google.generativeai as genai
import logging

class AIOperations:
    def __init__(self):
        """
        Inicializa o modelo de IA e configura a API Key.
        """
        try:
            # ALTERAÇÃO AQUI: Procura a chave dentro da seção [general]
            api_key = st.secrets["general"]["GOOGLE_API_KEY"]
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
            logging.info("Modelo de IA inicializado com sucesso.")
            
        except (KeyError, AttributeError):
            st.error("Chave 'GOOGLE_API_KEY' não encontrada na seção [general] dos secrets. Por favor, configure-a.")
            logging.error("API Key do Google não encontrada em [general].")
            st.stop()
        except Exception as e:
            st.error(f"Erro ao inicializar o modelo de IA: {e}")
            logging.error(f"Erro na inicialização da IA: {e}")
            st.stop()

    def get_consultant_analysis(self, prompt: str) -> str:
        """
        Envia um prompt para o modelo Gemini e retorna a análise textual.
        """
        try:
            with st.spinner("IA processando a análise consultiva..."):
                response = self.model.generate_content(prompt)
                return response.text
        except Exception as e:
            error_message = f"Ocorreu um erro na chamada à API de IA: {e}"
            logging.error(error_message)
            st.error(error_message)
            return "Não foi possível gerar a análise da IA devido a um erro."
