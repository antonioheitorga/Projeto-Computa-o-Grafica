"""Áudio do jogo: música de fundo + efeitos sonoros (SFX).

Segue a mesma filosofia de `src/assets.py`: se o arquivo de áudio não
existir em `assets/audio/`, o módulo falha silenciosamente (o jogo
continua rodando, só sem som). Assim é possível desenvolver / testar
sem nenhum asset de áudio no disco.

Arquivos reconhecidos (coloque em `assets/audio/`):
    music_menu.ogg    — música da tela de menu
    music_game.ogg    — música durante o gameplay
    shoot.wav         — tiro da nave
    explosion.wav     — asteroide destruído
    powerup.wav       — coleta de power-up
    hit.wav           — nave recebe dano

Formatos suportados: OGG (preferido), WAV, MP3. OGG costuma ser o
mais confiável em pygame entre plataformas.
"""
import os
import pygame


AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "audio")

# Nomes lógicos → lista de extensões aceitáveis (primeira encontrada vence).
_EXTS = (".ogg", ".wav", ".mp3")

# Cache de Sound objects já carregados.
_sfx_cache: dict[str, pygame.mixer.Sound | None] = {}
_mixer_ok = False
_volume_music = 0.35
_volume_sfx = 0.55


def _find(nome: str) -> str | None:
    for ext in _EXTS:
        caminho = os.path.join(AUDIO_DIR, f"{nome}{ext}")
        if os.path.isfile(caminho):
            return caminho
    return None


def init() -> None:
    """Inicializa o mixer do pygame. Silencioso se falhar (sem placa, headless, etc.)."""
    global _mixer_ok
    try:
        pygame.mixer.init()
        _mixer_ok = True
    except pygame.error:
        _mixer_ok = False


def play_music(nome: str, loop: bool = True) -> None:
    """Toca música de fundo em loop. Troca suave se já houver outra tocando."""
    if not _mixer_ok:
        return
    caminho = _find(nome)
    if caminho is None:
        pygame.mixer.music.stop()
        return
    try:
        pygame.mixer.music.load(caminho)
        pygame.mixer.music.set_volume(_volume_music)
        pygame.mixer.music.play(-1 if loop else 0)
    except pygame.error:
        pass


def stop_music() -> None:
    if _mixer_ok:
        pygame.mixer.music.stop()


def play_sfx(nome: str) -> None:
    """Toca um efeito sonoro (não bloqueia). Cacheia o Sound após primeiro uso."""
    if not _mixer_ok:
        return
    if nome not in _sfx_cache:
        caminho = _find(nome)
        if caminho is None:
            _sfx_cache[nome] = None
        else:
            try:
                snd = pygame.mixer.Sound(caminho)
                snd.set_volume(_volume_sfx)
                _sfx_cache[nome] = snd
            except pygame.error:
                _sfx_cache[nome] = None
    snd = _sfx_cache[nome]
    if snd is not None:
        snd.play()
