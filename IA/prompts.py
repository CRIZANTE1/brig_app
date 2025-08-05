import pandas as pd
import json 

def get_report_generation_prompt(calculation_json: dict) -> str:
    """
    Cria um prompt para que a IA gere um relatório técnico completo em Markdown
    com base no resultado do cálculo (em formato JSON).
    """
    # Extrai os dados do JSON para facilitar a inserção no prompt
    instalacao = calculation_json.get("dados_da_instalacao", {})
    calculo_turnos = calculation_json.get("calculo_por_turno", [])
    resumo = calculation_json.get("resumo_final", {})

    # Formata a tabela de cálculo para o prompt
    tabela_calculo = "Turno | População | Base | Acréscimo | Total Turno\n"
    tabela_calculo += "-----|-----------|------|-----------|------------\n"
    for turno_info in calculo_turnos:
        tabela_calculo += (
            f"{turno_info.get('turno')} | "
            f"{turno_info.get('populacao')} | "
            f"{turno_info.get('calculo_base')} | "
            f"{turno_info.get('calculo_acrescimo')} | "
            f"**{turno_info.get('total_turno')}**\n"
        )

    return f"""
    **Persona:** Você é um Engenheiro de Segurança do Trabalho redigindo um relatório técnico oficial sobre o dimensionamento da Brigada de Incêndio de uma instalação. Sua linguagem deve ser formal, técnica e objetiva.

    **Dados de Entrada (JSON do Cálculo Realizado):**
    ```json
    {json.dumps(calculation_json, indent=2)}
    ```

    **Sua Tarefa (Gerar Relatório em Markdown):**
    Com base estritamente nos dados do JSON acima, redija um relatório técnico completo em formato Markdown contendo as seguintes seções obrigatórias:

    ---

    ### **Relatório de Dimensionamento de Brigada de Incêndio**

    **1. Introdução**
    - Apresente o objetivo do relatório: dimensionar a quantidade mínima de brigadistas para a instalação especificada.
    - Mencione o nome da instalação ('imovel') e a razão social.

    **2. Metodologia Aplicada**
    - Explique que o cálculo foi realizado com base nos requisitos da norma ABNT NBR 14276 (ou a norma citada na `regra_base_aplicada`).
    - Descreva o método: o número de brigadistas é determinado para cada turno de trabalho individualmente, considerando a população fixa, a divisão da edificação e o nível de risco.

    **3. Detalhamento do Cálculo**
    - Apresente os resultados do cálculo em uma tabela Markdown. Use a tabela abaixo como modelo.
    
    {tabela_calculo}
    
    - Após a tabela, explique textualmente como o cálculo para o turno mais crítico foi feito, citando a regra base e a regra de acréscimo que foram aplicadas (você pode extrair isso da seção `calculo_por_turno` do JSON).

    **4. Conclusão**
    - Apresente o resultado final consolidado.
    - Declare o **número total de brigadistas** necessários para a edificação (a soma de todos os turnos).
    - Declare o **efetivo mínimo** que deve estar presente por turno (o maior valor entre os turnos).
    - Recomende que a empresa garanta que o número de brigadistas treinados e disponíveis em cada turno atenda a este mínimo dimensionado.

    **5. Referências Normativas**
    - Crie uma lista com as referências normativas utilizadas. Extraia as regras das chaves `regra_base_aplicada` e `regra_acrescimo_aplicada` do JSON e liste-as aqui. Cite a norma (ex: ABNT NBR 14276).

    ---
    """
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
    Cria um prompt avançado e robusto para que a IA execute o cálculo da brigada.
    Este prompt inclui:
    - Persona e tarefa claras.
    - Contexto completo da instalação.
    - Base de conhecimento (RAG).
    - Instruções de raciocínio passo a passo (Chain of Thought).
    - Análise de erros comuns para guiar o modelo (Few-shot error analysis).
    - Formato de saída JSON estrito e obrigatório.
    """
    # Extrai os dados do contexto para inserção no prompt
    installation = ia_context.get("installation_info", {})
    divisao = ia_context.get("division")
    risco = ia_context.get("risk")
    populations = ia_context.get("populations", [])

    # Captura os dados da instalação para usar no prompt e no exemplo de saída
    razao_social_exemplo = installation.get("Razao_Social", "N/A")
    imovel_exemplo = installation.get("Imovel", "N/A")

    return f"""
    **Persona:** Você é um Engenheiro de Segurança do Trabalho especialista em normas, altamente preciso e metódico. Sua tarefa é gerar um relatório técnico em formato JSON com o cálculo de brigadistas para múltiplos turnos, seguindo rigorosamente as regras da Base de Conhecimento.

    **Base de Conhecimento (Sua ÚNICA fonte de regras):**
    ---
    {knowledge_context}
    ---

    **Cenário de Entrada para Análise:**
    - Razão Social: {razao_social_exemplo}
    - Imóvel: {imovel_exemplo}
    - Divisão da Planta: {divisao}
    - Nível de Risco: {risco}
    - População por Turno: {populations}

    **Sua Tarefa (Raciocínio Passo a Passo Obrigatório):**
    Você deve calcular o número de brigadistas para cada turno. Siga **EXATAMENTE** este processo de raciocínio para CADA TURNO:

    **ETAPA 1: CÁLCULO BASE**
    1.  **Busque a Regra Base:** Encontre na Base de Conhecimento a regra específica para a **população base (até 10 pessoas)** da Divisão '{divisao}' e Risco '{risco}'. Esta é a sua `regra_base_aplicada`.
    2.  **Calcule o Número Base:** Se a regra for um número, use-o. Se a regra for 'Todos', o número base (`calculo_base`) é 10.

    **ETAPA 2: CÁLCULO DE ACRÉSCIMO (Apenas para população > 10)**
    3.  **Busque a Regra de Acréscimo:** Encontre na Base de Conhecimento a regra geral de **acréscimo** para o Risco '{risco}'. Esta é a sua `regra_acrescimo_aplicada`.
    4.  **Calcule o Acréscimo:** Calcule `(população_do_turno - 10) / fator_de_risco`. **ARREDONDE QUALQUER RESULTADO DECIMAL PARA CIMA**.
    
    **ETAPA 3: CÁLCULO FINAL DO TURNO**
    5.  **Regra de Limite:** Se a população for <= 10, o `total_turno` é o **menor valor** entre o `calculo_base` e a `populacao_do_turno`. O acréscimo é 0 e a regra de acréscimo é 'Não aplicável'.
    6.  **Soma Total:** Se a população for > 10, o `total_turno` é a soma de `calculo_base` + `calculo_acrescimo`.

    **ANÁLISE DE ERROS COMUNS (Preste Atenção!):**
    - **ERRO DE REGRA:** NÃO confunda a "Regra Base" com a "Regra de Acréscimo". Elas são duas regras diferentes e devem ser buscadas e citadas separadamente.
    - **ERRO DE ARREDONDAMENTO:** Um cálculo de `11 / 10` resulta em `1.1`. **NÃO ARREDONDE PARA BAIXO (1)**. O correto é **SEMPRE ARREDONDAR PARA CIMA (2)**.

    **Formato de Saída (JSON ESTRITO OBRIGATÓRIO):**
    Após realizar o raciocínio para TODOS os turnos, compile os resultados APENAS no seguinte formato JSON. Não inclua nenhum texto antes ou depois do JSON.
    **CRÍTICO: A seção 'dados_da_instalacao' DEVE conter as chaves 'razao_social' e 'imovel'.**

    ```json
    {{
      "dados_da_instalacao": {{
        "razao_social": "{razao_social_exemplo}",
        "imovel": "{imovel_exemplo}"
      }},
      "calculo_por_turno": [
        {{
          "turno": 1,
          "populacao": {populations[0] if len(populations) > 0 else 0},
          "regra_base_aplicada": "A regra da Base de Conhecimento específica para a população base (até 10 pessoas).",
          "calculo_base": <numero_base_brigadistas>,
          "regra_acrescimo_aplicada": "A regra da Base de Conhecimento geral para o acréscimo, ou 'Não aplicável'.",
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
        "total_geral_brigadistas": <soma_de_todos_os_'total_turno'>,
        "maior_turno_necessidade": <o_maior_valor_entre_os_'total_turno'>
      }}
    }}
    ```
    """
    
