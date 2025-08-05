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
    incluindo exemplos de erros comuns para garantir a precisão do cálculo,
    especialmente no arredondamento.
    """
    divisao = ia_context.get("division")
    risco = ia_context.get("risk")
    populations = ia_context.get("populations", [])

    # Exemplo de cálculo para guiar a IA
    example_calculation_logic = "..." # (O exemplo anterior continua o mesmo)

    return f"""
    **Persona:** Você é um Engenheiro de Segurança do Trabalho altamente preciso e metódico. Sua tarefa é calcular o número de brigadistas para múltiplos turnos, seguindo rigorosamente as regras da Base de Conhecimento e evitando erros comuns.

    **Base de Conhecimento (Sua ÚNICA fonte de regras):**
    ---
    {knowledge_context}
    ---

    **Sua Tarefa (Raciocínio Passo a Passo Obrigatório):**
    Você deve calcular o número de brigadistas para os seguintes turnos e populações: **{populations}**.

    Siga **EXATAMENTE** este processo de raciocínio para CADA TURNO:

    **ETAPA 1: VALIDAÇÃO DE CONTEXTO**
    - Filtre a 'Base de Conhecimento'. **IGNORE QUALQUER REGRA que não seja ESPECÍFICA para a Divisão '{divisao}'** ou que não seja uma regra geral de acréscimo.

    **ETAPA 2: CÁLCULO PASSO A PASSO (Usando apenas o conhecimento filtrado)**
    1.  Identifique a população do turno.
    2.  Busque a Regra Base para a Divisão '{divisao}' e Risco '{risco}'.
    3.  Calcule o Número Base. Se a regra for 'Todos', o número base é 10.
    4.  **REGRA DE LIMITE:** Se a população for <= 10, o `total_turno` é o **menor valor** entre o `calculo_base` e a `populacao_do_turno`. O acréscimo é 0.
    5.  **CÁLCULO DE ACRÉSCIMO (Apenas para população > 10):**
        a.  Calcule o Excedente (`população_do_turno - 10`).
        b.  Busque a Regra de Acréscimo para o Risco '{risco}'.
        c.  Calcule o Acréscimo (`excedente / fator_de_risco`). **ARREDONDE QUALQUER RESULTADO DECIMAL PARA CIMA**.
        d.  Some Base + Acréscimo para obter o total do turno.

    **ANÁLISE DE ERROS COMUNS (Preste Atenção!):**
    - **ERRO COMUM DE ARREDONDAMENTO:** Um cálculo de `11 / 10` resulta em `1.1`. **NÃO ARREDONDE PARA BAIXO (1)**. O correto é **SEMPRE ARREDONDAR PARA CIMA (2)**, pois qualquer fração de um grupo de pessoas exige um brigadista completo.
    - **EXEMPLO DE ERRO:** População 21, Risco Alto. Excedente = 11. Acréscimo = 11/10 = 1.1. **Cálculo ERRADO do acréscimo: 1**. **Cálculo CORRETO do acréscimo: 2**. Total CORRETO do turno: 10 + 2 = 12.

    **Formato de Saída (JSON ESTRITO OBRIGATÓRIO):**
    Após realizar o raciocínio para TODOS os turnos, compile os resultados APENAS no seguinte formato JSON.

    ```json
    {{
      "calculo_por_turno": [
        {{
          "turno": 1,
          "populacao": <população_do_turno_1>,
          "regra_base_aplicada": "A regra da Base de Conhecimento que você usou.",
          "calculo_base": <numero_base_brigadistas>,
          "regra_acrescimo_aplicada": "A regra de acréscimo, ou 'Não aplicável'.",
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
