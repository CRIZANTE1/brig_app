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
    incluindo uma etapa de validação de contexto para selecionar as regras corretas
    antes de executar o cálculo.
    """
    divisao = ia_context.get("division")
    risco = ia_context.get("risk")
    populations = ia_context.get("populations", [])

    # Exemplo de cálculo para guiar a IA (Few-shot Prompting)
    example_calculation_logic = """
    Exemplo de Raciocínio para um turno com 22 pessoas, Divisão M-2, Risco Alto:
    1.  **Validação de Contexto:** O cenário é para Divisão 'M-2'. Vou ignorar todas as regras da Base de Conhecimento que se aplicam a outras divisões (como 'F-3', 'D-2', etc.). Vou focar apenas nas regras para 'M-2' e nas regras gerais de acréscimo.
    2.  **População do Turno:** 22 pessoas. É maior que 10, então preciso de uma regra base e uma de acréscimo.
    3.  **Busca da Regra Base (Filtrada):** Procuro na Base de Conhecimento a regra para "M-2", "Risco Alto", "população até 10". Encontro: "'Todos' devem ser brigadistas".
    4.  **Cálculo Base:** A regra 'Todos' para uma base de 10 pessoas significa que o `calculo_base` é 10.
    5.  **Cálculo do Excedente:** 22 - 10 = 12 pessoas.
    6.  **Busca da Regra de Acréscimo (Geral):** Procuro a regra para "Risco Alto" e "população maior que 10". Encontro: "adicionar 1 brigadista para cada grupo de 10 pessoas".
    7.  **Cálculo do Acréscimo:** 12 / 10 = 1.2. Arredondando para cima, o `calculo_acrescimo` é 2.
    8.  **Cálculo Total do Turno:** 10 + 2 = 12.
    """

    return f"""
    **Persona:** Você é um Engenheiro de Segurança do Trabalho metódico e extremamente preciso. Sua tarefa é calcular o número de brigadistas para múltiplos turnos, seguindo um processo rigoroso de validação e cálculo.

    **Base de Conhecimento (Sua ÚNICA fonte de regras):**
    ---
    {knowledge_context}
    ---

    **Sua Tarefa (Raciocínio Passo a Passo Obrigatório):**
    Você deve calcular o número de brigadistas para o seguinte cenário:
    - Divisão da Planta: **{divisao}**
    - Nível de Risco: **{risco}**
    - População por Turno: **{populations}**

    Siga **EXATAMENTE** este processo de raciocínio para CADA TURNO:

    **ETAPA 1: VALIDAÇÃO DE CONTEXTO (A MAIS IMPORTANTE)**
    - Antes de qualquer cálculo, filtre a 'Base de Conhecimento'. **IGNORE QUALQUER REGRA que não seja ESPECÍFICA para a Divisão '{divisao}'** ou que não seja uma regra geral de acréscimo (como as de 'Nota 5'). Não use regras de outras divisões (como F, D, I, etc.) se o cenário não pedir.

    **ETAPA 2: CÁLCULO PASSO A PASSO (Usando apenas o conhecimento filtrado)**
    1.  Identifique a população do turno.
    2.  Busque, no seu conhecimento filtrado, a Regra Base para a Divisão '{divisao}' e Risco '{risco}'.
    3.  Calcule o Número Base. Se a regra for 'Todos', o número base é 10.
    4.  Calcule o Excedente (população_do_turno - 10). Se for <= 0, o excedente é 0.
    5.  Busque a Regra de Acréscimo geral para o Risco '{risco}'.
    6.  Calcule o Acréscimo. **ARREDONDE QUALQUER RESULTADO DECIMAL PARA CIMA**.
    7.  Some Base + Acréscimo para obter o total do turno.

    **Veja este exemplo de como pensar:**
    {example_calculation_logic}

    **Formato de Saída (JSON ESTRITO OBRIGATÓRIO):**
    Após realizar o raciocínio para TODOS os turnos, compile os resultados APENAS no seguinte formato JSON. Não inclua seu raciocínio no JSON final.

    ```json
    {{
      "calculo_por_turno": [
        {{
          "turno": 1,
          "populacao": <população_do_turno_1>,
          "regra_base_aplicada": "A regra da Base de Conhecimento que você usou para o cálculo base.",
          "calculo_base": <numero_base_brigadistas>,
          "regra_acrescimo_aplicada": "A regra da Base de Conhecimento para o acréscimo, ou 'Não aplicável'.",
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
