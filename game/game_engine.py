import pygame
import random
import io
import wave
import math
import struct

from .player import Player
from .enemy import EnemyGrid
from .bullet import Bullet


# Game Engine

WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
RED = (220, 60, 60)


class GameEngine:

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.player = Player(width // 2 - 20, height - 50, 40, 20)
        self.enemy_grid = EnemyGrid(width)

        self.player_bullets = []
        self.enemy_bullets = []

        self._shoot_cooldown = 0

        self.difficulty = "Medium"
        self.enemy_fire_chance = 0.01

        self.score = 0
        self.font = pygame.font.SysFont("Arial", 30)
        self.game_over = False

        # Initialize the mixer and create the sound effects once.
        self._initialize_sounds()

    def _initialize_sounds(self):
        self.fire_sound = None
        self.enemy_destroyed_sound = None
        self.game_over_sound = None

        try:
            # Only initialize the mixer if it has not already been initialized.
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(
                    frequency=44100,
                    size=-16,
                    channels=1,
                    buffer=512
                )

            self.fire_sound = self._create_sound(
                start_frequency=700,
                end_frequency=450,
                duration=0.07,
                volume=0.25
            )

            self.enemy_destroyed_sound = self._create_sound(
                start_frequency=250,
                end_frequency=120,
                duration=0.10,
                volume=0.30
            )

            self.game_over_sound = self._create_sound(
                start_frequency=500,
                end_frequency=80,
                duration=0.50,
                volume=0.35
            )

        except pygame.error:
            # If audio is unavailable, continue playing without sound.
            self.fire_sound = None
            self.enemy_destroyed_sound = None
            self.game_over_sound = None

    def _create_sound(
        self,
        start_frequency,
        end_frequency,
        duration,
        volume
    ):
        sample_rate = 44100
        sample_count = int(sample_rate * duration)

        audio_data = bytearray()

        for i in range(sample_count):
            progress = i / sample_count

            frequency = (
                start_frequency
                + (end_frequency - start_frequency) * progress
            )

            sample = math.sin(
                2 * math.pi * frequency * i / sample_rate
            )

            # Fade the sound in and out to avoid clicks.
            if progress < 0.05:
                sample *= progress / 0.05
            elif progress > 0.90:
                sample *= (1.0 - progress) / 0.10

            sample *= volume

            value = int(sample * 32767)

            audio_data.extend(
                struct.pack("<h", value)
            )

        wav_data = io.BytesIO()

        with wave.open(wav_data, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data)

        wav_data.seek(0)

        return pygame.mixer.Sound(file=wav_data)

    def _play_sound(self, sound):
        if sound is not None:
            try:
                sound.play()
            except pygame.error:
                pass

    def handle_event(self, event):
        # Handle input while the Game Over/replay screen is displayed.
        if self.game_over:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self._start_new_game("Easy")
                elif event.key == pygame.K_2:
                    self._start_new_game("Medium")
                elif event.key == pygame.K_3:
                    self._start_new_game("Hard")
                elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    return False

            return True

        # Normal gameplay: Space shoots.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if self._shoot_cooldown <= 0:
                bullet_x = self.player.center_x() - 2

                self.player_bullets.append(
                    Bullet(
                        bullet_x,
                        self.player.y,
                        direction=-1
                    )
                )

                # Task 4: Play the player firing sound.
                self._play_sound(self.fire_sound)

                self._shoot_cooldown = 15

        return True

    def handle_input(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.move(-self.player.speed, self.width)

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.move(self.player.speed, self.width)

    def update(self):
        if self.game_over:
            return

        if self._shoot_cooldown > 0:
            self._shoot_cooldown -= 1

        self.enemy_grid.move()

        for enemy in self.enemy_grid.alive_enemies():
            if random.random() < self.enemy_fire_chance:
                bullet_x = enemy.x + enemy.width // 2

                self.enemy_bullets.append(
                    Bullet(
                        bullet_x,
                        enemy.y + enemy.height,
                        direction=1
                    )
                )

        for bullet in self.player_bullets:
            bullet.move()

        for bullet in self.enemy_bullets:
            bullet.move()

        self.player_bullets = [
            b for b in self.player_bullets
            if not b.off_screen(self.height)
        ]

        self.enemy_bullets = [
            b for b in self.enemy_bullets
            if not b.off_screen(self.height)
        ]

        # Task 1: Improved collision handling.
        # Iterate over a copy so bullets can safely be removed
        # from the original list during collision processing.
        for bullet in self.player_bullets[:]:
            for enemy in self.enemy_grid.alive_enemies():
                if bullet.rect().colliderect(enemy.rect()):
                    enemy.alive = False
                    self.player_bullets.remove(bullet)
                    self.score += 1

                    # Task 4: Play the enemy-destroyed sound.
                    self._play_sound(self.enemy_destroyed_sound)

                    break

        # Check enemy bullets hitting the player.
        for bullet in self.enemy_bullets:
            if bullet.rect().colliderect(self.player.rect()):
                self._set_game_over()
                break

        # Check whether enemies have reached the player area.
        if self.enemy_grid.reached_bottom(self.player.y):
            self._set_game_over()

    def _set_game_over(self):
        # Only trigger the Game Over sound once.
        if not self.game_over:
            self.game_over = True

            # Task 4: Play the Game Over sound.
            self._play_sound(self.game_over_sound)

    def render(self, screen):
        # Task 2/3: Display Game Over/replay menu instead of normal game.
        if self.game_over:
            self._render_game_over(screen)
            return

        # Normal game rendering.
        pygame.draw.rect(
            screen,
            GREEN,
            self.player.rect()
        )

        for enemy in self.enemy_grid.alive_enemies():
            pygame.draw.rect(
                screen,
                WHITE,
                enemy.rect()
            )

        for bullet in self.player_bullets:
            pygame.draw.rect(
                screen,
                WHITE,
                bullet.rect()
            )

        for bullet in self.enemy_bullets:
            pygame.draw.rect(
                screen,
                RED,
                bullet.rect()
            )

        score_text = self.font.render(
            f"Score: {self.score}",
            True,
            WHITE
        )

        screen.blit(score_text, (10, 10))

    def _render_game_over(self, screen):
        screen.fill((0, 0, 0))

        title_font = pygame.font.Font(None, 72)
        score_font = pygame.font.Font(None, 44)
        option_font = pygame.font.Font(None, 38)
        instruction_font = pygame.font.Font(None, 28)

        title = title_font.render(
            "GAME OVER",
            True,
            WHITE
        )

        score = score_font.render(
            f"Final Score: {self.score}",
            True,
            WHITE
        )

        easy = option_font.render(
            "1 - Easy",
            True,
            WHITE
        )

        medium = option_font.render(
            "2 - Medium",
            True,
            WHITE
        )

        hard = option_font.render(
            "3 - Hard",
            True,
            WHITE
        )

        exit_text = option_font.render(
            "Enter/Escape - Exit",
            True,
            WHITE
        )

        instruction = instruction_font.render(
            "Choose a difficulty to play again",
            True,
            (180, 180, 180)
        )

        center_x = screen.get_width() // 2

        title_rect = title.get_rect(
            center=(center_x, 100)
        )

        score_rect = score.get_rect(
            center=(center_x, 175)
        )

        easy_rect = easy.get_rect(
            center=(center_x, 285)
        )

        medium_rect = medium.get_rect(
            center=(center_x, 340)
        )

        hard_rect = hard.get_rect(
            center=(center_x, 395)
        )

        exit_rect = exit_text.get_rect(
            center=(center_x, 450)
        )

        instruction_rect = instruction.get_rect(
            center=(center_x, 525)
        )

        screen.blit(title, title_rect)
        screen.blit(score, score_rect)
        screen.blit(easy, easy_rect)
        screen.blit(medium, medium_rect)
        screen.blit(hard, hard_rect)
        screen.blit(exit_text, exit_rect)
        screen.blit(instruction, instruction_rect)

    def _start_new_game(self, difficulty):
        # Reset player and enemy grid.
        self.player = Player(
            self.width // 2 - 20,
            self.height - 50,
            40,
            20
        )

        self.enemy_grid = EnemyGrid(self.width)

        # Clear all existing bullets.
        self.player_bullets = []
        self.enemy_bullets = []

        # Reset shooting cooldown.
        self._shoot_cooldown = 0

        # Reset score and game-over state.
        self.score = 0
        self.game_over = False

        # Store selected difficulty and apply enemy fire rate.
        self.difficulty = difficulty

        if difficulty == "Easy":
            self.enemy_fire_chance = 0.004
        elif difficulty == "Medium":
            self.enemy_fire_chance = 0.01
        elif difficulty == "Hard":
            self.enemy_fire_chance = 0.018