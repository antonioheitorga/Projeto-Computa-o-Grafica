"""HUD (Heads-Up Display) do Veridis Quo.

Renderiza os elementos de interface sobrepostos ao gameplay:
- Vidas (ícones de mini-naves)
- Pontuação (canto superior direito)
- Onda atual
- Indicador de escudo (quando invulnerável)
- Banner de "ONDA X" quando uma nova onda começa

Mantém a lógica de desenho isolada do PlayingState para legibilidade.
"""
import pygame


# Cores
WHITE = (255, 255, 255)
YELLOW = (255, 215, 0)
GRAY = (160, 160, 160)
GREEN = (120, 220, 120)
CYAN = (120, 220, 255)
PAINEL_BG = (10, 15, 30, 180)  # RGBA — painel semi-transparente


def _build_life_icon() -> pygame.Surface:
    """Mini-ícone de nave usado para representar cada vida."""
    size = 22
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    # Triângulo apontando para cima (menor, sem detalhes).
    pontos = [
        (cx, cy - 8),
        (cx - 6, cy + 6),
        (cx + 6, cy + 6),
    ]
    pygame.draw.polygon(surf, (60, 70, 100), pontos)
    pygame.draw.polygon(surf, (220, 230, 255), pontos, width=1)
    return surf


def _draw_panel(screen: pygame.Surface, rect: pygame.Rect, cor_borda=(70, 90, 130)):
    """Desenha um painel semi-transparente com borda fina."""
    painel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    painel.fill(PAINEL_BG)
    screen.blit(painel, rect.topleft)
    pygame.draw.rect(screen, cor_borda, rect, width=1, border_radius=4)


class HUD:
    def __init__(self):
        self.font_pequena = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_media = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_grande = pygame.font.SysFont("Arial", 30, bold=True)
        self.font_banner = pygame.font.SysFont("Arial", 42, bold=True)

        self._life_icon = _build_life_icon()

        # Banner de nova onda: duracao_restante e numero a mostrar.
        self._banner_timer = 0.0
        self._banner_onda = 1
        self._banner_duracao = 1.8  # segundos

    # ---------------------------------------------------------------- banners
    def mostrar_banner_onda(self, numero: int):
        self._banner_timer = self._banner_duracao
        self._banner_onda = numero

    def update(self, dt: float):
        if self._banner_timer > 0:
            self._banner_timer = max(0.0, self._banner_timer - dt)

    # ------------------------------------------------------------------- draw
    def draw(self, screen: pygame.Surface, vidas: int, score: int, onda: int,
             invuln_restante: float, invuln_total: float):
        largura = screen.get_width()

        # --- Painel de vidas (canto superior esquerdo) ---
        icon_w = self._life_icon.get_width()
        n_icones = max(vidas, 0)
        painel_w = 20 + n_icones * (icon_w + 4) if n_icones > 0 else 60
        painel_rect = pygame.Rect(10, 10, painel_w, 32)
        _draw_panel(screen, painel_rect)
        label = self.font_pequena.render("VIDAS", True, GRAY)
        screen.blit(label, (painel_rect.x + 6, painel_rect.y - 14))
        for i in range(n_icones):
            x = painel_rect.x + 8 + i * (icon_w + 4)
            y = painel_rect.y + (painel_rect.height - self._life_icon.get_height()) // 2
            screen.blit(self._life_icon, (x, y))

        # --- Painel de pontuação (canto superior direito) ---
        score_text = self.font_grande.render(f"{score:06d}", True, YELLOW)
        score_label = self.font_pequena.render("PONTUAÇÃO", True, GRAY)
        painel_score_w = max(score_text.get_width(), score_label.get_width()) + 24
        painel_score_rect = pygame.Rect(
            largura - painel_score_w - 10, 10, painel_score_w, 44
        )
        _draw_panel(screen, painel_score_rect)
        screen.blit(
            score_label,
            (painel_score_rect.x + 10, painel_score_rect.y + 4),
        )
        screen.blit(
            score_text,
            (painel_score_rect.x + 10, painel_score_rect.y + 14),
        )

        # --- Onda (centro superior) ---
        onda_text = self.font_media.render(f"ONDA {onda}", True, CYAN)
        onda_rect = onda_text.get_rect(center=(largura // 2, 26))
        painel_onda = onda_rect.inflate(24, 12)
        _draw_panel(screen, painel_onda)
        screen.blit(onda_text, onda_rect)

        # --- Indicador de escudo (invulnerabilidade) ---
        if invuln_restante > 0 and invuln_total > 0:
            barra_largura = 160
            barra_altura = 8
            barra_x = (largura - barra_largura) // 2
            barra_y = 60
            # Label
            label_escudo = self.font_pequena.render("ESCUDO", True, GREEN)
            screen.blit(
                label_escudo,
                label_escudo.get_rect(center=(largura // 2, barra_y - 8)),
            )
            # Fundo da barra
            pygame.draw.rect(
                screen, (30, 40, 50),
                (barra_x, barra_y, barra_largura, barra_altura),
                border_radius=3,
            )
            # Preenchimento proporcional ao tempo restante
            fator = max(0.0, min(1.0, invuln_restante / invuln_total))
            pygame.draw.rect(
                screen, GREEN,
                (barra_x, barra_y, int(barra_largura * fator), barra_altura),
                border_radius=3,
            )

        # --- Banner de nova onda (centro da tela) ---
        if self._banner_timer > 0:
            fator = self._banner_timer / self._banner_duracao
            # Alpha pulsa: começa forte e some ao final.
            alpha = int(255 * fator)
            banner = self.font_banner.render(
                f"ONDA {self._banner_onda}", True, YELLOW
            )
            banner = banner.convert_alpha()
            banner.set_alpha(alpha)
            rect = banner.get_rect(center=(largura // 2, screen.get_height() // 2))
            screen.blit(banner, rect)

        # --- Dica de ESC no rodapé ---
        dica = self.font_pequena.render("ESC: voltar ao menu", True, (80, 90, 110))
        screen.blit(dica, (10, screen.get_height() - 22))
