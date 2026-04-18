# Veridis Quo

Jogo de nave no estilo **Asteroids clássico**, desenvolvido como projeto avaliativo da disciplina de **Computação Gráfica**. Aplica na prática as quatro transformações geométricas 2D: **translação, rotação, escala e reflexão**.

O nome é uma homenagem à faixa *Veridis Quo* do Daft Punk.

## Descrição do jogo

O jogador controla uma nave espacial com rotação livre (360°) e propulsão inercial. A missão é sobreviver o maior tempo possível em um campo de asteroides que giram, pulsam e se movem pela tela, destruindo-os com tiros para pontuar. O jogo termina quando as vidas acabam.

## Transformações geométricas aplicadas

| Transformação | Onde aparece |
|---------------|--------------|
| **Translação** | Movimento da nave, projéteis e asteroides |
| **Rotação**    | Giro da nave (360°), asteroides girando sobre si, projéteis seguindo ângulo da nave |
| **Escala**     | Asteroides pulsando/crescendo ao se aproximar, explosões, power-ups |
| **Reflexão**   | Flip em efeitos visuais e sprites em momentos específicos do gameplay |

Implementadas como funções reutilizáveis em [src/transforms.py](src/transforms.py).

## Pré-requisitos

- **Python 3.10 ou superior** (testado em 3.13)
- **pip** (gerenciador de pacotes do Python)
- **pygame 2.6.1** (instalado via `requirements.txt`)

## Instalação

```bash
git clone <url-do-repo>
cd Projeto-Computa-o-Grafica
pip install -r requirements.txt
```

Recomendado usar um ambiente virtual:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

## Execução

```bash
python main.py
```

## Controles

| Tecla | Ação |
|-------|------|
| `←` / `→` ou `A` / `D` | Rotacionar nave |
| `↑` ou `W` | Acelerar (propulsão) |
| `ESPAÇO` | Atirar |
| `ENTER` | Iniciar jogo (no menu) |
| `ESC` | Pausar / voltar ao menu / sair |

## Assets customizados (opcional)

Todos os sprites do jogo são gerados **proceduralmente** por padrão (nave, asteroides, power-up). Se quiser substituir por arte real (ex: [Kenney.nl](https://kenney.nl/assets) ou [OpenGameArt.org](https://opengameart.org/)), basta colocar PNGs com fundo transparente em `assets/images/` com os seguintes nomes:

| Arquivo | O que substitui |
|---------|-----------------|
| `ship.png` | Sprite da nave (apontando para cima) |
| `asteroid_grande.png` | Asteroide tamanho grande |
| `asteroid_medio.png` | Asteroide tamanho médio |
| `asteroid_pequeno.png` | Asteroide tamanho pequeno |
| `powerup.png` | Power-up (precisa ser **visivelmente assimétrico** para a reflexão ficar perceptível) |

O `src/assets.py` detecta automaticamente os PNGs e, se não existirem, cai no sprite procedural.

## Estrutura do projeto

```
.
├── main.py                 # Ponto de entrada
├── requirements.txt        # Dependências
├── README.md
├── assets/
│   ├── images/             # Sprites (nave, asteroides, projéteis)
│   └── sounds/             # Efeitos sonoros (opcional)
└── src/
    ├── __init__.py
    ├── game.py             # Classe Game (janela + game loop)
    ├── states.py           # Estados: Menu, Jogando, Game Over
    ├── player.py           # Nave do jogador + projéteis
    ├── asteroid.py         # Asteroides (3 tiers, splitting)
    ├── powerup.py          # Power-up colecionável (reflexão)
    ├── particles.py        # Partículas de explosão
    ├── starfield.py        # Fundo estelado com paralaxe
    ├── assets.py           # Asset loader com fallback procedural
    └── transforms.py       # Transformações geométricas 2D (as 4 obrigatórias)
```

## Equipe

Disciplina: **Computação Gráfica** — Prof.ª **Suzana Sousa**

| Integrante | Matrícula |
|------------|-----------|
| Heitor Yasuo Yamamoto | 230700022 |
| Gustavo Yuji Virgolino Nishimura | 23070007 |
| Antonio Heitor Gomes Azevedo | 23070017 |
| Deivison Ryan Brito Tavares | 23070037 |
