# Aplicativo de Cálculo de Brigada de Incêndio

Este é um aplicativo Streamlit projetado para calcular o número de brigadistas de incêndio necessários para uma edificação, com base em uma variedade de fatores, como classificação da edificação, área, população e nível de risco. O aplicativo também se integra ao Google Sheets para carregar dados da edificação e usa um modelo de IA para fornecer recomendações.

## Funcionalidades

- **Cálculo Detalhado:** Calcula o número de brigadistas com base em vários parâmetros da edificação.
- **Integração com Google Sheets:** Carrega dados da edificação diretamente de uma planilha Google.
- **Recomendação de IA:** Fornece uma recomendação de brigadistas orientada por IA (atualmente um placeholder).
- **Autenticação:** Usa OpenID Connect para autenticação de usuários via Google.
- **Controle de Acesso:** Verifica se o usuário é um administrador com base em uma lista em uma planilha do Google.

## Como Executar a Aplicação

1. **Instale as Dependências:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure os Segredos do Streamlit:**

   Crie um arquivo `.streamlit/secrets.toml` e adicione as seguintes informações:

   ```toml
   # Credenciais da API do Google Sheets
   [gcp_service_account]
   type = "service_account"
   project_id = "your_project_id"
   private_key_id = "your_private_key_id"
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "your_client_email"
   client_id = "your_client_id"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "..."

   # Configuração do OpenID Connect
   [oidc]
   google_client_id = "your_google_client_id"
   google_client_secret = "your_google_client_secret"
   google_redirect_uri = "http://localhost:8501"
   cookie_secret = "your_random_cookie_secret"
   ```

3. **Execute a Aplicação:**

   ```bash
   streamlit run app.py
   ```
