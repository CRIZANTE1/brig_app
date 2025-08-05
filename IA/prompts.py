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
    Cria um prompt avançado que força a IA a seguir um raciocínio passo a passo,
    diferenciando claramente entre Regra Base e Regra de Acréscimo.
    """
    divisao = ia_context.get("division")
    risco = ia_context.get("risk")
    populations = ia_context.get("populations", [])

    return f"""
    **Persona:** Você é um Engenheiro de Segurança do Trabalho metódico e preciso. Sua tarefa é calcular o número de brigadistas, detalhando CADA regra usada.

    **Base de Conhecimento (Sua ÚNICA fonte de regras):**
    ---
    {knowledge_context}
    ---

    **Sua Tarefa (Raciocínio Passo a Passo Obrigatório):**
    Você deve calcular o número de brigadistas para o cenário: Divisão='{divisao}', Risco='{risco}', Populações por Turno='{populations}'.

    Siga **EXATAMENTE** este processo de raciocínio para CADA TURNO:

    **ETAPA 1: CÁLCULO BASE**
    1.  **Busque a Regra Base:** Encontre na Base de Conhecimento a regra específica para a **população base (até 10 pessoas)** da Divisão '{divisao}' e Risco '{risco}'. Esta é a sua `regra_base_aplicada`.
    2.  **Calcule o Número Base:** Se a regra for um número, use-o. Se a regra for 'Todos', o número base (`calculo_base`) é 10.

    **ETAPA 2: CÁLCULO DE ACRÉSCIMO (Apenas para população > 10)**
    3.  **Busque a Regra de Acréscimo:** Encontre na Base de Conhecimento a regra geral de **acréscimo** para o Risco '{risco}'. Esta é a sua `regra_acrescimo_aplicada`.
    4.  **Calcule o Acréscimo:** Calcule `(população_do_turno - 10) / fator_de_risco`. **ARREDONDE QUALQUER RESULTADO DECIMAL PARA CIMA**.
    
    **ETAPA 3: CÁLCULO FINAL DO TURNO**
    5.  **Regra de Limite:** Se a população for <= 10, o `total_turno` é o **menor valor** entre o `calculo_base` e a `populacao_do_turno`. O acréscimo é 0 e a regra de acréscimo é 'Não aplicável'.
    6.  **Soma Total:** Se a população for > 10, o `total_turno` é a soma de `calculo_base` + `calculo_acrescimo`.

    **ANÁLISE DE ERROS COMUNS:**
    - **ERRO DE REGRA:** NÃO confunda a "Regra Base" (para até 10 pessoas) com a "Regra de Acréscimo" (para mais de 10 pessoas). Elas são duas regras diferentes e devem ser buscadas e citadas separadamente.
    - **ERRO DE ARREDONDAMENTO:** Lembre-se, 1.1 vira 2.

    **Formato de Saída (JSON ESTRITO OBRIGOTÓRIO):**
    Após realizar o raciocínio para TODOS os turnos, compile os resultados APENAS no seguinte formato JSON.

    ```json
    {{
      "calculo_por_turno": [
        {{
          "turno": 1,
          "populacao": <população_do_turno_1>,
          "regra_base_aplicada": "A regra da Base de Conhecimento específica para a população base (até 10 pessoas).",
          "calculo_base": <numero_base_brigadistas>,
          "regra_acrescimo_aplicada": "A regra da Base de Conhecimento geral para o acréscimo, ou 'Não aplicável'.",
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
