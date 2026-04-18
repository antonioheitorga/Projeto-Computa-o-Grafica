"""Estados do jogo: Menu, Jogando e Game Over.

Implementa a máquina de estados simples que rege o fluxo do jogo:

    Menu  ---ENTER--->  Jogando  ---morre--->  Game Over
      ^                    |                        |
      |                    |---ESC------------------+
      +------ESC-----------+                        |
                                                    |
      <--------------ESC--------------------------- +

Cada estado herda de BaseState e implementa quatro métodos:
  - reset()            : reinicia o estado ao entrar nele
  - handle_events(ev)  : processa eventos discretos (KEYDOWN, QUIT)
  - update(dt)         : lógica contínua por frame
  - draw(screen)       : desenho na tela

A classe Game (em game.py) mantém o loop principal e chama esses
métodos no estado atual a cada iteração.
"""
import pygame

from src.player import Player, SHIP_RADIUS, Bullet
from src.asteroid import spawn_inicial
from src.powerup import talvez_dropar
from src.particles import explosao
from src.starfield import Starfield
from src.hud import HUD
from src import audio

# Parâmetros de gameplay do PlayingState
ASTEROIDES_INICIAIS = 4
INVULN_APOS_DANO = 1.8        # segundos de invulnerabilidade (piscando) após apanhar
ZONA_SEGURA_SPAWN = 140       # raio em volta da nave onde não nasce asteroide
VIDAS_MAX = 5

# Cores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (160, 160, 160)
YELLOW = (255, 215, 0)
RED = (220, 60, 60)


class BaseState:
    """Interface comum dos estados."""

    def __init__(self, game):
        self.game = game

    def reset(self):
        """Reinicia o estado ao entrar nele."""
        pass

    def handle_events(self, events):
        pass

    def update(self, dt: float):
        pass

    def draw(self, screen):
        pass


class MenuState(BaseState):
    """Tela inicial: mostra o nome do jogo e instrução de início."""

    def __init__(self, game):
        super().__init__(game)
        self.title_font = pygame.font.SysFont("Arial", 72, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 24)
        self.starfield = Starfield(game.screen.get_width(), game.screen.get_height())

    def update(self, dt: float):
        self.starfield.update(dt)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self.game.change_state("playing")
                elif event.key == pygame.K_ESCAPE:
                    self.game.quit()

    def draw(self, screen):
        screen.fill(BLACK)
        self.starfield.draw(screen)
        title = self.title_font.render("VERIDIS QUO", True, YELLOW)
        start = self.text_font.render("Pressione ENTER ou ESPAÇO para iniciar", True, WHITE)
        exit_msg = self.text_font.render("ESC para sair", True, GRAY)

        screen.blit(title, title.get_rect(center=(screen.get_width() // 2, 200)))
        screen.blit(start, start.get_rect(center=(screen.get_width() // 2, 420)))
        screen.blit(exit_msg, exit_msg.get_rect(center=(screen.get_width() // 2, 460)))


class PlayingState(BaseState):
    """Estado de gameplay. Será expandido com nave, asteroides e projéteis."""

    def __init__(self, game):
        super().__init__(game)
        self.score = 0
        self.lives = 3
        self.onda = 1
        self.player = None
        self.bullets = []
        self.asteroides = []
        self.powerups = []
        self.particles = []
        self.invuln = 0.0
        self.starfield = Starfield(game.screen.get_width(), game.screen.get_height())
        self.hud = HUD()

    def reset(self):
        self.score = 0
        self.lives = 3
        self.onda = 1
        largura = self.game.screen.get_width()
        altura = self.game.screen.get_height()
        self.player = Player(largura / 2, altura / 2)
        self.bullets = []
        self.asteroides = spawn_inicial(
            ASTEROIDES_INICIAIS, largura, altura,
            zona_segura=(largura / 2, altura / 2, ZONA_SEGURA_SPAWN),
        )
        self.powerups = []
        self.particles = []
        self.invuln = INVULN_APOS_DANO
        self.hud.mostrar_banner_onda(self.onda)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.change_state("menu")

    def update(self, dt: float):
        if self.player is None:
            return
        largura = self.game.screen.get_width()
        altura = self.game.screen.get_height()

        self.starfield.update(dt)

        teclas = pygame.key.get_pressed()
        self.player.handle_input(teclas, dt, self.bullets)
        self.player.update(dt, largura, altura)

        for b in self.bullets:
            b.update(dt, largura, altura)
        self.bullets = [b for b in self.bullets if b.vivo]

        for a in self.asteroides:
            a.update(dt, largura, altura)

        for p in self.powerups:
            p.update(dt, largura, altura)
        self.powerups = [p for p in self.powerups if p.vivo]

        for part in self.particles:
            part.update(dt)
        self.particles = [part for part in self.particles if part.vivo]

        self._processar_colisoes(dt)

        # Se todos os asteroides foram destruídos, avança para a próxima onda.
        if not self.asteroides:
            self.onda += 1
            self.asteroides = spawn_inicial(
                ASTEROIDES_INICIAIS + self.onda - 1, largura, altura,
                zona_segura=(self.player.x, self.player.y, ZONA_SEGURA_SPAWN),
            )
            self.hud.mostrar_banner_onda(self.onda)

        if self.invuln > 0:
            self.invuln -= dt

        self.hud.update(dt)

    def _processar_colisoes(self, dt: float):
        # Bullet x Asteroide
        novos = []
        for a in self.asteroides:
            destruido = False
            for b in self.bullets:
                if not b.vivo:
                    continue
                if a.colide_com_ponto(b.x, b.y, raio_outro=Bullet.RADIUS):
                    b.vivo = False
                    self.score += a.pontos
                    novos.extend(a.dividir())
                    # Chance de dropar um power-up no local da destruição.
                    drop = talvez_dropar(a.x, a.y)
                    if drop is not None:
                        self.powerups.append(drop)
                    # Efeito visual de explosão.
                    self.particles.extend(explosao(a.x, a.y))
                    audio.play_sfx("explosion")
                    destruido = True
                    break
            if not destruido:
                novos.append(a)
        self.asteroides = novos
        self.bullets = [b for b in self.bullets if b.vivo]

        # Player x PowerUp
        restantes = []
        for p in self.powerups:
            if p.colide_com_ponto(self.player.x, self.player.y, raio_outro=SHIP_RADIUS):
                if self.lives < VIDAS_MAX:
                    self.lives += 1
                self.score += 25
                audio.play_sfx("powerup")
            else:
                restantes.append(p)
        self.powerups = restantes

        # Player x Asteroide (só se não estiver invulnerável)
        if self.invuln <= 0:
            for a in self.asteroides:
                if a.colide_com_ponto(self.player.x, self.player.y, raio_outro=SHIP_RADIUS):
                    self.lives -= 1
                    self.invuln = INVULN_APOS_DANO
                    audio.play_sfx("hit")
                    # Reseta velocidade da nave para evitar re-colisão imediata.
                    self.player.vx = 0.0
                    self.player.vy = 0.0
                    if self.lives <= 0:
                        # Passa pontuação e onda para o Game Over.
                        go = self.game.states["gameover"]
                        go.final_score = self.score
                        go.final_onda = self.onda
                        self.game.change_state("gameover")
                    break

    def draw(self, screen):
        screen.fill(BLACK)
        self.starfield.draw(screen)

        for a in self.asteroides:
            a.draw(screen)

        for p in self.powerups:
            p.draw(screen)

        for part in self.particles:
            part.draw(screen)

        for b in self.bullets:
            b.draw(screen)

        if self.player is not None:
            # Pisca durante invulnerabilidade (efeito visual de dano).
            if self.invuln <= 0 or int(self.invuln * 10) % 2 == 0:
                self.player.draw(screen)

        self.hud.draw(
            screen,
            vidas=self.lives,
            score=self.score,
            onda=self.onda,
            invuln_restante=max(0.0, self.invuln),
            invuln_total=INVULN_APOS_DANO,
        )


class GameOverState(BaseState):
    """Tela de fim de jogo."""

    def __init__(self, game):
        super().__init__(game)
        self.title_font = pygame.font.SysFont("Arial", 60, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 24)
        self.final_score = 0
        self.final_onda = 1
        self.starfield = Starfield(game.screen.get_width(), game.screen.get_height())

    def update(self, dt: float):
        self.starfield.update(dt)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.game.change_state("playing")
                elif event.key == pygame.K_ESCAPE:
                    self.game.change_state("menu")

    def draw(self, screen):
        screen.fill(BLACK)
        self.starfield.draw(screen)
        title = self.title_font.render("GAME OVER", True, RED)
        score_msg = self.text_font.render(
            f"Pontuação final: {self.final_score}", True, YELLOW
        )
        onda_msg = self.text_font.render(
            f"Onda alcançada: {self.final_onda}", True, (120, 220, 255)
        )
        retry = self.text_font.render("ENTER para jogar novamente", True, WHITE)
        back = self.text_font.render("ESC para voltar ao menu", True, GRAY)
        cx = screen.get_width() // 2
        screen.blit(title, title.get_rect(center=(cx, 200)))
        screen.blit(score_msg, score_msg.get_rect(center=(cx, 290)))
        screen.blit(onda_msg, onda_msg.get_rect(center=(cx, 325)))
        screen.blit(retry, retry.get_rect(center=(cx, 400)))
        screen.blit(back, back.get_rect(center=(cx, 435)))
