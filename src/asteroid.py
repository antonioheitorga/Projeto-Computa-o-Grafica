"""Asteroides do jogo Veridis Quo.

Cada asteroide combina três das quatro transformações geométricas
obrigatórias:

    translacao : movimento linear pelo espaço (com wrap-around nas bordas).
    rotacao    : giro contínuo sobre o próprio eixo.
    escala     : pulso senoidal que encolhe/aumenta o sprite periodicamente,
                 além do tamanho base por tier (grande / médio / pequeno).

O pulso de escala é calculado por escala(t) = 1 + A * sin(f * t + phi)
onde A = amplitude (PULSO_AMPLITUDE), f = frequência (PULSO_FREQ) e phi
é uma fase aleatória por asteroide (para cada rocha pulsar fora de
sincronia com as outras, dando um efeito mais natural).

Ao serem destruídos, asteroides grandes e médios se dividem em dois
menores (mecânica clássica de Asteroids, 1979), o que torna a mudança
de escala ainda mais perceptível em gameplay: o asteroide "grande"
subitamente se fragmenta em fragmentos "médios" — uma redução
abrupta de escala que complementa o pulso contínuo.
"""
import math
import random
import pygame

from src.transforms import translacao, rotacao, escala
from src.assets import load_sprite, tem_asset


# ---------------------------------------------------------------------------
# Configurações por tier
# ---------------------------------------------------------------------------
# Cada tier define (raio_base, velocidade_min, velocidade_max, pontos, proximo_tier)
TIERS = {
    "grande":  {"raio": 42, "vel_min": 40,  "vel_max": 90,  "pontos": 20, "proximo": "medio"},
    "medio":   {"raio": 26, "vel_min": 70,  "vel_max": 130, "pontos": 50, "proximo": "pequeno"},
    "pequeno": {"raio": 14, "vel_min": 110, "vel_max": 180, "pontos": 100, "proximo": None},
}

# Amplitude do pulso de escala (0.15 = varia entre 85% e 115% do tamanho base).
PULSO_AMPLITUDE = 0.15
# Velocidade angular do pulso (rad/s).
PULSO_FREQ = 3.2


def _build_asteroid_surface(raio: int, sementes: int = 12) -> pygame.Surface:
    """Sprite procedural de asteroide (polígono irregular com textura rochosa).

    Fallback usado quando não existe assets/images/asteroid.png.
    """
    tamanho = raio * 2 + 8
    surf = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
    centro = tamanho // 2

    # Contorno principal com raios variáveis.
    pontos = []
    for i in range(sementes):
        angulo = (2 * math.pi * i) / sementes
        variacao = random.uniform(0.72, 1.0)
        px = centro + math.cos(angulo) * raio * variacao
        py = centro + math.sin(angulo) * raio * variacao
        pontos.append((px, py))

    # Preenchimento (cor base) + contorno claro.
    pygame.draw.polygon(surf, (90, 85, 95), pontos)
    pygame.draw.polygon(surf, (200, 195, 210), pontos, width=2)

    # Crateras: círculos pequenos e escuros distribuídos na rocha.
    num_crateras = max(2, raio // 10)
    for _ in range(num_crateras):
        ang = random.uniform(0, 2 * math.pi)
        r = random.uniform(0, raio * 0.55)
        cx = centro + math.cos(ang) * r
        cy = centro + math.sin(ang) * r
        raio_cratera = random.randint(2, max(3, raio // 8))
        pygame.draw.circle(surf, (60, 55, 65), (int(cx), int(cy)), raio_cratera)
        pygame.draw.circle(surf, (130, 125, 140), (int(cx), int(cy)), raio_cratera, 1)
    return surf


class Asteroid:
    """Asteroide com movimento linear, rotação contínua e escala pulsante."""

    def __init__(self, x: float, y: float, tier: str = "grande",
                 vx: float | None = None, vy: float | None = None):
        if tier not in TIERS:
            raise ValueError(f"Tier inválido: {tier}")
        self.tier = tier
        cfg = TIERS[tier]
        self.raio = cfg["raio"]
        self.pontos = cfg["pontos"]

        self.x = x
        self.y = y

        # Se vx/vy não foram passados, sorteia uma direção aleatória.
        if vx is None or vy is None:
            velocidade = random.uniform(cfg["vel_min"], cfg["vel_max"])
            angulo = random.uniform(0, 2 * math.pi)
            vx = math.cos(angulo) * velocidade
            vy = math.sin(angulo) * velocidade
        self.vx = vx
        self.vy = vy

        # Ângulo atual (para rotação visual) e velocidade angular.
        self.angulo = random.uniform(0, 360)
        self.vel_angular = random.uniform(-90, 90)  # graus/segundo

        # Fase do pulso de escala, para cada asteroide pulsar fora de sincronia.
        self.fase_pulso = random.uniform(0, 2 * math.pi)
        self.escala_atual = 1.0  # último fator de escala aplicado (usado na colisão)

        self.vivo = True
        # Tenta carregar um PNG customizado por tier (ex: asteroid_grande.png).
        # Se não houver, gera proceduralmente.
        nome_asset = f"asteroid_{tier}"
        if tem_asset(nome_asset):
            self._sprite_base = load_sprite(nome_asset, lambda: _build_asteroid_surface(self.raio))
        else:
            self._sprite_base = _build_asteroid_surface(self.raio)

    # ----------------------------------------------------------------- update
    def update(self, dt: float, largura: int, altura: int):
        # Translacao (movimento linear).
        self.x, self.y = translacao((self.x, self.y), (self.vx * dt, self.vy * dt))

        # Wrap-around nas bordas (asteroides não somem quando saem).
        self.x %= largura
        self.y %= altura

        # Atualiza ângulo (rotação contínua).
        self.angulo = (self.angulo + self.vel_angular * dt) % 360

        # Atualiza fase do pulso de escala.
        self.fase_pulso += PULSO_FREQ * dt
        self.escala_atual = 1.0 + PULSO_AMPLITUDE * math.sin(self.fase_pulso)

    # ------------------------------------------------------------------- draw
    def draw(self, screen: pygame.Surface):
        # Composição de transformações: primeiro escala, depois rotação.
        # A ordem importa! Em álgebra de matrizes: M_total = R * S, aplicado
        # a um ponto p como M_total * p = R * (S * p). Aplicar escala antes da
        # rotação garante que o eixo de rotação (centro do sprite) não sofra
        # deformação e que a imagem gire inteira sem distorção.
        sprite_escalado = escala(self._sprite_base, self.escala_atual)
        sprite_final = rotacao(sprite_escalado, self.angulo)
        rect = sprite_final.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(sprite_final, rect)

    # -------------------------------------------------------------- colisões
    def raio_efetivo(self) -> float:
        """Raio atual considerando o pulso de escala. Usado para colisão."""
        return self.raio * self.escala_atual

    def colide_com_ponto(self, px: float, py: float, raio_outro: float = 0.0) -> bool:
        return math.hypot(self.x - px, self.y - py) <= (self.raio_efetivo() + raio_outro)

    # -------------------------------------------------------------- splitting
    def dividir(self) -> list["Asteroid"]:
        """Ao ser destruído, gera 2 asteroides do tier seguinte (se houver)."""
        proximo = TIERS[self.tier]["proximo"]
        if proximo is None:
            return []

        filhos = []
        for _ in range(2):
            # Direcao dos filhos derivada da velocidade atual + variação.
            velocidade_pai = math.hypot(self.vx, self.vy)
            nova_vel = velocidade_pai * random.uniform(1.05, 1.35)
            angulo = math.atan2(self.vy, self.vx) + random.uniform(-1.0, 1.0)
            vx = math.cos(angulo) * nova_vel
            vy = math.sin(angulo) * nova_vel
            filhos.append(Asteroid(self.x, self.y, tier=proximo, vx=vx, vy=vy))
        return filhos


def spawn_inicial(n: int, largura: int, altura: int,
                  zona_segura: tuple[float, float, float] | None = None) -> list[Asteroid]:
    """Cria n asteroides grandes em posições aleatórias.

    zona_segura: tupla (cx, cy, raio) em que não pode nascer asteroide
    (para não spawnar em cima do jogador).
    """
    asteroides = []
    tentativas_max = 30
    for _ in range(n):
        for _ in range(tentativas_max):
            x = random.uniform(0, largura)
            y = random.uniform(0, altura)
            if zona_segura is not None:
                cx, cy, raio = zona_segura
                if math.hypot(x - cx, y - cy) < raio:
                    continue
            asteroides.append(Asteroid(x, y, tier="grande"))
            break
    return asteroides
