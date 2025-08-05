import math

# Dados da Tabela A.1 da ABNT NBR 14276 (parcial, focando nos grupos mais comuns)
# A estrutura é: Divisão -> Risco -> População -> Brigadistas
# "Todos" significa que 100% da população do turno deve ser brigadista.
NBR_TABLE = {
    'D-2': { # Agência Bancária
        'Baixo':  {10: 2}, 'Médio': {10: 4}, 'Alto': {10: 'Todos'}
    },
    'M-2': { # Tanques ou parque de tanques
        'Baixo':  {10: 'Todos'}, 'Médio': {10: 'Todos'}, 'Alto': {10: 'Todos'}
    },
    'I-1': { # Indústria com baixo risco
        'Baixo': {10: 2}, 'Médio': {10: 4}, 'Alto': {10: 'Todos'}
    },
    'I-2': { # Indústria com médio risco
        'Baixo': {10: 2}, 'Médio': {10: 4}, 'Alto': {10: 'Todos'}
    },
    'I-3': { # Indústria com alto risco
        'Baixo': {10: 2}, 'Médio': {10: 4}, 'Alto': {10: 'Todos'}
    },
    'C-1': { # Comércio com baixo risco
        'Baixo': {10: 2}, 'Médio': {10: 4}, 'Alto': {10: 'Todos'}
    },
    'C-2': { # Comércio com médio risco
        'Baixo': {10: 2}, 'Médio': {10: 4}, 'Alto': {10: 'Todos'}
    },
    'J-4': { # Depósitos de alto risco
        'Baixo': {10: 2}, 'Médio': {10: 'Todos'}, 'Alto': {10: 'Todos'}
    }
    # Adicione outras divisões da norma aqui conforme necessário
}

# Constantes da Nota 5 da norma (pessoas por brigadista adicional)
ACRESCIMO_POR_RISCO = {
    "Baixo": 20,
    "Médio": 15,
    "Alto": 10
}

def get_table_divisions() -> list:
    """Retorna a lista de divisões disponíveis na tabela para o selectbox da UI."""
    return sorted(list(NBR_TABLE.keys()))

def calculate_brigade_for_shift(division: str, risk: str, population: int) -> int:
    """
    Calcula o número de brigadistas para um único turno, baseado na NBR 14276.
    """
    if population <= 0:
        return 0
        
    if division not in NBR_TABLE or risk not in NBR_TABLE[division]:
        raise ValueError(f"Combinação de Divisão '{division}' e Risco '{risk}' não encontrada na norma implementada.")

    # Pega o valor base para população até 10 pessoas
    base_calc = NBR_TABLE[division][risk].get(10)

    # Se a regra for "Todos", o número de brigadistas é igual à população do turno.
    if base_calc == 'Todos':
        return population

    base_brigadistas = int(base_calc)

    # Se a população for 10 ou menos, retorna o valor base (limitado ao número de pessoas).
    if population <= 10:
        return min(population, base_brigadistas)

    # Se a população for maior que 10, calcula o acréscimo (Nota 5 da norma)
    pop_excedente = population - 10
    divisor = ACRESCIMO_POR_RISCO[risk]
    
    # math.ceil arredonda para cima, garantindo que qualquer fração de grupo conte como 1 brigadista a mais.
    brigadistas_adicionais = math.ceil(pop_excedente / divisor)
    
    return base_brigadistas + brigadistas_adicionais

def calculate_total_brigade(turn_populations: list, division: str, risk: str) -> dict:
    """
    Calcula o número de brigadistas por turno e o total.
    
    Args:
        turn_populations (list): Uma lista com a população de cada turno. Ex: [28, 8, 5]
        division (str): A divisão da edificação (ex: 'M-2').
        risk (str): O nível de risco ('Baixo', 'Médio', 'Alto').
        
    Returns:
        dict: Um dicionário com os resultados detalhados.
    """
    brigade_per_shift = [calculate_brigade_for_shift(division, risk, pop) for pop in turn_populations]
    
    total_brigadistas = sum(brigade_per_shift)
    
    return {
        "total_brigadistas": total_brigadistas,
        "brigadistas_por_turno": brigade_per_shift,
        "maior_turno_necessidade": max(brigade_per_shift) if brigade_per_shift else 0
    }
