import logging

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError

# Configuração do Logging para rastrear todos os passos e erros
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def reproduzir_aulas(page):
    logger.info("Carregando a lista de reprodução e aguardando estabilidade...")

    # 1. Aguarda os elementos principais com folga de tempo
    try:
        page.wait_for_selector("#videoIndex", state="visible", timeout=40000)
        page.wait_for_selector(
            "#id-iframe-player-videoteca", state="attached", timeout=40000
        )
        page.wait_for_timeout(5000)  # Tempo extra para a página assentar
    except TimeoutError:
        logger.error(
            "Tempo esgotado aguardando o carregamento da lista de aulas ou do player."
        )
        return

    # Conta o total de vídeos
    total_aulas = page.locator("#videoIndex > div").count()
    logger.info(f"Total de {total_aulas} aulas/atividades encontradas na fila.")

    for index in range(total_aulas):
        aula_item = page.locator("#videoIndex > div").nth(index)

        try:
            raw_text = aula_item.text_content()
            titulo = " ".join(raw_text.split()) if raw_text else f"Aula {index + 1}"
        except PlaywrightError:
            titulo = f"Aula {index + 1}"

        logger.info(f"Iniciando vídeo ({index + 1}/{total_aulas}): {titulo}")

        # ---------------------------------------------------------
        # SELEÇÃO NA PLAYLIST LATERAL
        # ---------------------------------------------------------
        try:
            aula_item.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)

            aula_item.click(force=True)
            logger.info("Carregando o vídeo no player central...")
            # Aguarda a transição do iFrame para evitar ler o vídeo anterior
            page.wait_for_timeout(6000)
        except PlaywrightError as err:
            logger.warning(
                f"Erro ao selecionar item na lista: {err.message.splitlines()[0]}"
            )
            continue

        # ---------------------------------------------------------
        # CLIQUE FÍSICO ÚNICO E CALIBRADO (Evita play/pause duplo)
        # ---------------------------------------------------------
        iframe_loc = page.locator("#id-iframe-player-videoteca").first

        try:
            iframe_loc.scroll_into_view_if_needed()
            page.wait_for_timeout(1500)

            logger.info("Acionando o botão de play no centro do vídeo...")
            box = iframe_loc.bounding_box()
            if box:
                # Clica exatamente no centro geométrico do iFrame
                page.mouse.click(
                    box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
                )
            else:
                iframe_loc.click(force=True)

            page.wait_for_timeout(2000)
        except PlaywrightError as err:
            logger.debug(
                f"Falha leve ao tentar clicar no iframe: {err.message.splitlines()[0]}"
            )

        # ---------------------------------------------------------
        # MONITORAMENTO BLINDADO VIA JAVASCRIPT
        # ---------------------------------------------------------
        logger.info("Reproduzindo... Aguardando término do vídeo.")
        video_concluido = False
        tentativas_sem_video = 0
        tentativas_pausado = 0

        while not video_concluido:
            video_state = None
            target_frame = None

            # Busca o vídeo acessando os frames ativamente (Evita o erro de "is_visible" e "Context Destroyed")
            for frame in page.frames:
                try:
                    if (
                        "videoteca" in frame.url
                        or frame.name == "id-iframe-player-videoteca"
                    ):
                        state = frame.evaluate("""() => {
                            const v = document.querySelector('video');
                            if (!v) return null;
                            return {
                                exists: true,
                                ended: v.ended,
                                currentTime: v.currentTime || 0,
                                duration: isNaN(v.duration) ? 0 : v.duration,
                                paused: v.paused
                            };
                        }""")
                        if state:
                            video_state = state
                            target_frame = frame
                            break
                except PlaywrightError as err:
                    logger.debug(
                        f"Erro ao avaliar frame na busca: {err.message.splitlines()[0]}"
                    )
                    continue

            # Se o vídeo não existe no DOM ainda
            if not video_state:
                tentativas_sem_video += 1
                if tentativas_sem_video >= 15:  # Desiste após ~30 segundos
                    logger.error(
                        "Vídeo não detectado na página após 30 segundos. Pulando."
                    )
                    video_concluido = True
                page.wait_for_timeout(2000)
                continue

            # O vídeo foi encontrado, reseta o contador de ausência
            tentativas_sem_video = 0

            c_time = video_state.get("currentTime", 0)
            dur = video_state.get("duration", 0)
            ended = video_state.get("ended", False)
            paused = video_state.get("paused", False)

            # AUTO-CURA (HEALING): Se o vídeo estiver pausado por algum motivo
            if paused:
                tentativas_pausado += 1
                if tentativas_pausado >= 3:  # Notou pausa por ~6 segundos seguidos
                    logger.info(
                        "Vídeo pausado detectado. Tentando forçar o play novamente..."
                    )
                    try:
                        if target_frame:
                            target_frame.locator("body").click(force=True, timeout=1000)
                            target_frame.evaluate("""() => {
                                const v = document.querySelector('video');
                                if (v) { v.muted = false; v.play().catch(()=>{}); }
                            }""")
                    except PlaywrightError as err:
                        logger.debug(
                            f"Erro ao tentar forçar play via JS: {err.message.splitlines()[0]}"
                        )
                    tentativas_pausado = 0  # Zera para aguardar mais 6 segundos antes da próxima tentativa
            else:
                tentativas_pausado = 0

            # CRITÉRIOS DE SUCESSO (O Vídeo Acabou?)
            if (
                ended
                or (dur > 0 and c_time >= (dur - 1.5))
                or (paused and dur > 0 and (dur - c_time) < 5.0 and c_time > 10)
            ):
                # O player travou o vídeo propositalmente nos segundos finais para mostrar a tela final
                video_concluido = True

            # Pausa do loop de monitoramento
            if not video_concluido:
                page.wait_for_timeout(2000)

        if video_concluido:
            logger.info("Bloco finalizado com sucesso!")

        # Pausa extra antes de iniciar o próximo vídeo da lista (Deixa o site registrar o progresso)
        page.wait_for_timeout(4000)
