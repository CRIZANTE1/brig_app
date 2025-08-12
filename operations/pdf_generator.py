import streamlit as st
from weasyprint import HTML, CSS
from datetime import datetime

def generate_organogram_html(resumo: dict) -> str:
    """
    Gera o código HTML para um organograma simples da brigada.
    """
    total_brigadistas = resumo.get('total_geral_brigadistas', 'N/A')
    
    # Este é um organograma genérico. Pode ser expandido para mostrar
    # a distribuição por turno se os dados estiverem disponíveis.
    html = f"""
    <div class="org-chart">
        <div class="org-level">
            <div class="org-box coordinator">Coordenador Geral da Brigada</div>
        </div>
        <div class="org-line-down"></div>
        <div class="org-level">
            <div class="org-box chief">Líder de Turno 1</div>
            <div class="org-box chief">Líder de Turno 2</div>
            <div class="org-box chief">Líder de Turno 3</div>
        </div>
        <div class="org-line-down"></div>
        <div class="org-level">
            <div class="org-box brigadista">Brigadistas ({total_brigadistas} no total distribuídos nos turnos)</div>
        </div>
    </div>
    """
    return html

def generate_pdf_report_abnt(calculation_json: dict, inputs: dict) -> bytes:
    """
    Gera um relatório em PDF a partir de um template HTML e do JSON de cálculo da IA,
    formatado com um layout ABNT, incluindo contextualização, organograma e referências.
    """
    try:
        # --- Extração de Dados ---
        instalacao = calculation_json.get("dados_da_instalacao", {})
        calculo_turnos = calculation_json.get("calculo_por_turno", [])
        resumo = calculation_json.get("resumo_final", {})
        # Pega a Divisão e o Risco dos inputs do formulário
        divisao = inputs.get("division", "N/A")
        risco = inputs.get("risk", "N/A")

        # --- Construção de Elementos Dinâmicos ---
        tabela_turnos_html = ""
        turno_mais_critico = {}
        maior_populacao = -1

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
            if turno.get('populacao', 0) > maior_populacao:
                maior_populacao = turno.get('populacao', 0)
                turno_mais_critico = turno

        explicacao_calculo_html = ""
        if turno_mais_critico:
            pop_critico = turno_mais_critico.get('populacao', 0)
            base_critico = turno_mais_critico.get('calculo_base', 0)
            acrescimo_critico = turno_mais_critico.get('calculo_acrescimo', 0)
            total_critico = turno_mais_critico.get('total_turno', 0)
            explicacao_calculo_html = f"""
            <p>
                O cálculo para o turno de maior população (Turno {turno_mais_critico.get('turno')} com {pop_critico} pessoas) serve como exemplo para a metodologia. 
                Aplica-se a regra base da norma, resultando em <strong>{base_critico} brigadistas</strong>. 
                Para a população excedente ({pop_critico - 10 if pop_critico > 10 else 0} pessoas), a regra de acréscimo foi aplicada, resultando em 
                <strong>{acrescimo_critico} brigadista(s) adicional(is)</strong>. A soma destes valores 
                totaliza os <strong>{total_critico} brigadistas</strong> necessários para este turno.
            </p>
            """

        referencias_abnt_html = """
            <p class="reference">ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. <strong>NBR 14276: Brigada de incêndio - Requisitos</strong>. Rio de Janeiro: ABNT, 2020.</p>
            <p class="reference">SÃO PAULO (Estado). Decreto Estadual nº 63.911, de 10 de dezembro de 2018. <strong>Regulamento de Segurança contra Incêndio das Edificações e Áreas de Risco do Estado de São Paulo</strong>. Diário Oficial do Estado de São Paulo, São Paulo, 11 dez. 2018.</p>
            <p class="reference">SÃO PAULO (Estado). Instrução Técnica nº 17/2019 – <strong>Brigada de Incêndio</strong>. Corpo de Bombeiros da Polícia Militar do Estado de São Paulo, São Paulo, 2019.</p>
        """

        organograma_html = generate_organogram_html(resumo)

        # --- Template CSS (Estilo ABNT Robusto + Estilos do Organograma) ---
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
            .reference { text-indent: 0; }
            .org-chart { text-align: center; margin-top: 2em; page-break-inside: avoid; }
            .org-level { display: flex; justify-content: center; margin: 10px 0; }
            .org-box { border: 2px solid #003366; padding: 10px 15px; border-radius: 8px; display: inline-block; margin: 0 10px; background-color: #ffffff; font-size: 11pt; }
            .org-box.coordinator { background-color: #003366; color: white; font-weight: bold; }
            .org-box.chief { background-color: #e6f7ff; }
            .org-line-down { width: 2px; height: 20px; background: #003366; margin: 0 auto; }
        """

        # --- Template HTML ---
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>Relatório de Brigada</title></head>
        <body>
            <div class="cover-page">
                <div class="cover-header"><p>{instalacao.get('razao_social', 'N/A')}</p></div>
                <div class="cover-center">
                    <p class="cover-title">RELATÓRIO TÉCNICO DE DIMENSIONAMENTO DE BRIGADA DE INCÊNDIO</p>
                    <p class="cover-subtitle">{instalacao.get('imovel', 'N/A')}</p>
                </div>
                <div class="cover-footer"><p>{datetime.now().strftime('%B de %Y')}</p></div>
            </div>

            <h2>1 INTRODUÇÃO</h2>
            <p>Este relatório técnico apresenta o dimensionamento da quantidade mínima de brigadistas de incêndio para a instalação "{instalacao.get('imovel', 'N/A')}", pertencente à empresa {instalacao.get('razao_social', 'N/A')}. O objetivo é estabelecer o efetivo necessário para garantir a conformidade com as normas de segurança e a primeira resposta a uma emergência.</p>
            
            <h2>2 METODOLOGIA</h2>
            <p>A metodologia empregada para o cálculo segue estritamente as diretrizes das normas aplicáveis. O dimensionamento considera, para cada turno de trabalho, a população fixa e os seguintes parâmetros para a edificação:</p>
            <ul>
                <li><strong>Divisão da Edificação:</strong> {divisao}</li>
                <li><strong>Nível de Risco:</strong> {risco}</li>
            </ul>
            
            <h2>3 DETALHAMENTO DO CÁLCULO</h2>
            <p>Com base nos parâmetros acima, a análise resultou na seguinte composição da brigada de incêndio, distribuída por turno:</p>
            <table>
                <thead>
                    <tr><th>Turno</th><th>População</th><th>Cálculo Base</th><th>Acréscimo</th><th>Total de Brigadistas</th></tr>
                </thead>
                <tbody>{tabela_turnos_html}</tbody>
            </table>
            {explicacao_calculo_html}
            
            <h2>4 CONCLUSÃO</h2>
            <p>Com base na metodologia e nos cálculos apresentados para uma instalação classificada como <strong>Divisão {divisao}</strong> com <strong>Risco {risco}</strong>, conclui-se que o efetivo mínimo requerido para a Brigada de Incêndio da instalação é de:</p>
            <ul>
                <li><strong>{resumo.get('total_geral_brigadistas', 'N/A')} brigadistas no total</strong> (soma dos turnos);</li>
                <li><strong>{resumo.get('maior_turno_necessidade', 'N/A')} brigadistas como efetivo mínimo</strong> por turno de trabalho.</li>
            </ul>
            <p>Recomenda-se que a gestão adote as medidas necessárias para treinar, capacitar e manter o contingente de brigadistas em conformidade com os valores dimensionados.</p>

            <h2 style="page-break-before: always;">5 ORGANOGRAMA SUGERIDO DA BRIGADA</h2>
            <p>Para garantir uma estrutura de comando eficaz, sugere-se a seguinte organização funcional para a brigada de incêndio, em conformidade com a ABNT NBR 14276. A estrutura deve ser replicada e adaptada para cada turno de trabalho.</p>
            {organograma_html}

            <h2 style="page-break-before: always;">6 REFERÊNCIAS</h2>
            {referencias_abnt_html}
        </body>
        </html>
        """
        
        # --- Geração do PDF ---
        pdf_bytes = HTML(string=html_template).write_pdf(stylesheets=[CSS(string=css_abnt)])
        return pdf_bytes

    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar o relatório PDF: {e}")
        return None
