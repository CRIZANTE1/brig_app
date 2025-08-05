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


# IA/prompts.py

def get_brigade_calculation_prompt(ia_context: dict, knowledge_context: str) -> str:
    """
    Cria um prompt avançado que força a IA a seguir um raciocínio passo a passo
    para executar o cálculo da brigada, usando a base de conhecimento como
    única fonte de verdade.
    """
    divisao = ia_context.get("division")
    risco = ia_context.get("risk")
    populations = ia_context.get("populations", [])

    # Exemplo de cálculo para guiar a IA (Few-shot Prompting)
    example_calculation_logic = """
    Exemplo de Raciocínio para um turno com 22 pessoas, Divisão M-2, Risco Alto:
    1.  **População do Turno:** 22 pessoas.
    2.  **Análise da População:** 22 é maior que 10, então preciso da regra base e da regra de acréscimo.
    3.  **Busca da Regra Base:** Procuro na Base de Conhecimento a regra para "M-2", "Risco Alto", "população até 10". Encontro a regra: "'Todos' devem ser brigadistas".
    4.  **Cálculo Base:** A regra 'Todos' para uma base de 10 pessoas significa que o `calculo_base` é 10.
    5.  **Cálculo da População Excedente:** 22 (total) - 10 (base) = 12 pessoas.
    6.  **Busca da Regra de Acréscimo:** Procuro na Base de Conhecimento a regra para "Risco Alto" e "população maior que 10". Encontro a regra: "adicionar 1 brigadista para cada grupo de 10 pessoas".
    7.  **Cálculo do Acréscimo:** 12 (excedente) / 10 (fator) = 1.2. Arredondando para cima, o `calculo_acrescimo` é 2.
    8.  **Cálculo Total do Turno:** 10 (base) + 2 (acréscimo) = 12.
    """

    return f"""
    **Persona:** Você é um Engenheiro de Segurança do Trabalho altamente preciso e metódico. Sua tarefa é calcular o número de brigadistas para múltiplos turnos, seguindo rigorosamente as regras da Base de Conhecimento fornecida. Você deve detalhar seu raciocínio para cada passo.

    **Base de Conhecimento (Sua ÚNICA fonte de regras):**
    ---
    {knowledge_context}
    ---

    **Sua Tarefa (Raciocínio Passo a Passo Obrigatório):**
    Você deve calcular o número de brigadistas para cada um dos seguintes turnos e populações: **{populations}**.

    Siga **EXATAMENTE** este processo de raciocínio para CADA TURNO:
    1.  **Identifique a população do turno.**
    2.  **Busque a Regra Base:** Encontre na Base de Conhecimento a regra que se aplica à população base (geralmente até 10 pessoas) para a Divisão e Risco dados.
    3.  **Calcule o Número Base:** Se a regra for um número, use-o. Se a regra for 'Todos', o número base é 10 (considerando a base populacional de 10).
    4.  **Calcule o Excedente:** Se a população do turno for maior que 10, calcule `população_do_turno - 10`. Se for 10 ou menos, o excedente é 0.
    5.  **Busque a Regra de Acréscimo:** Se houver excedente, encontre na Base de Conhecimento a regra de acréscimo para o Nível de Risco.
    6.  **Calcule o Acréscimo:** Calcule `excedente / fator_de_risco`. **ARREDONDE QUALQUER RESULTADO DECIMAL PARA CIMA** (ex: 0.75 vira 1; 1.2 vira 2). Se não houver excedente, o acréscimo é 0.
    7.  **Some Base + Acréscimo** para obter o total do turno.

    **Veja este exemplo de como pensar:**
    {example_calculation_logic}

    **Formato de Saída (JSON ESTRITO OBRIGATÓRIO):**
    Após realizar o raciocínio para TODOS os turnos, compile os resultados APENAS no seguinte formato JSON. Não inclua seu raciocínio no JSON final, apenas os resultados e as regras aplicadas.

    ```json
    {{
      "calculo_por_turno": [
        {{
          "turno": 1,
          "populacao": <população_do_turno_1>,
          "regra_base_aplicada": "A regra da Base de Conhecimento que você usou para o cálculo base.",
          "calculo_base": <numero_base_brigadistas>,
          "regra_acrescimo_aplicada": "A regra da Base de Conhecimento para o acréscimo, ou 'Não aplicável' se a população for <= 10.",
          "calculo_acrescimo": <numero_adicional_brigadistas>,
          "total_turno": <total_brigadistas_no_turno>
        }}
      ],
      "resumo_final": {{
        "total_geral_brigadistas": <soma_de_todos_os_'total_turno'>,
        "maior_turno_necessidade": <o_maior_valor_entre_os_'total_turno'>
      }}
    }}
    ```
    """
