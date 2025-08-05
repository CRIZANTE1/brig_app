import streamlit as st
from weasyprint import HTML, CSS
from datetime import datetime
import base64

# Opcional: Para embutir uma imagem (logo) no PDF
# def get_image_as_base64(path):
#     try:
#         with open(path, "rb") as image_file:
#             return base64.b64encode(image_file.read()).decode()
#     except FileNotFoundError:
#         return None

def generate_pdf_report_abnt(calculation_json: dict) -> bytes:
    """
    Gera um relatório em PDF a partir de um template HTML e do JSON de cálculo da IA,
    formatado segundo as diretrizes da ABNT.
    Retorna o conteúdo do PDF em bytes.
    """
    try:
        # --- Extração de Dados do JSON ---
        instalacao = calculation_json.get("dados_da_instalacao", {})
        calculo_turnos = calculation_json.get("calculo_por_turno", [])
        resumo = calculation_json.get("resumo_final", {})
        
        # --- Construção de Elementos Dinâmicos ---
        # Tabela de Turnos
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

        # Lista de Referências
        referencias = set()
        for turno in calculo_turnos:
            if turno.get("regra_base_aplicada"): referencias.add(turno["regra_base_aplicada"])
            if turno.get("regra_acrescimo_aplicada") and "Não aplicável" not in turno["regra_acrescimo_aplicada"]:
                referencias.add(turno["regra_acrescimo_aplicada"])
        lista_referencias_html = "".join([f"<li>{ref}</li>" for ref in sorted(list(referencias))])
        
        # --- Template CSS (Estilo ABNT) ---
        css_abnt = """
            @page {
                size: A4;
                margin-top: 3cm;
                margin-left: 3cm;
                margin-bottom: 2cm;
                margin-right: 2cm;
                @bottom-right {
                    content: "Página " counter(page);
                    font-family: 'Arial', sans-serif;
                    font-size: 10pt;
                }
            }
            body {
                font-family: 'Arial', sans-serif;
                font-size: 12pt;
                line-height: 1.5;
                text-align: justify;
            }
            h1, h2, h3 {
                font-family: 'Arial', sans-serif;
                color: #000000;
                font-weight: bold;
                margin-top: 24pt; /* Espaçamento antes do título */
                margin-bottom: 12pt; /* Espaçamento depois do título */
            }
            h1 { font-size: 14pt; text-transform: uppercase; text-align: center; }
            h2 { font-size: 12pt; text-transform: uppercase; }
            p { margin-bottom: 12pt; text-indent: 1.25cm; }
            ul, ol { padding-left: 1.25cm; }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 12pt;
                margin-bottom: 12pt;
            }
            th, td {
                border: 1px solid #000000;
                padding: 6px;
                text-align: center;
                font-size: 10pt;
                vertical-align: middle;
            }
            th { background-color: #e0e0e0; }
            .cover-page { text-align: center; page-break-after: always; }
            .cover-title { font-size: 16pt; margin-top: 5cm; }
            .cover-subtitle { font-size: 14pt; margin-top: 1cm; }
            .cover-info { position: absolute; bottom: 3cm; width: 100%; }
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
            <!-- Página de Rosto -->
            <div class="cover-page">
                <p class="cover-title"><strong>RELATÓRIO TÉCNICO DE DIMENSIONAMENTO DE BRIGADA DE INCÊNDIO</strong></p>
                <p class="cover-subtitle">{instalacao.get('imovel', 'Instalação não informada')}</p>
                
                <div class="cover-info">
                    <p>{instalacao.get('razao_social', 'Empresa não informada')}</p>
                    <p>{datetime.now().strftime('%d de %B de %Y')}</p>
                </div>
            </div>

            <!-- Conteúdo do Relatório -->
            <h2>1 INTRODUÇÃO</h2>
            <p>
                Este relatório técnico apresenta o dimensionamento da quantidade mínima de brigadistas
                de incêndio para a instalação "{instalacao.get('imovel', 'N/A')}",
                pertencente à empresa {instalacao.get('razao_social', 'N/A')}. O objetivo é
                estabelecer o efetivo necessário para garantir a conformidade com as normas de segurança
                e a primeira resposta a uma emergência.
            </p>

            <h2>2 METODOLOGIA</h2>
            <p>
                A metodologia empregada para o cálculo segue estritamente as diretrizes da
                Norma Brasileira ABNT NBR 14276 e/ou Instruções Técnicas do Corpo de Bombeiros aplicáveis.
                O dimensionamento considera, para cada turno de trabalho, a população fixa,
                a divisão de ocupação e o grau de risco da edificação, conforme dados
                analisados por sistema de Inteligência Artificial com base em conhecimento normativo.
            </p>

            <h2>3 DETALHAMENTO DO CÁLCULO</h2>
            <p>
                A análise resultou na seguinte composição da brigada de incêndio, distribuída por turno:
            </p>
            <table>
                <thead>
                    <tr>
                        <th>Turno</th>
                        <th>População</th>
                        <th>Cálculo Base</th>
                        <th>Acréscimo</th>
                        <th>Total de Brigadistas</th>
                    </tr>
                </thead>
                <tbody>
                    {tabela_turnos_html}
                </tbody>
            </table>

            <h2>4 CONCLUSÃO</h2>
            <p>
                Com base na metodologia e nos cálculos apresentados, conclui-se que o efetivo mínimo
                requerido para a Brigada de Incêndio da instalação é de:
            </p>
            <ul>
                <li><strong>{resumo.get('total_geral_brigadistas', 'N/A')} brigadistas no total</strong> (soma dos turnos);</li>
                <li><strong>{resumo.get('maior_turno_necessidade', 'N/A')} brigadistas como efetivo mínimo</strong> por turno de trabalho.</li>
            </ul>
            <p>
                Recomenda-se que a gestão da empresa adote as medidas necessárias para treinar, capacitar
                e manter o contingente de brigadistas em conformidade com os valores dimensionados,
                garantindo a cobertura de todos os turnos de trabalho.
            </p>

            <h2>5 REFERÊNCIAS NORMATIVAS</h2>
            <ol>
                {lista_referencias_html}
            </ol>
        </body>
        </html>
        """
        
        # --- Geração do PDF ---
        # Converte o HTML em PDF em memória, aplicando o CSS
        pdf_bytes = HTML(string=html_template).write_pdf(stylesheets=[CSS(string=css_abnt)])
        return pdf_bytes

    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar o relatório PDF no padrão ABNT: {e}")
        return None
        st.error(f"Ocorreu um erro ao gerar o relatório PDF: {e}")
        return None
