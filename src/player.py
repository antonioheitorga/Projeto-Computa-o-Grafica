"""Nave do jogador (Player) e projétil (Bullet).

Estilo Asteroids clássico: rotação livre 360°, propulsão com inércia,
wrap-around nas bordas da tela.

Aplica as transformações geométricas definidas em src/transforms.py:
    - translacao : movimento frame a frame da nave e dos projéteis.
    - rotacao    : orientação do sprite da nave conforme o ângulo atual.

Observação importante sobre o eixo Y
------------------------------------
Em matemática convencional o eixo Y cresce para cima, mas no Pygame
(como em quase todo framework gráfico) Y cresce para baixo, pois as
coordenadas de tela seguem a convenção de "pixel (0,0) no canto
superior esquerdo". Por isso usamos `-sin(angulo)` em vez de
`+sin(angulo)` ao converter ângulo em componentes de velocidade:
isso garante que ângulo=90° represente "para cima" tanto no cálculo
físico quanto no sprite visual.

Observação sobre delta time (dt)
--------------------------------
Todas as grandezas dinâmicas são expressas por segundo (graus/s,
pixels/s, pixels/s²). Multiplicamos por `dt` a cada update para
tornar o movimento independente da taxa de frames. Se o jogo rodar
a 30 ou 120 FPS, a nave continua se movendo na mesma velocidade.
"""
import math
import pygame

from src.transforms import translacao, rotacao
from src.assets import load_sprite
from src import audio


# ---------------------------------------------------------------------------
# Constantes de gameplay (ajustáveis)
# ---------------------------------------------------------------------------
ROTATION_SPEED = 220.0      # graus por segundo
THRUST_ACCEL = 260.0        # pixels/s^2 aplicados na direção da nave
MAX_SPEED = 420.0           # velocidade máxima (pixels/s)
FRICTION = 0.6              # atrito por segundo (simula arrasto leve do espaço)
BULLET_SPEED = 520.0        # velocidade do projétil (pixels/s)
BULLET_LIFETIME = 1.1       # segundos antes do projétil sumir
FIRE_COOLDOWN = 0.22        # segundos entre tiros

SHIP_RADIUS = 16            # raio do sprite da nave (para colisões)


def _build_ship_surface_proc() -> pygame.Surface:
    """Sprite procedural da nave (fallback caso não haja assets/images/ship.png).

    Nave aponta para cima (ângulo 90° em coordenadas Pygame).
    """
    size = SHIP_RADIUS * 2 + 6
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2

    # Corpo (triângulo principal, preenchido).
    corpo = [
        (cx, cy - SHIP_RADIUS),
        (cx - SHIP_RADIUS * 0.75, cy + SHIP_RADIUS * 0.8),
        (cx + SHIP_RADIUS * 0.75, cy + SHIP_RADIUS * 0.8),
    ]
    pygame.draw.polygon(surf, (60, 70, 100), corpo)
    pygame.draw.polygon(surf, (220, 230, 255), corpo, width=2)

    # Cockpit (círculo claro perto do nariz).
    pygame.draw.circle(surf, (140, 200, 255), (cx, cy - SHIP_RADIUS // 3), 3)

    # Traço central vertical (detalhe).
    pygame.draw.line(surf, (200, 210, 240),
                     (cx, cy - SHIP_RADIUS + 5),
                     (cx, cy + SHIP_RADIUS * 0.5), 1)
    return surf


def _build_flame_surface() -> pygame.Surface:
    """Chama de propulsão da nave (triangulinho laranja que aparece atrás)."""
    size = SHIP_RADIUS * 2 + 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    # Triângulo apontando para baixo, atrás da nave.
    chama = [
        (cx, cy + SHIP_RADIUS + 4),
        (cx - 5, cy + SHIP_RADIUS * 0.8),
        (cx + 5, cy + SHIP_RADIUS * 0.8),
    ]
    pygame.draw.polygon(surf, (255, 160, 60), chama)
    # Núcleo mais claro.
    nucleo = [
        (cx, cy + SHIP_RADIUS + 1),
        (cx - 2, cy + SHIP_RADIUS * 0.85),
        (cx + 2, cy + SHIP_RADIUS * 0.85),
    ]
    pygame.draw.polygon(surf, (255, 240, 200), nucleo)
    return surf


class Bullet:
    """Projétil disparado pela nave. Move em linha reta com tempo de vida limitado."""

    RADIUS = 2

    def __init__(self, x: float, y: float, angulo_graus: float):
        # Pygame usa Y invertido (cresce para baixo); o ajuste de sinal em sin
        # faz com que ângulo=90° aponte para cima, coerente com o sprite.
        rad = math.radians(angulo_graus)
        self.x = x
        self.y = y
        self.vx = math.cos(rad) * BULLET_SPEED
        self.vy = -math.sin(rad) * BULLET_SPEED
        self.tempo_vida = BULLET_LIFETIME
        self.vivo = True

    def update(self, dt: float, largura: int, altura: int):
        # Translacao do projétil frame a frame.
        self.x, self.y = translacao((self.x, self.y), (self.vx * dt, self.vy * dt))

        # Projétil some ao sair da tela (sem wrap-around).
        if self.x < 0 or self.x > largura or self.y < 0 or self.y > altura:
            self.vivo = False
            return

        self.tempo_vida -= dt
        if self.tempo_vida <= 0:
            self.vivo = False

    def draw(self, screen: pygame.Surface):
        pygame.draw.circle(screen, (255, 255, 180),
                           (int(self.x), int(self.y)), Bullet.RADIUS)


class Player:
    """Nave do jogador. Rotaciona livre, acelera no próprio eixo e atira."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        # Ângulo em graus. 90° = apontando para cima (sprite base).
        self.angulo = 90.0
        self.cooldown = 0.0
        self.acelerando = False

        # Sprite base (nunca modificado, sempre transformado a partir daqui).
        # Tenta carregar assets/images/ship.png; se não existir, usa o procedural.
        self._sprite_base = load_sprite("ship", _build_ship_surface_proc)
        self._sprite_chama = _build_flame_surface()

    # ------------------------------------------------------------------ input
    def handle_input(self, teclas, dt: float, bullets: list):
        """Lê o estado do teclado e aplica rotação/propulsão/tiro."""
        # Rotação (esquerda/direita).
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            self.angulo += ROTATION_SPEED * dt
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            self.angulo -= ROTATION_SPEED * dt

        # Propulsão no eixo atual.
        self.acelerando = bool(teclas[pygame.K_UP] or teclas[pygame.K_w])
        if self.acelerando:
            rad = math.radians(self.angulo)
            self.vx += math.cos(rad) * THRUST_ACCEL * dt
            self.vy += -math.sin(rad) * THRUST_ACCEL * dt

        # Tiro (respeita cooldown).
        self.cooldown = max(0.0, self.cooldown - dt)
        if teclas[pygame.K_SPACE] and self.cooldown <= 0.0:
            bullets.append(Bullet(self.x, self.y, self.angulo))
            self.cooldown = FIRE_COOLDOWN
            audio.play_sfx("shoot")

    # ----------------------------------------------------------------- update
    def update(self, dt: float, largura: int, altura: int):
        # Atrito suave para a nave não acelerar infinitamente.
        fator_atrito = max(0.0, 1.0 - FRICTION * dt)
        self.vx *= fator_atrito
        self.vy *= fator_atrito

        # Clamp de velocidade máxima.
        velocidade = math.hypot(self.vx, self.vy)
        if velocidade > MAX_SPEED:
            escala_v = MAX_SPEED / velocidade
            self.vx *= escala_v
            self.vy *= escala_v

        # Translacao da posição usando a função reutilizável.
        self.x, self.y = translacao((self.x, self.y), (self.vx * dt, self.vy * dt))

        # Wrap-around nas bordas (comportamento clássico do Asteroids).
        self.x %= largura
        self.y %= altura

    # ------------------------------------------------------------------- draw
    def draw(self, screen: pygame.Surface):
        # Desenha a chama de propulsão primeiro (atrás da nave), se acelerando.
        # A chama é rotacionada junto com a nave para ficar coerente visualmente.
        if self.acelerando:
            chama = rotacao(self._sprite_chama, self.angulo - 90.0)
            rect_chama = chama.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(chama, rect_chama)

        # Rotação do sprite. O sprite base aponta para 90° (cima),
        # então subtraímos 90° para alinhar com o ângulo da nave.
        sprite_rotacionado = rotacao(self._sprite_base, self.angulo - 90.0)
        rect = sprite_rotacionado.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(sprite_rotacionado, rect)
