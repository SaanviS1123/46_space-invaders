import pygame

from game.game_engine import GameEngine


# Initialize pygame / Start application
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 600, 700

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption("Space Invaders - Pygame Version")

# Colors
BLACK = (0, 0, 0)

# Clock
clock = pygame.time.Clock()
FPS = 60

# Game loop
engine = GameEngine(WIDTH, HEIGHT)


def main():
    running = True

    while running:
        SCREEN.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif not engine.handle_event(event):
                running = False

        # Only run normal gameplay while the game is active.
        if running and not engine.game_over:
            engine.handle_input()
            engine.update()

        # Render either the normal game or the Game Over screen.
        engine.render(SCREEN)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()