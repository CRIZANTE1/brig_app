# IA/prompts.py

import pandas as pd

def get_brigade_analysis_prompt(calc_data: dict, brigadistas_atuais: pd.DataFrame) -> str:
    """
    Cria o prompt detalhado para ser enviado ao modelo de IA, agindo como um consultor.
    """
    
    # Prepara uma representação textual da lista de brigadistas atuais
    if not brigadistas_atuais.empty:
        lista_brigadistas_str = brigadistas_atuais['Nome_Brigadista'].to_string(index=False)
        num_brigadistas_atuais = len(brigadistas_atuais)
    else:
        lista_brigadistas_str = "Nenhum brigadista treinado registrado."
        num_brigadistas_atuais = 0

    # O prompt define a persona, o contexto e a tarefa da IA
    prompt = f"""
    **Persona:** Você é um consultor especialista em Segurança contra Incêndio e Emergências, com profundo conhecimento das normas brasileiras como a ABNT NBR 14276. Sua resposta deve ser técnica, clara e orientada para a ação.

    **Contexto:** Você recebeu um cálculo de dimensionamento de brigada de incêndio e a lista de brigadistas atuais para uma planta. Sua tarefa é analisar esses dados e fornecer um relatório consultivo.

    **Dados Recebidos:**
    - Divisão da Planta: {calc_data.get("division")}
    - Nível de Risco: {calc_data.get("risk")}
    - Cálculo Mínimo pela Norma (Total): {calc_data.get("total_brigade")} brigadistas.
    - Necessidade Mínima para o Turno Mais Crítico: {calc_data.get("maior_turno_necessidade")} brigadistas.
    - Número de Brigadistas Atuais: {num_brigadistas_atuais}
    - Lista de Brigadistas Atuais:
    {lista_brigadistas_str}

    **Sua Tarefa (Formato de Resposta Obrigatório):**
    Com base nos dados fornecidos, gere um relatório em Markdown com as seguintes seções:

    ### 1. Diagnóstico de Conformidade
    Analise se o número de brigadistas atuais atende ao mínimo exigido pela norma. Seja direto: a planta está em conformidade ou há um déficit? Quantos brigadistas precisam ser treinados, se for o caso?

    ### 2. Análise de Risco Qualitativa
    Comente brevemente sobre os riscos específicos associados à Divisão '{calc_data.get("division")}' com Nível de Risco '{calc_data.get("risk")}'.

    ### 3. Recomendação Estratégica
    Sugira um número total de brigadistas ideal, incluindo uma margem de segurança (geralmente 10-20% acima do mínimo) para cobrir ausências (férias, doenças). Justifique essa margem.

    ### 4. Plano de Ação Sugerido
    Forneça uma lista de 3 a 4 ações práticas e priorizadas que o gestor de segurança deve tomar com base na sua análise.

    Use uma linguagem profissional e direta.
    """
    return prompt
