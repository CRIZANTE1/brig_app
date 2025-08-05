import streamlit as st
import pandas as pd

@st.cache_data(ttl=300) # Cache de 5 minutos para não ler o secrets a cada interação
def get_authorized_users() -> list:
    """
    Carrega a lista de usuários autorizados a partir do st.secrets.
    Retorna uma lista de dicionários, cada um representando um usuário.
    """
    try:
        # Acessa a lista de credenciais dentro da seção 'users'
        if "users" in st.secrets and "credentials" in st.secrets.users:
            # Garante que a estrutura seja uma lista de dicionários Python puros
            return [dict(user) for user in st.secrets.users.credentials]
        
        # Se a estrutura não for encontrada, retorna uma lista vazia
        st.warning("A estrutura 'users.credentials' não foi encontrada em secrets.toml.")
        return []
    except Exception as e:
        st.error(f"Erro inesperado ao carregar os segredos dos usuários: {e}")
        return []

def get_user_info(email: str) -> dict | None:
    """
    Busca as informações completas de um usuário na lista de autorizados,
    usando o e-mail como chave (case-insensitive).
    """
    if not email:
        return None
    
    authorized_users = get_authorized_users()
    email_lower = email.lower()

    for user in authorized_users:
        if user.get("email", "").lower() == email_lower:
            return user
            
    # Retorna None se o usuário não for encontrado na lista
    return None

def is_user_logged_in_at_all() -> bool:
    """
    Verifica APENAS se o usuário está logado via st.user (autenticação do Google),
    sem checar se ele está na lista de permissões.
    """
    return hasattr(st, "user") and hasattr(st.user, "email") and st.user.email is not None

def is_user_authorized() -> bool:
    """
    Verifica se o usuário atual está logado E se seu e-mail consta na
    lista de usuários autorizados no st.secrets. Esta é a verificação de
    acesso principal.
    """
    if not is_user_logged_in_at_all():
        return False
        
    user_info = get_user_info(st.user.email)
    return user_info is not None

def get_user_role() -> str:
    """
    Retorna a 'role' (função) do usuário logado (ex: 'admin' ou 'user').
    Retorna 'user' como padrão seguro se não for encontrado.
    """
    if not is_user_authorized():
        return "user"
        
    user_info = get_user_info(st.user.email)
    return user_info.get("role", "user")

def get_user_display_name() -> str:
    """
    Retorna o nome de exibição do usuário logado para saudações.
    Prioriza o nome definido no secrets, senão o nome do Google, e por último o e-mail.
    """
    if not is_user_logged_in_at_all():
        return "Visitante"
        
    user_info = get_user_info(st.user.email)
    
    if user_info and user_info.get("name"):
        return user_info["name"]
    
    return getattr(st.user, "name", st.user.email)

def is_admin() -> bool:
    """Verifica se o usuário logado tem a role de 'admin'."""
    return get_user_role() == "admin"

def check_admin_permission():
    """
    Função de barreira: Verifica se o usuário é admin. Se não for, exibe
    uma mensagem de erro e para a execução do script da página.
    Útil para proteger páginas ou funcionalidades exclusivas de administradores.
    """
    if not is_admin():
        st.error("Acesso Negado. Você não tem permissão de administrador para acessar esta funcionalidade.")
        st.stop()

def get_users_for_display() -> pd.DataFrame:
    """
    Prepara um DataFrame com os usuários autorizados para ser exibido em
    uma página de gerenciamento de usuários.
    """
    authorized_users = get_authorized_users()
    if not authorized_users:
        return pd.DataFrame(columns=["Nome", "E-mail", "Função"])
    
    display_data = []
    for user in authorized_users:
        display_data.append({
            "Nome": user.get("name", "N/A"),
            "E-mail": user.get("email", "N/A"),
            "Função": user.get("role", "user").capitalize() # ex: "Admin", "User"
        })
        
    df = pd.DataFrame(display_data)
    return df



