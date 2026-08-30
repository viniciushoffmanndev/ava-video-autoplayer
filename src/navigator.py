from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError


def acessar_disciplina(context, page, nome_disciplina):
    print("-> Acessando o Ambiente Virtual...")
    try:
        with context.expect_page(timeout=15000) as new_page_info:
            page.click("text=Ambiente Virtual")
        ava_page = new_page_info.value
    except TimeoutError:
        page.click("text=Ambiente Virtual")
        ava_page = page

    ava_page.wait_for_load_state("networkidle")
    ava_page.wait_for_timeout(5000)

    print(f"-> Localizando a disciplina: {nome_disciplina}")

    # Ancoragem precisa no card da disciplina
    card_disciplina = (
        ava_page.locator(".card")
        .filter(has=ava_page.locator("h2", has_text=nome_disciplina))
        .first
    )

    card_disciplina.locator("button", has_text="ACESSAR SUA SALA DE AULA").click(
        force=True
    )

    ava_page.wait_for_load_state("networkidle")
    ava_page.wait_for_timeout(3000)

    print("-> Navegando pelas sanfonas da sala de aula...")

    def obter_botao_estudar():
        return (
            ava_page.get_by_text("Clique aqui para estudar o conteúdo", exact=False)
            .locator("visible=true")
            .first
        )

    # ---------------------------------------------------------------------------------
    # ESTRATÉGIA DE NAVEGAÇÃO E CAPTURA DA NOVA ABA DE VÍDEO
    # ---------------------------------------------------------------------------------

    # TENTATIVA 1
    try:
        with context.expect_page(timeout=3000) as video_page_info:
            obter_botao_estudar().click(timeout=2000)
        print("      [✓] A sanfona já estava aberta. Acessando a aula...")
        video_page = video_page_info.value
        video_page.wait_for_load_state("networkidle")
        return video_page
    except (PlaywrightError, TimeoutError):
        pass

    # TENTATIVA 2: Nível 1
    print("      [~] Abrindo a sanfona principal (Nível 1)...")
    try:
        ava_page.get_by_text("Início:", exact=False).locator(
            "visible=true"
        ).first.click(force=True)
        ava_page.wait_for_timeout(2000)

        with context.expect_page(timeout=3000) as video_page_info:
            obter_botao_estudar().click(timeout=2000)
        print("      [✓] Acessando a aula após Nível 1...")
        video_page = video_page_info.value
        video_page.wait_for_load_state("networkidle")
        return video_page
    except (PlaywrightError, TimeoutError):
        pass

    # TENTATIVA 3: Nível 2
    print(f"      [~] Abrindo a sub-sanfona 'Disciplina: {nome_disciplina}'...")
    try:
        aba_disciplina = (
            ava_page.locator("div")
            .filter(has_text="Disciplina:")
            .filter(has_text=nome_disciplina)
            .locator("visible=true")
            .last
        )
        aba_disciplina.click(force=True)

        print("      [~] Aguardando 3 segundos...")
        ava_page.wait_for_timeout(3000)

        print("      [~] Clicando em 'Clique aqui para estudar o conteúdo'...")

        # Captura a nova aba gerada pelo clique
        try:
            with context.expect_page(timeout=5000) as video_page_info:
                obter_botao_estudar().click(timeout=5000, force=True)
            ava_page = video_page_info.value
        except TimeoutError:
            # Caso navegue na mesma aba
            ava_page = context.pages[-1]

        print("      [✓] Acessando a aula após Nível 2...")
        ava_page.wait_for_load_state("networkidle")
    except PlaywrightError as err:
        print(
            f"-> [!] Não foi possível clicar no botão de estudo: {err.message.splitlines()[0]}"
        )

    return ava_page
