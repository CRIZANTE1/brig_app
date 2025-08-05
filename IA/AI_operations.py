import time
import collections

class RateLimiter:
    """
    Gerencia e impõe limites de taxa para chamadas de API de IA (RPM e TPM).
    """
    def __init__(self, rpm_limit: int, tpm_limit: int):
        """
        Inicializa o RateLimiter com os limites especificados.

        Args:
            rpm_limit (int): Limite de requisições por minuto.
            tpm_limit (int): Limite de tokens por minuto.
        """
        self.rpm_limit = rpm_limit
        self.tpm_limit = tpm_limit
        
        # Fila para rastrear os timestamps das requisições no último minuto
        self.request_timestamps = collections.deque()
        # Fila para rastrear os timestamps e a contagem de tokens
        self.token_usage = collections.deque()

    def _cleanup_old_requests(self):
        """Remove timestamps de requisições mais antigas que um minuto."""
        current_time = time.time()
        while self.request_timestamps and self.request_timestamps[0] <= current_time - 60:
            self.request_timestamps.popleft()

    def _cleanup_old_tokens(self):
        """Remove registros de uso de token mais antigos que um minuto."""
        current_time = time.time()
        while self.token_usage and self.token_usage[0][0] <= current_time - 60:
            self.token_usage.popleft()

    def wait_for_rpm_slot(self):
        """
        Verifica o limite de RPM. Se excedido, aguarda o tempo necessário.
        """
        self._cleanup_old_requests()
        if len(self.request_timestamps) >= self.rpm_limit:
            # Calcula o tempo de espera necessário
            time_to_wait = self.request_timestamps[0] - (time.time() - 60)
            if time_to_wait > 0:
                print(f"[RateLimiter] Limite de RPM ({self.rpm_limit}) atingido. Aguardando {time_to_wait:.2f} segundos.")
                time.sleep(time_to_wait)
        
        # Registra a nova requisição
        self.request_timestamps.append(time.time())

    def wait_for_tpm_slot(self, tokens_to_send: int):
        """
        Verifica o limite de TPM. Se o envio atual exceder, aguarda.
        
        Args:
            tokens_to_send (int): O número de tokens que serão enviados na próxima requisição.
        """
        self._cleanup_old_tokens()
        current_tokens = sum(count for _, count in self.token_usage)

        if current_tokens + tokens_to_send > self.tpm_limit:
            # Esta é uma simplificação. Uma implementação robusta precisaria
            # de uma lógica mais complexa para esperar o tempo exato.
            # Por enquanto, apenas emitimos um aviso e esperamos um tempo fixo.
            time_to_wait = 10 # Espera um tempo fixo como fallback
            print(f"[RateLimiter] Limite de TPM ({self.tpm_limit}) seria excedido. Aguardando {time_to_wait}s.")
            time.sleep(time_to_wait)
        
        # Registra o uso de tokens
        self.token_usage.append((time.time(), tokens_to_send))

    def call_api(self, api_function, *args, **kwargs):
        """
        Executa uma chamada de API, garantindo que os limites de taxa sejam respeitados.
        
        Args:
            api_function: A função da API a ser chamada.
            *args, **kwargs: Argumentos para a função da API.

        Returns:
            O resultado da chamada da função da API.
        """
        # Exemplo de como obter a contagem de tokens (isso é hipotético)
        # Em uma implementação real, você precisaria de uma função para tokenizar o prompt.
        prompt_tokens = kwargs.get('prompt_tokens', 1000) # Valor de exemplo

        # Espera por um slot de RPM e TPM
        self.wait_for_rpm_slot()
        self.wait_for_tpm_slot(prompt_tokens)

        print(f"[RateLimiter] Realizando chamada para a API...")
        # Chama a função real da API
        return api_function(*args, **kwargs)

# --- Exemplo de Uso ---

# Instancia o limiter com os limites do Gemini 2.5 Pro
gemini_limiter = RateLimiter(rpm_limit=100, tpm_limit=5250000)

# Função de exemplo que simula uma chamada à API de IA
def fake_gemini_api_call(prompt: str, prompt_tokens: int):
    print(f"  -> API: Processando prompt com {prompt_tokens} tokens.")
    time.sleep(0.2) # Simula a latência da rede
    return {"response": f"Resposta para: {prompt}"}

if __name__ == '__main__':
    print("Iniciando simulação de chamadas de API com Rate Limiting...")
    
    # Simula 110 chamadas para testar o limite de RPM
    for i in range(110):
        print(f"Preparando chamada {i+1}...")
        gemini_limiter.call_api(
            fake_gemini_api_call, 
            prompt=f"Este é o prompt número {i+1}",
            prompt_tokens=50000 # Simulando um uso alto de tokens
        )
    
    print("\nSimulação concluída.")