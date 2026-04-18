"""Sistema simples de partículas para explosões.

Cada partícula é um ponto com posição, velocidade, cor e tempo de vida.
Ao destruir um asteroide, geramos uma "nuvem" de partículas que se
irradiam radialmente do ponto de impacto, cada uma seguindo uma
trajetória aleatória e desaparecendo em uma fração de segundo.

Demonstra translacao em grande escala: em 14 partículas por explosão
+ quatro asteroides por onda + divisão em dois filhos por destruição,
em poucos segundos centenas de pontos estão sendo transladados por
frame. O custo de cada chamada a translacao() é O(1), o que torna
viável aplicar a transformação individualmente em cada entidade.

Serve apenas como polimento visual — não interfere em colisões.
"""
import math
import random
import pygame

from src.transforms import translacao


class Particle:
    def __init__(self, x: float, y: float, vx: float, vy: float,
                 cor: tuple[int, int, int], tempo_vida: float):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.cor = cor
        self.tempo_vida = tempo_vida
        self.tempo_total = tempo_vida
        self.vivo = True

    def update(self, dt: float):
        self.x, self.y = translacao((self.x, self.y), (self.vx * dt, self.vy * dt))
        # Desacelera com o tempo (arrasto leve).
        self.vx *= 0.96
        self.vy *= 0.96
        self.tempo_vida -= dt
        if self.tempo_vida <= 0:
            self.vivo = False

    def draw(self, screen: pygame.Surface):
        # Fade conforme o tempo de vida acaba.
        alpha = max(0, min(255, int(255 * (self.tempo_vida / self.tempo_total))))
        cor = (*self.cor, alpha)
        surf = pygame.Surface((4, 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, cor, (2, 2), 2)
        screen.blit(surf, (int(self.x) - 2, int(self.y) - 2))


def explosao(x: float, y: float, quantidade: int = 14) -> list[Particle]:
    """Gera uma nuvem de partículas irradiando do ponto (x, y)."""
    particulas = []
    for _ in range(quantidade):
        angulo = random.uniform(0, 2 * math.pi)
        velocidade = random.uniform(60, 200)
        vx = math.cos(angulo) * velocidade
        vy = math.sin(angulo) * velocidade
        cor = random.choice([(255, 200, 80), (255, 150, 60), (220, 220, 230)])
        tempo = random.uniform(0.35, 0.75)
        particulas.append(Particle(x, y, vx, vy, cor, tempo))
    return particulas
