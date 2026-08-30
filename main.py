from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from src import auth, config, navigator, player

# 1. Lista de disciplinas disponíveis
DISCIPLINAS = [
    "FUNDAMENTOS GERAIS DA EDUCAÇÃO BÁSICA",
    "DIDÁTICA",
    "LIBRAS E SISTEMA BRAILLE",
    "AFRICANIDADES E DEMOCRACIA",
    "CULTURA E LITERATURA AFRICANA E INDÍGENA",
    "FUNDAMENTOS TEÓRICOS E METODOLÓGICOS DA EDUCAÇÃO ESPECIAL E INCLUSIVA",
    "FUNDAMENTOS DA EDUCAÇÃO ESPECIAL",
    "GESTÃO EDUCACIONAL",
    "DEFICIÊNCIA VISUAL COM ÊNFASE EM BRAILLE",
    "DEFICIÊNCIA FÍSICA E DIFICULDADES PSICOMOTORAS",
    "TRANSTORNOS GLOBAIS DE DESENVOLVIMENTO (TGD) E ALTAS HABILIDADES",
    "TECNOLOGIA ASSISTIVA",
    "COMUNICAÇÃO ALTERNATIVA",
    "PRÁTICAS DE LEITURA E ESCRITA DE ALUNOS COM DEFICIÊNCIA INTELECTUAL",
    "FUNDAMENTOS DA EDUCAÇÃO ESPECIAL NA PERSPECTIVA INCLUSIVA",
    "METODOLOGIA DO ENSINO DA EDUCAÇÃO ESPECIAL",
    "CURRÍCULO ESCOLAR EM UMA PERSPECTIVA INCLUSIVA",
]


# 2. Função que cria o menu no terminal
def selecionar_disciplina() -> str:
    print("\n" + "=" * 60)
    print(" SELEÇÃO DE DISCIPLINA PARA AUTOMOÇÃO")
    print("=" * 60)
    for idx, disciplina in enumerate(DISCIPLINAS, 1):
        print(f"  [{idx:2d}] {disciplina}")
    print("=" * 60)

    while True:
        try:
            escolha = int(
                input(f"\nDigite o número da disciplina (1-{len(DISCIPLINAS)}): ")
            )
            if 1 <= escolha <= len(DISCIPLINAS):
                disciplina_selecionada = DISCIPLINAS[escolha - 1]
                print(f"\nDisciplina selecionada: {disciplina_selecionada}\n")
                return disciplina_selecionada
            print("Opção fora do intervalo. Tente novamente.")
        except ValueError:
            print("Entrada inválida! Digite apenas o número.")


def main():
    # 3. Chama o menu antes de abrir o navegador
    disciplina_alvo = selecionar_disciplina()

    with sync_playwright() as p:
        # Launch com tela maximizada
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        # no_viewport=True faz o Playwright usar a resolução total do seu monitor
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        try:
            auth.realizar_login(page, config.LOGIN_URL, config.CPF, config.SENHA)

            # 4. Passa a disciplina escolhida para o navegador
            ava_page = navigator.acessar_disciplina(context, page, disciplina_alvo)
            player.reproduzir_aulas(ava_page)

            print("\nAutomação concluída com sucesso!")
        except PlaywrightError as err_playwright:
            print(f"\nOcorreu um erro na automação de navegação: {err_playwright}")
        except RuntimeError as err_runtime:
            print(f"\nOcorreu um erro de execução: {err_runtime}")
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
