HOST_SERVIDOR = "127.0.0.1"
PORTA_SERVIDOR = 9002

DURACAO_VOTACAO = 300

def url_servidor(host: str = HOST_SERVIDOR, porta: int = PORTA_SERVIDOR) -> str:
    return f"http://{host}:{porta}/"
