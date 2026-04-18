"""Classe principal do jogo: janela, game loop e orquestração de estados.

O que é um "game loop"
----------------------
O coração de todo jogo é um loop que se repete 60 vezes por segundo
(ou seja lá qual for o FPS alvo). Cada iteração executa três fases:

    1. INPUT  — ler eventos do SO / teclado / mouse
    2. UPDATE — atualizar lógica (posições, colisões, timers, IA)
    3. DRAW   — renderizar o quadro atual na tela

No fim de cada iteração chamamos pygame.display.flip() para trocar o
buffer offscreen com o buffer visível (double buffering), evitando
tearing visual.

O clock.tick(FPS) faz duas coisas: (1) espera o tempo necessário para
manter FPS constante e (2) retorna o tempo decorrido desde a última
chamada em milissegundos — o famoso "delta time" ou `dt`, que nós
convertemos para segundos e usamos em todos os updates para manter o
jogo independente da taxa de frames.
"""
import sys
import pygame

from src.states import MenuState, PlayingState, GameOverState
from src import audio

# Configurações da janela
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TITLE = "Veridis Quo"


class Game:
    """Contém o loop principal e gerencia a transição entre estados."""

    def __init__(self):
        pygame.init()
        audio.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # Registra os estados disponíveis
        self.states = {
            "menu": MenuState(self),
            "playing": PlayingState(self),
            "gameover": GameOverState(self),
        }
        self.current_state = self.states["menu"]
        # Inicia a música do menu (silencioso se não houver arquivo).
        audio.play_music("music_menu")

    def change_state(self, state_name: str):
        """Troca o estado atual do jogo, resetando o novo estado."""
        if state_name not in self.states:
            raise ValueError(f"Estado desconhecido: {state_name}")
        self.current_state = self.states[state_name]
        self.current_state.reset()
        # Troca de trilha conforme o estado.
        if state_name == "playing":
            audio.play_music("music_game")
        elif state_name in ("menu", "gameover"):
            audio.play_music("music_menu")

    def quit(self):
        """Encerra o loop principal na próxima iteração."""
        self.running = False

    def run(self):
        """Loop principal: eventos → update → draw, a 60 FPS."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # delta em segundos

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            self.current_state.handle_events(events)
            self.current_state.update(dt)
            self.current_state.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()
