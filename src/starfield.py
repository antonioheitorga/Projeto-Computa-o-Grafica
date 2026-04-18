"""Fundo estelado com paralaxe.

Três camadas de estrelas se movem em velocidades diferentes para dar
sensação de profundidade:
    - camada de fundo  : 80 estrelas pequenas e lentas (18 px/s).
    - camada do meio   : 50 estrelas médias (36 px/s).
    - camada da frente : 25 estrelas grandes e rápidas (65 px/s).

Esse efeito é chamado *paralaxe* — o mesmo princípio usado em jogos
2D de plataforma desde os anos 80 para simular profundidade em cenas
bidimensionais. Objetos distantes movem-se mais devagar que objetos
próximos, imitando a perspectiva do olho humano.

Aqui a paralaxe é apenas visual (o jogo não tem câmera que se mova),
mas o conceito tem papel central em renderização 3D, onde a projeção
perspectiva transforma coordenadas 3D em 2D justamente mapeando
profundidade em velocidade de deslocamento aparente.

Exemplifica translacao em ação ao nível do cenário — não só objetos
jogáveis, mas também elementos de fundo podem ser transladados a cada
frame para criar atmosfera.
"""
import random
import pygame

from src.transforms import translacao


# Config por camada: (quantidade, velocidade_y, tamanho, cor)
CAMADAS = [
    (80, 18,  1, (120, 120, 140)),  # fundo — longe, lenta
    (50, 36,  1, (180, 180, 200)),  # meio
    (25, 65,  2, (230, 230, 250)),  # frente — perto, rápida
]


class Starfield:
    def __init__(self, largura: int, altura: int):
        self.largura = largura
        self.altura = altura
        # estrelas: lista de tuplas [x, y, vy, tamanho, cor]
        self.estrelas = []
        for qtd, vy, tam, cor in CAMADAS:
            for _ in range(qtd):
                x = random.uniform(0, largura)
                y = random.uniform(0, altura)
                self.estrelas.append([x, y, vy, tam, cor])

    def update(self, dt: float):
        for s in self.estrelas:
            # Translacao vertical.
            s[0], s[1] = translacao((s[0], s[1]), (0, s[2] * dt))
            # Wrap-around vertical (entram por cima ao sair por baixo).
            if s[1] > self.altura:
                s[1] = 0
                s[0] = random.uniform(0, self.largura)

    def draw(self, screen: pygame.Surface):
        for x, y, _vy, tam, cor in self.estrelas:
            if tam == 1:
                screen.set_at((int(x), int(y)), cor)
            else:
                pygame.draw.circle(screen, cor, (int(x), int(y)), tam)
