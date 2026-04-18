"""Transformacoes geometricas 2D do Veridis Quo.

Este modulo reune as quatro transformacoes obrigatorias da disciplina
de Computacao Grafica como funcoes puras e reutilizaveis: translacao,
rotacao, escala e reflexao. Cada uma e aplicada em diferentes entidades
do jogo (nave, projeteis, asteroides, power-ups, particulas e fundo).

    Fundamentacao rapida (referencia para o relatorio)
    --------------------------------------------------

    Em computacao grafica 2D uma transformacao geometrica pode ser
    descrita por uma matriz 3x3 aplicada em coordenadas homogeneas
    [x, y, 1]^T. Cada funcao abaixo mostra, no docstring, a matriz
    correspondente.

    Os tipos de transformacao implementados sao *afins*: preservam
    linhas retas e paralelismo, mas nao necessariamente angulos ou
    distancias (a escala e a reflexao, por exemplo, nao preservam
    comprimentos).

    Porque funcoes e nao uma classe?
    --------------------------------
    Sao transformacoes *puras*: nao possuem estado. Receber entrada,
    retornar saida e nao guardar nada do lado facilita o teste, a
    composicao e a citacao no relatorio. Cada funcao corresponde
    diretamente a uma das 4 transformacoes exigidas.
"""
import pygame


# ---------------------------------------------------------------------------
# 1. TRANSLACAO
# ---------------------------------------------------------------------------
def translacao(posicao: tuple[float, float],
               deslocamento: tuple[float, float]) -> tuple[float, float]:
    """Translada um ponto 2D somando o vetor de deslocamento.

    Matriz de translacao em coordenadas homogeneas:

        | 1  0  dx |   | x |   | x + dx |
        | 0  1  dy | * | y | = | y + dy |
        | 0  0   1 |   | 1 |   |   1    |

    Como estamos em codigo de jogo (nao em calculo simbolico de matrizes),
    aplicamos a transformacao diretamente por soma de vetores. O resultado
    matematico e o mesmo, com custo computacional menor.

    Parametros
    ----------
    posicao : (x, y)
        Posicao atual do objeto no plano da tela.
    deslocamento : (dx, dy)
        Vetor de translacao a ser aplicado (normalmente velocidade * dt).

    Retorno
    -------
    (x + dx, y + dy) : nova posicao apos a translacao.

    Uso no jogo
    -----------
    Chamada a cada frame no update() de Player, Bullet, Asteroid,
    PowerUp, Particle e Starfield -- qualquer entidade que se mova.
    """
    x, y = posicao
    dx, dy = deslocamento
    return (x + dx, y + dy)


# ---------------------------------------------------------------------------
# 2. ROTACAO
# ---------------------------------------------------------------------------
def rotacao(superficie: pygame.Surface, angulo_graus: float) -> pygame.Surface:
    """Rotaciona uma Surface em torno do seu centro visual.

    Matriz de rotacao 2D (angulo theta, anti-horario):

        | cos(theta)  -sen(theta)  0 |
        | sen(theta)   cos(theta)  0 |
        |    0             0       1 |

    Aplicada a um ponto (x, y), leva a:

        x' = x * cos(theta) - y * sen(theta)
        y' = x * sen(theta) + y * cos(theta)

    O pygame.transform.rotate aplica essa mesma matriz a cada pixel
    da Surface, preservando o centro visual. Importante: o Surface
    retornado tem um bounding box *maior* que o original (pois a
    rotacao nao e um endomorfismo sobre o retangulo), por isso, no
    caller, recalculamos o rect com get_rect(center=...) para manter
    o pivot no lugar correto.

    Parametros
    ----------
    superficie : pygame.Surface
        Sprite original (nao e modificado -- e Python, lembra: imutavel
        em semantica externa, pois criamos uma nova Surface).
    angulo_graus : float
        Angulo em graus. Pygame usa convencao anti-horaria.

    Retorno
    -------
    Nova Surface contendo o sprite rotacionado.

    Uso no jogo
    -----------
    - Player.draw: orienta o sprite da nave conforme o angulo do leme.
    - Asteroid.draw: da giro continuo aos asteroides.
    """
    return pygame.transform.rotate(superficie, angulo_graus)


# ---------------------------------------------------------------------------
# 3. ESCALA
# ---------------------------------------------------------------------------
def escala(superficie: pygame.Surface, fator: float) -> pygame.Surface:
    """Aplica uma escala uniforme a uma Surface.

    Matriz de escala em 2D (fator sx = sy = s, uniforme):

        | s  0  0 |
        | 0  s  0 |
        | 0  0  1 |

    Se fator < 1.0 a imagem encolhe; se > 1.0 cresce; 1.0 e identidade.
    Usamos smoothscale (interpolacao bilinear) em vez de scale puro
    porque ela reduz os artefatos de aliasing ao redimensionar, o que
    importa num sprite pulsante (sem suavizacao o efeito fica "serrilhado").

    Atencao
    -------
    smoothscale nao aceita Surface com per-pixel alpha zero/largura 0.
    Por isso usamos max(1, int(fator * tam)) para garantir tamanho minimo
    de 1 pixel em cada eixo.

    Parametros
    ----------
    superficie : pygame.Surface
    fator : float
        Multiplicador de tamanho. Ex.: 1.15 = +15%, 0.5 = metade.

    Retorno
    -------
    Nova Surface redimensionada.

    Uso no jogo
    -----------
    - Asteroid.draw: pulso senoidal (escala varia no tempo).
    - PowerUp.draw: efeito de "respiracao".
    - Possui aplicacao adicional nas subclasses de sprite procedural.
    """
    largura, altura = superficie.get_size()
    nova_largura = max(1, int(largura * fator))
    nova_altura = max(1, int(altura * fator))
    return pygame.transform.smoothscale(superficie, (nova_largura, nova_altura))


# ---------------------------------------------------------------------------
# 4. REFLEXAO (flip / espelhamento)
# ---------------------------------------------------------------------------
def reflexao(superficie: pygame.Surface,
             horizontal: bool = True,
             vertical: bool = False) -> pygame.Surface:
    """Espelha uma Surface nos eixos solicitados.

    Matrizes de reflexao em 2D:

        Reflexao horizontal (em torno do eixo Y):
            | -1  0  0 |
            |  0  1  0 |
            |  0  0  1 |

        Reflexao vertical (em torno do eixo X):
            | 1   0  0 |
            | 0  -1  0 |
            | 0   0  1 |

    Uma reflexao pode ser vista como uma escala negativa em um dos
    eixos. E uma transformacao que *nao* preserva orientacao (inverte
    o "sentido" da figura), mas preserva distancias e angulos, entao
    pertence ao grupo das transformacoes isometricas.

    Parametros
    ----------
    superficie : pygame.Surface
    horizontal : bool
        Se True, espelha no eixo X (troca esquerda <-> direita).
    vertical : bool
        Se True, espelha no eixo Y (troca cima <-> baixo).

    Retorno
    -------
    Nova Surface refletida.

    Uso no jogo
    -----------
    - PowerUp.draw: alterna entre original e espelhamento horizontal
      a cada 0.35s, fazendo o "brilho" do item pular de lado (efeito
      visual que torna a reflexao inegavelmente perceptivel).
    """
    return pygame.transform.flip(superficie, horizontal, vertical)
