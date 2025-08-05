import streamlit as st

# Placeholder for RAG model
def get_rag_recommendation(data):
    # In a real implementation, this function would call a RAG model
    # to get a recommendation based on the input data.
    # For now, it returns a dummy recommendation.

    recommendation = f'''
    **Recomendação da IA:**

    Com base nos dados fornecidos, a recomendação da IA é de **{data['brigade_size'] + 2}** brigadistas.

    **Justificativa:**

    A IA considerou os seguintes fatores para chegar a esta recomendação:

    * **Nível de Risco:** {data['risk_level']}
    * **Área Total:** {data['area']} m²
    * **Presença de Líquidos Inflamáveis:** {"Sim" if data['has_flammable_liquids'] else "Não"}

    A IA também recomenda a implementação de um sistema de sprinklers automáticos para reduzir o risco de incêndio.
    '''

    return recommendation
