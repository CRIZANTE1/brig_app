import streamlit as st
from weasyprint import HTML, CSS
from datetime import datetime
import base64

# Opcional: Para embutir uma imagem (logo) no PDF
# Você pode descomentar esta função e a linha no HTML se tiver um logo.
# def get_image_as_base64(path_to_image):
#     try:
#         with open(path_to_image, "rb") as image_file:
#             return f"data:image/png;base64,{base64.b64encode(image_file.read()).decode()}"
#     except FileNotFoundError:
#         return None

def generate_pdf_report_abnt(calculation_json: dict) -> bytes:
    """
    Gera um relatório em PDF a partir de um template HTML e do JSON de cálculo da IA,
    formatado com um layout ABNT robusto usando Flexbox.
    Retorna o conteúdo do PDF em bytes.
    """
    try:
        # --- Extração de Dados do JSON ---
        instalacao = calculation_json.get("dados_da_instalacao", {})
        calculo_turnos = calculation_json.get("calculo_por_turno", [])
        resumo = calculation_json.get("resumo_final", {})
        
        # --- Construção de Elementos Dinâmicos ---
        tabela_turnos_html = ""
        for turno in calculo_turnos:
            tabela_turnos_html += f"""
                <tr>
                    <td>{turno.get('turno', 'N/A')}</td>
                    <td>{turno.get('populacao', 'N/A')}</td>
                    <td>{turno.get('calculo_base', 'N/A')}</td>
                    <td>{turno.get('calculo_acrescimo', 'N/A')}</td>
                    <td><strong>{turno.get('total_turno', 'N/A')}</strong></td>
                </tr>
            """

        referencias = set()
        for turno in calculo_turnos:
            if turno.get("regra_base_aplicada"): referencias.add(turno["regra_base_aplicada"])
            if turno.get("regra_acrescimo_aplicada") and "Não aplicável" not in turno["regra_acrescimo_aplicada"]:
                referencias.add(turno["regra_acrescimo_aplicada"])
        lista_referencias_html = "".join([f"<li>{ref}</li>" for ref in sorted(list(referencias))])
        
        # --- Template CSS (Estilo ABNT Robusto) ---
        css_abnt = """
            @page {
                size: A4;
                margin: 3cm 2cm 2cm 3cm; /* Superior, Direita, Inferior, Esquerda */
                @bottom-right { content: counter(page); font-family: Arial, sans-serif; font-size: 10pt; color: #888; }
            }
            body { font-family: Arial, sans-serif; font-size: 12pt; line-height: 1.5; text-align: justify; }
            h1, h2, h3 { font-family: Arial, sans-serif; color: #000; font-weight: bold; margin-top: 1.5em; margin-bottom: 0.75em; line-height: 1.2; }
            h1 { font-size: 14pt; text-transform: uppercase; text-align: center; }
            h2 { font-size: 12pt; text-transform: uppercase; }
            p { margin: 0 0 1em 0; text-indent: 1.25cm; }
            ul, ol { padding-left: 1.25cm; margin-bottom: 1em; }
            table { width: 100%; border-collapse: collapse; margin: 1.5em 0; }
            th, td { border: 1px solid #000; padding: 8px; text-align: center; font-size: 10pt; vertical-align: middle; }
            th { background-color: #EAEAEA; font-weight: bold; }
            .cover-page { display: flex; flex-direction: column; justify-content: space-between; align-items: center; height: 20.7cm; page-break-after: always; text-align: center; }
            .cover-header, .cover-center, .cover-footer { width: 100%; }
            .cover-title { font-size: 16pt; font-weight: bold; margin-top: 4cm; }
            .cover-subtitle { font-size: 14pt; margin-top: 2cm; }
            .cover-footer { font-size: 12pt; }
        """

        # --- Template HTML ---
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Relatório de Dimensionamento de Brigada de Incêndio</title>
        </head>
        <body>
            <!-- Página de Rosto com Flexbox -->
            <div class="cover-page">
                <div class="cover-header">
                    <!-- A chamada para a função de imagem foi completamente removida -->
                    <p>{instalacao.get('razao_social', 'Empresa não informada')}</p>
                </div>
                
                <div class="cover-center">
                    <p class="cover-title">RELATÓRIO TÉCNICO DE DIMENSIONAMENTO DE BRIGADA DE INCÊNDIO</p>
                    <p class="cover-subtitle">{instalacao.get('imovel', 'Instalação não informada')}</p>
                </div>

                <div class="cover-footer">
                    <p>{datetime.now().strftime('%B de %Y')}</p>
                </div>
            </div>

            <!-- Conteúdo do Relatório -->
            <h2>1 INTRODUÇÃO</h2>
            <p>Este relatório técnico apresenta o dimensionamento da quantidade mínima de brigadistas de incêndio para a instalação "{instalacao.get('imovel', 'N/A')}", pertencente à empresa {instalacao.get('razao_social', 'N/A')}. O objetivo é estabelecer o efetivo necessário para garantir a conformidade com as normas de segurança e a primeira resposta a uma emergência.</p>
            <h2>2 METODOLOGIA</h2>
            <p>A metodologia empregada para o cálculo segue estritamente as diretrizes da Norma Brasileira ABNT NBR 14276 e/ou Instruções Técnicas do Corpo de Bombeiros aplicáveis. O dimensionamento considera, para cada turno de trabalho, a população fixa, a divisão de ocupação e o grau de risco da edificação.</p>
            <h2>3 DETALHAMENTO DO CÁLCULO</h2>
            <p>A análise resultou na seguinte composição da brigada de incêndio, distribuída por turno:</p>
            <table>
                <thead>
                    <tr><th>Turno</th><th>População</th><th>Cálculo Base</th><th>Acréscimo</th><th>Total de Brigadistas</th></tr>
                </thead>
                <tbody>{tabela_turnos_html}</tbody>
            </table>
            <h2>4 CONCLUSÃO</h2>
            <p>Com base na metodologia e nos cálculos apresentados, conclui-se que o efetivo mínimo requerido para a Brigada de Incêndio da instalação é de:</p>
            <ul>
                <li><strong>{resumo.get('total_geral_brigadistas', 'N/A')} brigadistas no total</strong> (soma dos turnos);</li>
                <li><strong>{resumo.get('maior_turno_necessidade', 'N/A')} brigadistas como efetivo mínimo</strong> por turno de trabalho.</li>
            </ul>
            <p>Recomenda-se que a gestão da empresa adote as medidas necessárias para treinar, capacitar e manter o contingente de brigadistas em conformidade com os valores dimensionados.</p>
            <h2>5 REFERÊNCIAS NORMATIVAS</h2>
            <ol>
                {lista_referencias_html}
            </ol>
        </body>
        </html>
        """
        
        # --- Geração do PDF ---
        pdf_bytes = HTML(string=html_template).write_pdf(stylesheets=[CSS(string=css_abnt)])
        return pdf_bytes

    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar o relatório PDF no padrão ABNT: {e}")
        return None
