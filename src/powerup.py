"""PowerUp colecionável do Veridis Quo.

Aparece com chance ao destruir um asteroide. Flutua pela tela e anima
alternando entre o sprite original e seu reflexo horizontal. É aqui
que a quarta transformação obrigatória — reflexão (flip) — ganha
destaque visual: como o sprite é assimétrico (brilho do lado esquerdo,
sombra do lado direito), o espelhamento fica inegavelmente perceptível,
com a luz pulando de um lado para o outro a cada `TEMPO_FLIP` segundos.

Essa escolha de design foi intencional: a reflexão em um sprite
simétrico seria indetectável (o resultado visual seria idêntico ao
original). Sempre que for demonstrar reflexão em computação gráfica,
use figuras assimétricas — esse é um princípio geral.

Também aplica:
    translacao : flutuação linear pelo espaço com wrap-around.
    escala     : "respiração" senoidal mais sutil que a do asteroide.
"""
import math
import random
import pygame

from src.transforms import translacao, reflexao, escala
from src.assets import load_sprite


RAIO = 14                   # raio lógico usado para colisão
TEMPO_FLIP = 0.35           # segundos entre um flip e o próximo
TEMPO_VIDA = 9.0            # segundos em tela antes de sumir
VELOCIDADE = 65             # módulo da velocidade (pixels/s)
ESCALA_AMP = 0.10           # amplitude do "breathing"
ESCALA_FREQ = 4.0           # frequência do "breathing" (rad/s)
CHANCE_SPAWN = 0.22         # chance de cair ao destruir um asteroide


def _build_powerup_surface() -> pygame.Surface:
    """Sprite procedural do power-up (diamante brilhante assimétrico).

    Claramente assimétrico: "luz" do lado esquerdo + sombra do lado direito.
    Assim a reflexão horizontal fica bem perceptível (luz pula de lado).
    Fallback usado quando não existe assets/images/powerup.png.
    """
    tamanho = RAIO * 2 + 12
    surf = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
    cx, cy = tamanho // 2, tamanho // 2

    # Halo externo (brilho difuso em torno do item).
    for r, alpha in [(RAIO + 4, 40), (RAIO + 2, 70)]:
        halo = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
        pygame.draw.circle(halo, (255, 230, 120, alpha), (cx, cy), r)
        surf.blit(halo, (0, 0))

    # Corpo: diamante/losango amarelo.
    diamante = [
        (cx, cy - RAIO),
        (cx + RAIO * 0.8, cy),
        (cx, cy + RAIO),
        (cx - RAIO * 0.8, cy),
    ]
    pygame.draw.polygon(surf, (255, 200, 50), diamante)
    pygame.draw.polygon(surf, (255, 255, 200), diamante, width=2)

    # Sombra do lado direito (torna a assimetria perceptível no flip).
    sombra = [
        (cx, cy - RAIO),
        (cx + RAIO * 0.8, cy),
        (cx, cy + RAIO),
    ]
    sombra_surf = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
    pygame.draw.polygon(sombra_surf, (0, 0, 0, 90), sombra)
    surf.blit(sombra_surf, (0, 0))

    # Brilho principal do lado esquerdo (fica bem visível no flip).
    pygame.draw.circle(surf, (255, 255, 255), (cx - RAIO // 2, cy - RAIO // 3), 4)
    pygame.draw.circle(surf, (255, 255, 200), (cx - RAIO // 3, cy), 2)

    return surf


class PowerUp:
    """Item colecionável que concede +1 vida ao ser coletado."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        angulo = random.uniform(0, 2 * math.pi)
        self.vx = math.cos(angulo) * VELOCIDADE
        self.vy = math.sin(angulo) * VELOCIDADE

        self.tempo_vida = TEMPO_VIDA
        self.vivo = True

        # Animação
        self.timer_flip = 0.0
        self.flipado = False           # estado atual do flip horizontal
        self.fase_escala = random.uniform(0, 2 * math.pi)
        self.escala_atual = 1.0

        self._sprite_base = load_sprite("powerup", _build_powerup_surface)

    # ----------------------------------------------------------------- update
    def update(self, dt: float, largura: int, altura: int):
        # Translacao + wrap-around: o power-up flutua pelo campo de jogo.
        self.x, self.y = translacao((self.x, self.y), (self.vx * dt, self.vy * dt))
        self.x %= largura
        self.y %= altura

        # Alterna o flip horizontal periodicamente — reflexão em ação.
        self.timer_flip += dt
        if self.timer_flip >= TEMPO_FLIP:
            self.timer_flip = 0.0
            self.flipado = not self.flipado

        # Breathing leve via escala.
        self.fase_escala += ESCALA_FREQ * dt
        self.escala_atual = 1.0 + ESCALA_AMP * math.sin(self.fase_escala)

        # Expiração.
        self.tempo_vida -= dt
        if self.tempo_vida <= 0:
            self.vivo = False

    # ------------------------------------------------------------------- draw
    def draw(self, screen: pygame.Surface):
        # Aplica escala (breathing) e, se for o caso, reflexão horizontal.
        sprite = escala(self._sprite_base, self.escala_atual)
        if self.flipado:
            sprite = reflexao(sprite, horizontal=True, vertical=False)

        rect = sprite.get_rect(center=(int(self.x), int(self.y)))
        # Pisca nos últimos 2 segundos como aviso de que vai sumir.
        if self.tempo_vida < 2.0 and int(self.tempo_vida * 8) % 2 == 0:
            return
        screen.blit(sprite, rect)

    # -------------------------------------------------------------- colisões
    def colide_com_ponto(self, px: float, py: float, raio_outro: float = 0.0) -> bool:
        return math.hypot(self.x - px, self.y - py) <= (RAIO + raio_outro)


def talvez_dropar(x: float, y: float) -> PowerUp | None:
    """Com chance CHANCE_SPAWN, retorna um PowerUp em (x, y); senão None."""
    if random.random() < CHANCE_SPAWN:
        return PowerUp(x, y)
    return None
