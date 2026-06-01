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

   Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml` e preencha os valores.

   O login usa `st.login()` do Streamlit (OIDC). A seção **`[auth]`** é obrigatória — não use `[oidc]`:

   ```toml
   [auth]
   redirect_uri = "http://localhost:8501/oauth2callback"
   cookie_secret = "string-aleatoria-longa"
   client_id = "xxx.apps.googleusercontent.com"
   client_secret = "xxx"
   server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
   ```

   No [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials → seu cliente OAuth 2.0, adicione em **Authorized redirect URIs** a mesma URL de `redirect_uri` (local ou `https://SEU-APP.streamlit.app/oauth2callback` na Cloud).

   No **Streamlit Cloud**, cole o conteúdo completo em **App settings → Secrets** (não é necessário arquivo `.streamlit/secrets.toml` no repositório).

3. **Execute a Aplicação:**

   ```bash
   streamlit run app.py
   ```
