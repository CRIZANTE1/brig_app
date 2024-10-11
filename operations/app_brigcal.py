# Importações necessárias
from datetime import datetime
import json
from math import ceil
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Definindo o caminho do arquivo JSON como uma variável global
CAMINHO_JSON = r'dicts/tabela_a1.json'

def ler_json():
    try:
        with open(CAMINHO_JSON, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            # Adicionando a lista de opções de funcionários se não existir
            if 'opcoes_funcionarios' not in dados:
                dados['opcoes_funcionarios'] = list(range(1, 101))  # Gera a lista de 1 a 100
            return dados
    except FileNotFoundError:
        print(f"Erro: O arquivo {CAMINHO_JSON} não foi encontrado.")
        raise
    except UnicodeDecodeError:
        with open(CAMINHO_JSON, 'r', encoding='latin-1') as f:
            return json.load(f)

# Função para calcular a brigada
def calcula_brigada():
    dados_json = ler_json()
    # Extrair dados do JSON
    divisao = dados_json['numeros_utilizados']['divisao']
    risco = dados_json['numeros_utilizados']['risco']
    pessoas = dados_json['numeros_utilizados']['pessoas']
    turnos = dados_json['numeros_utilizados']['turnos']

    # Extrair constantes de risco do JSON
    RISCO_BAIXO = dados_json['constantes_por_nivel_de_risco']['risco_baixo']
    RISCO_MEDIO = dados_json['constantes_por_nivel_de_risco']['risco_medio']
    RISCO_ALTO = dados_json['constantes_por_nivel_de_risco']['risco_alto']

    # Determina o valor base de brigadistas e o tamanho do grupo para o risco fornecido
    if risco == 'risco_baixo':
        base_brigadistas, grupo = 2, RISCO_BAIXO
    elif risco == 'risco_medio':
        base_brigadistas, grupo = 4, RISCO_MEDIO
    elif risco == 'risco_alto':
        base_brigadistas, grupo = 8, RISCO_ALTO
    else:
        # Caso padrão se nenhum dos riscos acima for correspondido
        base_brigadistas, grupo = 2, RISCO_BAIXO
        print(f"Aviso: Risco não reconhecido '{risco}'. Usando valores padrão.")

    # Cálculo pela Tabela A.1
    brigada = base_brigadistas if pessoas <= 10 else base_brigadistas + ceil((pessoas - 10) / grupo)

    # Cálculo por turno
    pessoas_turno = pessoas / turnos
    brigada_turno = base_brigadistas if pessoas_turno <= 10 else base_brigadistas + ceil((pessoas_turno - 10) / grupo)
    total_brigada_turnos = brigada_turno * turnos

    # Número mínimo é o maior entre os cálculos
    return max(brigada, total_brigada_turnos)

# Função para emitir o relatório
def emitir_relatorio(brigadistas_necessarios):
    dados_json = ler_json()
    divisao = dados_json['numeros_utilizados']['divisao']
    risco = dados_json['numeros_utilizados']['risco']
    pessoas = dados_json['numeros_utilizados']['pessoas']
    turnos = dados_json['numeros_utilizados']['turnos']
    
    data_atual = datetime.now().strftime('%d/%m/%Y')
    
    relatorio = f"""Cálculo de Brigada de Emergência

Conforme Instrução Técnica nº 17/2019 do Corpo de Bombeiros do Estado de São Paulo, Tabela A.1 - Composição mínima da brigada de incêndio por pavimento; Divisão {divisao}; Nota 5 - Regra de acréscimo de brigadistas para população fixa maior que 10; Exemplo B; Total de turnos; Nota 7, a quantidade mínima de brigadistas deve ser conforme o previsto na tabela ou de acordo com a necessidade no cenário de combate ao incêndio, o que for maior;

Implementando as regras especificadas nesses elementos, calculando primeiramente o mínimo pela Tabela A.1, divisão {divisao}, Nota 7 e Nota 5, depois seguindo o Exemplo B, levando em consideração os turnos, e retornando o maior valor encontrado.

Dados do Cálculo:
- Divisão: {divisao}
- Risco: {risco}
- População fixa da Instalação: {pessoas} pessoas
- Turnos: {turnos}

Local:
Razão Social: {dados_json['local_calculo_brigada']['razao_social']}
CNPJ: {dados_json['local_calculo_brigada']['cnpj']}
Imóvel: {dados_json['local_calculo_brigada']['imovel']}
Endereço: {dados_json['local_calculo_brigada']['endereco']}
Bairro: {dados_json['local_calculo_brigada']['bairro']}
Cidade: {dados_json['local_calculo_brigada']['cidade']}
UF: {dados_json['local_calculo_brigada']['uf']}
CEP: {dados_json['local_calculo_brigada']['cep']}

Data de Emissão: {data_atual}

Brigadistas necessários: {brigadistas_necessarios}

Referências Normativas:
1. SÃO PAULO (Estado). Instrução Técnica nº 17/2019 – Brigada de Incêndio. Secretaria da Segurança Pública, Corpo de Bombeiros da Polícia Militar do Estado de São Paulo, São Paulo, 2019.
2. ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. NBR 14277: Instalações e equipamentos para treinamento de combate a incêndio. Rio de Janeiro: ABNT, 2005.
3. SÃO PAULO (Estado). Decreto Estadual nº 63.911, de 10 de dezembro de 2018. Regulamento de Segurança contra Incêndio das Edificações e Áreas de Risco do Estado de São Paulo. Diário Oficial do Estado de São Paulo, São Paulo, 11 dez. 2018.
4. ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. NBR 18801: Gestão de emergências. Rio de Janeiro: ABNT, 2010.
5. ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. NBR ISO 45001: Sistemas de gestão de segurança e saúde ocupacional, Requisitos com orientação para uso. Rio de Janeiro: ABNT, 2018.

Desenvolvido por: CRISTIAN FERREIRA CARLOS, cristiancarlos@vibraenergia.com.br"""
    
    return relatorio

# Função que exporta para PDF
def save_to_pdf(text, file_path="relatorio_brigada.pdf"):
    doc = SimpleDocTemplate(file_path, pagesize=letter,
                            rightMargin=10, leftMargin=10,
                            topMargin=10, bottomMargin=10)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Normal_Unicode',
                              fontName='Helvetica',
                              fontSize=10,
                              leading=12))

    story = []
    for paragraph in text.split('\n\n'):
        p = Paragraph(paragraph.replace('\n', '<br/>'), styles['Normal_Unicode'])
        story.append(p)
        story.append(Spacer(1, 6))

    doc.build(story)
    print(f"Relatório salvo em {file_path}")


