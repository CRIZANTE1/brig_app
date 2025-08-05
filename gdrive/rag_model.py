# utils/rag_model.py
import streamlit as st
import pandas as pd

# Em um cenário real, o RAG buscaria trechos da norma ABNT para justificar.
# Aqui, vamos simular esse comportamento com regras pré-definidas.
RISK_DESCRIPTIONS = {
    "M-2": "Risco associado ao armazenamento de líquidos e gases inflamáveis, como em parques de tanques. Requer atenção especial a vazamentos e controle de fontes de ignição.",
    "I-3": "Indústria de alto risco, possivelmente com processos químicos perigosos ou alta carga de incêndio. O tempo de resposta é crítico.",
    "J-4": "Depósitos com alta carga de incêndio. A principal preocupação é a rápida propagação do fogo e o colapso estrutural.",
    "D-2": "Agências bancárias, que apesar do risco moderado, possuem grande fluxo de pessoas e necessidade de evacuação ordenada."
}


def get_rag_recommendation(calc_data: dict, brigadistas_atuais: pd.DataFrame):
    """
    Simula um modelo RAG que atua como um consultor de segurança.
    
    Args:
        calc_data (dict): Dicionário com os inputs e resultados do cálculo oficial.
        brigadistas_atuais (pd.DataFrame): DataFrame com a lista de brigadistas já treinados.
    """
    
    # --- Extração de dados para a IA ---
    divisao = calc_data.get("division")
    risco = calc_data.get("risk")
    total_calculado = calc_data.get("total_brigade")
    necessidade_maior_turno = calc_data.get("maior_turno_necessidade")
    num_brigadistas_atuais = len(brigadistas_atuais)
    
    # --- Lógica da IA para gerar recomendações ---
    
    # 1. Análise de Déficit/Superávit
    deficit = total_calculado - num_brigadistas_atuais
    if deficit > 0:
        analise_quantitativa = f"🚨 **Alerta de Déficit:** A sua planta necessita de **{total_calculado}** brigadistas, mas atualmente possui apenas **{num_brigadistas_atuais}** registrados. É necessário treinar mais **{deficit}** colaborador(es) para atender à norma."
    else:
        analise_quantitativa = f"✅ **Conformidade Quantitativa:** O número de **{num_brigadistas_atuais}** brigadistas treinados atende ou supera o mínimo de **{total_calculado}** exigido pela norma."
        
    # 2. Recomendação de Margem de Segurança
    margem_sugerida = 2 if risco == "Alto" else 1
    total_recomendado = total_calculado + margem_sugerida
    
    # 3. Análise Qualitativa (baseada na Divisão)
    descricao_risco = RISK_DESCRIPTIONS.get(divisao, "Risco não mapeado para análise detalhada.")
    
    # --- Montagem do Texto Final ---
    recommendation = f"""
    ### Análise e Recomendações da IA

    **1. Diagnóstico da Norma:**
    O cálculo, baseado estritamente na ABNT NBR 14276, define uma necessidade mínima de **{total_calculado}** brigadistas no total, com um efetivo de pelo menos **{necessidade_maior_turno}** pessoas no turno de maior lotação.

    **2. Análise Quantitativa do Efetivo Atual:**
    {analise_quantitativa}

    **3. Recomendação Estratégica:**
    Para uma operação mais segura, a IA recomenda um efetivo total de **{total_recomendado} brigadistas**. Essa margem de **{margem_sugerida}** colaborador(es) acima do mínimo garante a cobertura em caso de faltas, férias ou múltiplas ocorrências simultâneas.

    **4. Análise de Risco Específico (Divisão {divisao}):**
    *"{descricao_risco}"*

    **Próximos Passos Sugeridos:**
    - **Ação Imediata:** Se houver déficit, planeje o treinamento de novos brigadistas.
    - **Auditoria:** Verifique a data de validade dos treinamentos dos brigadistas atuais na planilha.
    - **Prevenção:** Agende um simulado de emergência para os próximos 90 dias para testar a resposta da equipe.
    """

    return recommendation
