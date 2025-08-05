import pandas as pd

def get_pdf_extraction_prompt() -> str:
    """
    Cria o prompt para instruir a IA a extrair nomes de um PDF de atestado.
    """
    return """
    Sua tarefa é analisar o documento PDF fornecido, que é um atestado ou certificado de treinamento de brigada de incêndio.
    Identifique a lista de todos os participantes treinados listados no documento.
    
    Retorne sua resposta estritamente no seguinte formato JSON, contendo uma única chave "nomes" com uma lista de strings:
    
    {"nomes": ["NOME COMPLETO DO PARTICIPANTE 1", "NOME COMPLETO DO PARTICIPANTE 2", "NOME COMPLETO DO PARTICIPANTE 3"]}
    
    Não inclua números de matrícula, CPF, títulos (como "Sr." ou "Dra."), ou qualquer outro texto. Apenas os nomes completos.
    Se nenhum nome for encontrado, retorne uma lista vazia.
    """


def get_brigade_calculation_prompt(ia_context: dict, knowledge_context: str) -> str:
    """
    Cria um prompt avançado para que a IA execute o cálculo da brigada,
    considerando os dados da instalação.
    """
    # Extrai os dados do contexto
    installation = ia_context.get("installation_info", {})
    divisao = ia_context.get("division")
    risco = ia_context.get("risk")
    populations = ia_context.get("populations", [])

    return f"""
    **Persona:** Você é um Engenheiro de Segurança especialista em normas, gerando um relatório técnico.

    **Cenário de Entrada:**
    - Razão Social: {installation.get("Razao_Social", "N/A")}
    - CNPJ: {installation.get("CNPJ", "N/A")}
    - Imóvel: {installation.get("Imovel", "N/A")}
    - Divisão da Planta: {divisao}
    - Nível de Risco: {risco}
    - População por Turno: {populations}

    **Base de Conhecimento (Sua ÚNICA fonte de regras):**
    ---
    {knowledge_context}
    ---

    **Sua Tarefa (Raciocínio Passo a Passo Obrigatório):**
    1.  Analise cada turno individualmente.
    2.  Para cada turno, identifique a população.
    3.  Busque na Base de Conhecimento a regra base para a população (geralmente até 10 pessoas).
    4.  Se a população for maior que 10, busque a regra de acréscimo para o Nível de Risco e calcule os brigadistas adicionais (arredondando para cima).
    5.  Some o valor base com os adicionais para o total do turno.
    6.  Repita para todos os turnos.
    7.  Some os totais de cada turno para o `total_geral`.
    8.  Identifique o maior valor entre os turnos para `maior_turno_necessidade`.
    
    **Formato de Saída (JSON ESTRITO):**
    Retorne sua resposta APENAS no seguinte formato JSON. Não inclua nenhum texto antes ou depois.

    ```json
    {{
      "dados_da_instalacao": {{
        "razao_social": "{installation.get("Razao_Social", "N/A")}",
        "imovel": "{installation.get("Imovel", "N/A")}"
      }},
      "calculo_por_turno": [
        {{
          "turno": 1,
          "populacao": {populations[0] if len(populations) > 0 else 0},
          "regra_base_aplicada": "Descrição da regra base encontrada.",
          "calculo_base": <numero>,
          "regra_acrescimo_aplicada": "Descrição da regra de acréscimo, se aplicável.",
          "calculo_acrescimo": <numero>,
          "total_turno": <numero>
        }}
      ],
      "resumo_final": {{
        "total_geral_brigadistas": <numero>,
        "maior_turno_necessidade": <numero>
      }}
    }}
    ```
    """
