import streamlit as st
from weasyprint import HTML, CSS
from datetime import datetime

def generate_pdf_report(calculation_json: dict) -> bytes:
    """
    Gera um relatório em PDF a partir de um template HTML e do JSON de cálculo da IA.
    Retorna o conteúdo do PDF em bytes.
    """
    try:
        # --- Extração de Dados do JSON ---
        instalacao = calculation_json.get("dados_da_instalacao", {})
        calculo_turnos = calculation_json.get("calculo_por_turno", [])
        resumo = calculation_json.get("resumo_final", {})
        
        # --- Construção da Tabela de Turnos em HTML ---
        tabela_turnos_html = ""
        referencias = set() # Usamos um set para evitar referências duplicadas
        
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
            # Coleta as referências normativas
            if turno.get("regra_base_aplicada"):
                referencias.add(turno["regra_base_aplicada"])
            if turno.get("regra_acrescimo_aplicada") and turno["regra_acrescimo_aplicada"] != "Não aplicável":
                referencias.add(turno["regra_acrescimo_aplicada"])

        # Formata as referências como uma lista HTML
        lista_referencias_html = "".join([f"<li>{ref}</li>" for ref in sorted(list(referencias))])

        # --- Template HTML com CSS Integrado ---
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Relatório de Brigada de Incêndio</title>
            <style>
                @page {{ size: A4; margin: 2cm; }}
                body {{ font-family: 'Helvetica', sans-serif; color: #333; line-height: 1.6; }}
                h1, h2, h3 {{ color: #003366; border-bottom: 2px solid #003366; padding-bottom: 5px; }}
                h1 {{ font-size: 24pt; text-align: center; border: none; }}
                h2 {{ font-size: 16pt; margin-top: 30px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ccc; padding: 10px; text-align: center; }}
                th {{ background-color: #f2f2f2; color: #003366; }}
                .summary-box {{ background-color: #e6f7ff; border-left: 5px solid #003366; padding: 15px; margin-top: 20px; }}
                .footer {{ position: fixed; bottom: -1.5cm; left: 0; right: 0; text-align: center; font-size: 10pt; color: #888; }}
            </style>
        </head>
        <body>
            <div class="footer">
                Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
            </div>

            <h1>Relatório de Dimensionamento de Brigada de Incêndio</h1>

            <h2>1. Dados da Instalação</h2>
            <p><strong>Razão Social:</strong> {instalacao.get('razao_social', 'Não informado')}</p>
            <p><strong>Imóvel Analisado:</strong> {instalacao.get('imovel', 'Não informado')}</p>

            <h2>2. Metodologia</h2>
            <p>
                O presente dimensionamento foi realizado com base nos requisitos da ABNT NBR 14276 e outras normas aplicáveis, considerando a divisão da edificação, o nível de risco e a população fixa para cada turno de trabalho, conforme os dados fornecidos.
            </p>

            <h2>3. Detalhamento do Cálculo por Turno</h2>
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

            <h2>4. Conclusão do Dimensionamento</h2>
            <div class="summary-box">
                <p>Com base na análise, o dimensionamento mínimo para a instalação é de:</p>
                <ul>
                    <li><strong>Total Geral de Brigadistas:</strong> {resumo.get('total_geral_brigadistas', 'N/A')}</li>
                    <li><strong>Efetivo Mínimo por Turno:</strong> {resumo.get('maior_turno_necessidade', 'N/A')}</li>
                </ul>
                <p><strong>Recomendação:</strong> A empresa deve assegurar que o número de brigadistas treinados e disponíveis em cada turno de trabalho atenda ou exceda o efetivo mínimo aqui dimensionado.</p>
            </div>

            <h2>5. Referências Normativas Aplicadas</h2>
            <ul>
                {lista_referencias_html}
            </ul>

        </body>
        </html>
        """
        
        # --- Geração do PDF ---
        # Converte o HTML em PDF em memória
        pdf_bytes = HTML(string=html_template).write_pdf()
        return pdf_bytes

    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar o relatório PDF: {e}")
        return None
