import os

from dotenv import load_dotenv

load_dotenv()

CPF = os.getenv("AVA_CPF")
SENHA = os.getenv("AVA_SENHA")

if not CPF or not SENHA:
    raise ValueError("Credenciais não encontradas. Verifique o arquivo .env!")

# Constantes de navegação
LOGIN_URL = "https://exata.unimestresuperior.com/projetos/nucleo/uteis/login.php?&tid=0&lid=0&pid=24&arq_ret=R5QT1WSRQBMCVQVPFFQSF99MCT5RT44Q9WRW0RBM0FMM5QQ4R4CV59RWRF1F5SWCW0"
