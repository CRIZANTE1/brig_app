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


def get_brigade_analysis_prompt(ia_context: dict, knowledge_context: str) -> str:
    """
    Cria um prompt avançado para que a IA execute o cálculo da brigada
    baseado na base de conhecimento e retorne um JSON estruturado.
    """
    divisao = ia_context.get("division")
    risco = ia_context.get("risk")
    populations = ia_context.get("populations", [])

    return f"""
    **Persona:** Você é um Engenheiro de Segurança especialista em normas. Sua tarefa é calcular o número de brigadistas para múltiplos turnos, seguindo rigorosamente as regras da Base de Conhecimento.

    **Cenário de Entrada:**
    - Divisão da Planta: {divisao}
    - Nível de Risco: {risco}
    - População por Turno: {populations}

    **Base de Conhecimento (Sua ÚNICA fonte de regras):**
    ---
    {knowledge_context}
    ---

    **Sua Tarefa (Raciocínio Passo a Passo Obrigatório):**
    1.  **Analise cada turno individualmente.**
    2.  Para cada turno, identifique a população.
    3.  Busque na Base de Conhecimento a regra base para a população (geralmente até 10 pessoas).
    4.  Se a população for maior que 10, busque na Base de Conhecimento a regra de acréscimo correspondente ao Nível de Risco. Calcule os brigadistas adicionais. Lembre-se de arredondar para cima qualquer fração (ex: 1.1 vira 2).
    5.  Some o valor base com os adicionais para encontrar o total do turno.
    6.  Repita para todos os turnos.
    7.  Some os totais de cada turno para encontrar o `total_geral`.
    8.  Identifique o maior valor entre os turnos para `maior_turno_necessidade`.
    
    **Formato de Saída (JSON ESTRITO):**
    Retorne sua resposta APENAS no seguinte formato JSON. Não inclua nenhum texto antes ou depois do JSON.

    ```json
    {{
      "calculo_por_turno": [
        {{
          "turno": 1,
          "populacao": {populations[0] if len(populations) > 0 else 0},
          "regra_base_aplicada": "Descrição da regra base encontrada na Base de Conhecimento.",
          "calculo_base": <numero_base_brigadistas>,
          "regra_acrescimo_aplicada": "Descrição da regra de acréscimo, se aplicável.",
          "calculo_acrescimo": <numero_adicional_brigadistas>,
          "total_turno": <total_brigadistas_no_turno>
        }},
        {{
          "turno": 2,
          "populacao": {populations[1] if len(populations) > 1 else 0},
          "regra_base_aplicada": "...",
          "calculo_base": <...>,
          "regra_acrescimo_aplicada": "...",
          "calculo_acrescimo": <...>,
          "total_turno": <...>
        }}
      ],
      "resumo_final": {{
        "total_geral_brigadistas": <soma_de_todos_os_turnos>,
        "maior_turno_necessidade": <maior_valor_de_total_turno>
      }}
    }}
    ```
    """
