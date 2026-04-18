"""Asset loader com fallback procedural.

Tenta carregar um PNG de assets/images/<nome>.png. Se o arquivo existir,
retorna a Surface carregada. Se não existir, chama a função fallback
(que desenha o sprite proceduralmente).

Assim, a equipe pode substituir a arte por assets reais (ex: Kenney.nl,
OpenGameArt) sem mexer em uma linha de código dos módulos de gameplay.

Nota sobre pixels e resolução
-----------------------------
Todas as Surfaces carregadas por pygame.image.load são matrizes de
pixels RGBA — cada pixel é uma quádrupla (R, G, B, A) na faixa
[0, 255]. A resolução do sprite não precisa coincidir com a
resolução da tela: na hora de desenhar, aplicamos escala/rotacao
via src.transforms para ajustar o sprite ao contexto visual.

Chamamos convert_alpha() após o load para pré-converter a imagem
ao formato de pixel interno do display, acelerando blits futuros.
"""
import os
from typing import Callable

import pygame


ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "images")


def load_sprite(nome: str, fallback: Callable[[], pygame.Surface]) -> pygame.Surface:
    """Carrega assets/images/<nome>.png; se não existir, usa o fallback.

    O fallback é uma função que retorna uma Surface desenhada por código.
    """
    caminho = os.path.join(ASSETS_DIR, f"{nome}.png")
    if os.path.isfile(caminho):
        try:
            return pygame.image.load(caminho).convert_alpha()
        except pygame.error:
            # Arquivo existe mas falhou ao carregar — usa o fallback mesmo assim.
            pass
    return fallback()


def tem_asset(nome: str) -> bool:
    """Retorna True se existe um PNG custom para o sprite pedido."""
    caminho = os.path.join(ASSETS_DIR, f"{nome}.png")
    return os.path.isfile(caminho)
