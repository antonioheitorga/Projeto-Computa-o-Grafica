"""Smoke test do Veridis Quo.

Simula um fluxo completo do jogo (Menu -> Jogando -> Game Over)
sem abrir janela real, apenas para detectar crashes, vazamentos de
estado e regressões lógicas antes da apresentação.

Executar com: python -m tests.smoke_test
"""
import os
import sys

# Garante que pygame não tente usar display de verdade em ambiente sem tela.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402
pygame.init()
pygame.display.set_mode((800, 600))

# Imports do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.game import Game  # noqa: E402
from src.transforms import translacao, rotacao, escala, reflexao  # noqa: E402


def test_transforms_puras():
    """Confere propriedades matemáticas básicas das 4 transformações."""
    # Translacao: vetor zero é identidade.
    assert translacao((5, 7), (0, 0)) == (5, 7)
    # Translacao: composição por soma de vetores.
    p = translacao((1, 2), (3, 4))
    assert p == (4, 6)

    # Rotacao de 0 graus é identidade (mesmo tamanho).
    surf = pygame.Surface((20, 20), pygame.SRCALPHA)
    assert rotacao(surf, 0).get_size() == (20, 20)

    # Escala 1.0 preserva tamanho.
    assert escala(surf, 1.0).get_size() == (20, 20)
    # Escala 2.0 dobra.
    assert escala(surf, 2.0).get_size() == (40, 40)

    # Reflexao preserva tamanho (apenas espelha pixels).
    assert reflexao(surf, horizontal=True).get_size() == (20, 20)
    print("[OK] transformações puras")


def test_game_loop_simulado(frames=300):
    """Simula um gameplay de ~5 segundos (300 frames a 60fps)."""
    game = Game()
    game.change_state("playing")
    screen = game.screen

    # Força alguns inputs sintéticos para cobrir caminhos de código.
    # (não chamamos pygame.key.get_pressed em headless, o handle_input
    # só usa isso no update do player; aqui simulamos sem input.)
    for _ in range(frames):
        game.current_state.update(1 / 60)
        game.current_state.draw(screen)

    estado = game.states["playing"]
    print(
        f"[OK] 300 frames: onda={estado.onda} score={estado.score} "
        f"vidas={estado.lives} asteroides={len(estado.asteroides)}"
    )


def test_transicao_estados():
    """Menu -> Playing -> GameOver -> Playing novamente."""
    game = Game()
    assert game.current_state is game.states["menu"]
    game.change_state("playing")
    assert game.current_state is game.states["playing"]
    game.change_state("gameover")
    game.states["gameover"].final_score = 999
    game.states["gameover"].final_onda = 3
    assert game.current_state is game.states["gameover"]
    game.change_state("playing")
    assert game.states["playing"].score == 0  # resetou
    assert game.states["playing"].onda == 1
    print("[OK] transição de estados reseta corretamente")


def test_splitting_asteroides():
    from src.asteroid import Asteroid
    a = Asteroid(100, 100, "grande")
    filhos = a.dividir()
    assert len(filhos) == 2
    assert all(f.tier == "medio" for f in filhos)
    netos = filhos[0].dividir()
    assert len(netos) == 2
    assert all(n.tier == "pequeno" for n in netos)
    bisnetos = netos[0].dividir()
    assert bisnetos == []
    print("[OK] splitting grande -> médio -> pequeno -> (vazio)")


def test_powerup_flip_alterna():
    """Em ~1s o power-up deve ter alternado o flip várias vezes."""
    from src.powerup import PowerUp, TEMPO_FLIP
    p = PowerUp(400, 300)
    estados = []
    for _ in range(120):  # 2 segundos
        p.update(1 / 60, 800, 600)
        estados.append(p.flipado)
    # Em 2s e TEMPO_FLIP=0.35s, esperamos ~5 alternâncias.
    trocas = sum(1 for i in range(1, len(estados)) if estados[i] != estados[i - 1])
    assert trocas >= 4, f"esperado >=4 flips, obtive {trocas}"
    print(f"[OK] power-up alternou flip {trocas} vezes em 2s")


def main():
    test_transforms_puras()
    test_splitting_asteroides()
    test_powerup_flip_alterna()
    test_transicao_estados()
    test_game_loop_simulado()
    print("\nTodos os smoke tests passaram.")


if __name__ == "__main__":
    main()
