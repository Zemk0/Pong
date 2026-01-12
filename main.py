import pygame
import math
import random
import json
import os
from datetime import datetime

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1080
WINDOW_HEIGHT = 720
FPS = 60
MAX_BOUNCE_ANGLE = math.radians(60)  # Maximum reflection angle

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50)
NEON_BLUE = (0, 255, 255)
NEON_PINK = (255, 0, 255)
NEON_GREEN = (0, 255, 0)
NEON_PURPLE = (138, 43, 226)

class Vector2D:
    """Vector class for analytical geometry calculations"""
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        return Vector2D(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar):
        return Vector2D(self.x / scalar, self.y / scalar)

    def dot(self, other):
        """Dot product for vector calculations"""
        return self.x * other.x + self.y * other.y

    def magnitude(self):
        """Calculate vector magnitude"""
        return math.sqrt(self.x**2 + self.y**2)

    def normalize(self):
        """Return normalized vector (unit vector)"""
        mag = self.magnitude()
        if mag == 0:
            return Vector2D(0, 0)
        return Vector2D(self.x / mag, self.y / mag)

    def set_magnitude(self, new_mag):
        """Set vector to specific magnitude"""
        normalized = self.normalize()
        return normalized * new_mag

    def reflect(self, normal):
        """Reflect vector across a normal using V_new = V - 2(V·N)N"""
        normal_normalized = normal.normalize()
        dot_product = self.dot(normal_normalized)
        reflection = self - (normal_normalized * (2 * dot_product))
        return reflection

    def tuple(self):
        """Return as tuple for Pygame"""
        return (self.x, self.y)

class VisualStyle:
    """Visual theme system for easy style switching"""
    def __init__(self, name, bg_color, paddle_color, ball_color, text_color, line_color):
        self.name = name
        self.bg_color = bg_color
        self.paddle_color = paddle_color
        self.ball_color = ball_color
        self.text_color = text_color
        self.line_color = line_color

# Define visual styles
STYLES = {
    'classic': VisualStyle('Classic', BLACK, WHITE, WHITE, WHITE, WHITE),
    'Neon': VisualStyle('Neon', (10, 10, 30), NEON_PINK, NEON_BLUE, NEON_GREEN, NEON_PURPLE)
}

class Paddle:
    """Paddle with vector-based movement"""
    def __init__(self, x, y, width=15, height=100):
        self.position = Vector2D(x, y)
        self.width = width
        self.height = height
        self.velocity = Vector2D(0, 0)
        self.speed = 400  # Base speed in pixels per second

    def move(self, direction, dt, speed_multiplier=1.0):
        """Move paddle using vector velocity"""
        self.velocity = Vector2D(0, direction * self.speed * speed_multiplier)
        self.position = self.position + (self.velocity * dt)
        
        # Clamp to screen bounds
        if self.position.y < 0:
            self.position.y = 0
        elif self.position.y + self.height > WINDOW_HEIGHT:
            self.position.y = WINDOW_HEIGHT - self.height

    def get_rect(self):
        """Get pygame rect for rendering"""
        return pygame.Rect(self.position.x, self.position.y, self.width, self.height)

    def get_normal(self, ball_pos):
        """Calculate normal vector from paddle surface to ball"""
        # Determine which side of paddle was hit
        paddle_center = Vector2D(self.position.x + self.width/2, self.position.y + self.height/2)
        to_ball = ball_pos - paddle_center
        
        # Normal points away from paddle face
        if to_ball.x > 0:
            return Vector2D(1, 0)  # Right-facing normal
        else:
            return Vector2D(-1, 0)  # Left-facing normal

class Ball:
    """Ball with vector-based physics and analytical geometry collision"""
    def __init__(self, x, y, radius=8):
        self.position = Vector2D(x, y)
        self.velocity = Vector2D(0, 0)
        self.radius = radius
        self.base_speed = 400  # Base speed in pixels per second
        self.speed_multiplier = 1.0
        self.acceleration_enabled = True
        self.acceleration_factor = 1.05

    def reflect_from_paddle(self, paddle):
        """
        Change bounce angle based on hit position on paddle.
        """
        # Paddle center
        paddle_center_y = paddle.position.y + paddle.height / 2

        # Distance from paddle center
        offset = self.position.y - paddle_center_y

        # Normalize offset to range [-1, 1]
        normalized_offset = offset / (paddle.height / 2)
        normalized_offset = max(-1, min(1, normalized_offset))

        # Calculate bounce angle
        bounce_angle = normalized_offset * MAX_BOUNCE_ANGLE

        # Determine direction (left or right)
        direction = 1 if self.velocity.x < 0 else -1

        # Preserve speed
        speed = self.velocity.magnitude()
        if self.acceleration_enabled:
            speed *= self.acceleration_factor

        # Set new velocity based on angle
        self.velocity = Vector2D(
            math.cos(bounce_angle) * speed * direction,
            math.sin(bounce_angle) * speed
        )

    def reset(self, x, y):
        """Reset ball to center with random direction"""
        self.position = Vector2D(x, y)
        
        # Random angle between -45 and 45 degrees, random side
        angle = random.uniform(-math.pi/4, math.pi/4)
        direction = random.choice([-1, 1])
        
        # Create velocity vector with base speed
        self.velocity = Vector2D(
            math.cos(angle) * direction * self.base_speed,
            math.sin(angle) * self.base_speed
        )

    def update(self, dt, speed_multiplier=1.0):
        """Update ball position using vector velocity"""
        self.speed_multiplier = speed_multiplier
        self.position = self.position + (self.velocity * dt * speed_multiplier)

    def check_paddle_collision(self, paddle):
        """Check collision with paddle using analytical geometry"""
        # Find closest point on paddle rectangle to ball center
        closest_x = max(paddle.position.x, min(self.position.x, paddle.position.x + paddle.width))
        closest_y = max(paddle.position.y, min(self.position.y, paddle.position.y + paddle.height))
        closest_point = Vector2D(closest_x, closest_y)
        
        # Calculate distance vector from closest point to ball center
        distance_vec = self.position - closest_point
        distance = distance_vec.magnitude()
        
        # Collision detected if distance <= radius
        if distance <= self.radius:
            # Calculate normal vector (from paddle surface toward ball)
            self.reflect_from_paddle(paddle)
            
            # Move ball out of paddle to prevent multiple collisions
            overlap = self.radius - distance
            if overlap > 0:
                # Push ball away from paddle horizontally
                push_x = 1 if self.velocity.x > 0 else -1
                self.position.x += push_x * overlap

            return True
        return False

    def check_wall_collision(self):
        """Check collision with top/bottom walls using vector reflection"""
        if self.position.y - self.radius <= 0:
            # Top wall collision
            normal = Vector2D(0, 1)  # Downward normal
            self.velocity = self.velocity.reflect(normal)
            self.position.y = self.radius
            return True
        elif self.position.y + self.radius >= WINDOW_HEIGHT:
            # Bottom wall collision
            normal = Vector2D(0, -1)  # Upward normal
            self.velocity = self.velocity.reflect(normal)
            self.position.y = WINDOW_HEIGHT - self.radius
            return True
        return False

    def check_score(self):
        """Check if ball passed left or right boundary"""
        if self.position.x - self.radius <= 0:
            return 'right'  # Right player scored
        elif self.position.x + self.radius >= WINDOW_WIDTH:
            return 'left'  # Left player scored
        return None

class Button:
    """Interactive button with hover effects"""
    def __init__(self, x, y, width, height, text, font_size=32):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, font_size)
        self.hovered = False
        self.color = DARK_GRAY
        self.hover_color = GRAY
        self.text_color = WHITE

    def draw(self, screen):
        """Draw button with hover effect"""
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=8)
        
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def check_hover(self, mouse_pos):
        """Check if mouse is hovering over button"""
        self.hovered = self.rect.collidepoint(mouse_pos)
        return self.hovered

    def is_clicked(self, mouse_pos, mouse_clicked):
        """Check if button was clicked"""
        return self.hovered and mouse_clicked

class Slider:
    """Slider for adjusting values"""
    def __init__(self, x, y, width, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, width, 20)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.dragging = False
        self.font = pygame.font.Font(None, 24)
        
        # Calculate handle position
        self.handle_radius = 10
        self.update_handle_pos()

    def update_handle_pos(self):
        """Update handle position based on value"""
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        self.handle_x = self.rect.x + ratio * self.rect.width

    def draw(self, screen):
        """Draw slider"""
        # Draw track
        pygame.draw.rect(screen, GRAY, self.rect, border_radius=5)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=5)
        
        # Draw handle
        pygame.draw.circle(screen, WHITE, (int(self.handle_x), self.rect.centery), self.handle_radius)
        
        # Draw label and value
        label_text = f"{self.label}: {self.value:.2f}x"
        text_surface = self.font.render(label_text, True, WHITE)
        screen.blit(text_surface, (self.rect.x, self.rect.y - 25))

    def handle_event(self, event):
        """Handle mouse events for slider"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            handle_rect = pygame.Rect(self.handle_x - self.handle_radius, 
                                     self.rect.centery - self.handle_radius,
                                     self.handle_radius * 2, self.handle_radius * 2)
            if handle_rect.collidepoint(mouse_pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse_x = pygame.mouse.get_pos()[0]
            # Clamp to slider bounds
            mouse_x = max(self.rect.x, min(mouse_x, self.rect.x + self.rect.width))
            # Calculate new value
            ratio = (mouse_x - self.rect.x) / self.rect.width
            self.value = self.min_val + ratio * (self.max_val - self.min_val)
            self.update_handle_pos()

class Toggle:
    """Toggle switch for boolean options"""
    def __init__(self, x, y, label, initial_state=True):
        self.rect = pygame.Rect(x, y, 60, 30)
        self.label = label
        self.state = initial_state
        self.font = pygame.font.Font(None, 24)

    def draw(self, screen):
        """Draw toggle switch"""
        # Draw background
        color = NEON_GREEN if self.state else DARK_GRAY
        pygame.draw.rect(screen, color, self.rect, border_radius=15)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=15)
        
        # Draw toggle circle
        circle_x = self.rect.x + 45 if self.state else self.rect.x + 15
        pygame.draw.circle(screen, WHITE, (circle_x, self.rect.centery), 12)
        
        # Draw label
        label_surface = self.font.render(self.label, True, WHITE)
        screen.blit(label_surface, (self.rect.x, self.rect.y - 25))

    def handle_click(self, mouse_pos):
        """Toggle state on click"""
        if self.rect.collidepoint(mouse_pos):
            self.state = not self.state
            return True
        return False

class PlayerLog:
    """Manage persistent player logs"""
    def __init__(self, filename='player_logs.txt'):
        self.filename = filename
        self.logs = []
        self.load_logs()

    def load_logs(self):
        """Load logs from file"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    self.logs = [line.strip() for line in f.readlines()]
            except:
                self.logs = []

    def add_log(self, player1_name, player2_name, left_score, right_score):
        """Add new match log"""
        log_entry = f"{player1_name} vs {player2_name}: {left_score}-{right_score}"
        self.logs.append(log_entry)
        
        # Save to file
        try:
            with open(self.filename, 'a') as f:
                f.write(log_entry + '\n')
        except:
            pass

    def get_recent_logs(self, count=5):
        """Get most recent logs"""
        return self.logs[-count:] if len(self.logs) > 0 else []

class StartMenu:
    """Start menu with player input"""
    def __init__(self, screen):
        self.screen = screen
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        
        # Player name inputs
        self.player1_name = ""
        self.player2_name = ""
        self.input1_active = False
        self.input2_active = False
        self.input1_rect = pygame.Rect(WINDOW_WIDTH//2 - 150, 220, 300, 50)
        self.input2_rect = pygame.Rect(WINDOW_WIDTH//2 - 150, 310, 300, 50)
        
        # Buttons
        self.start_button = Button(WINDOW_WIDTH//2 - 100, 380, 200, 60, "Start Game")
        self.settings_button = Button(WINDOW_WIDTH//2 - 100, 460, 200, 60, "Settings")
        self.exit_button = Button(WINDOW_WIDTH//2 - 100, 540, 200, 60, "Exit")
        
        self.show_settings = False
        self.selected_style = 'classic'
        
        # Style selection buttons
        self.classic_button = Button(WINDOW_WIDTH//2 - 220, 300, 180, 50, "Classic", 28)
        self.Neon_button = Button(WINDOW_WIDTH//2 + 40, 300, 180, 50, "Neon", 28)
        self.back_button = Button(WINDOW_WIDTH//2 - 100, 450, 200, 60, "Back")

    def handle_event(self, event):
        """Handle menu events"""
        if self.show_settings:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if self.classic_button.is_clicked(mouse_pos, True):
                    self.selected_style = 'classic'
                elif self.Neon_button.is_clicked(mouse_pos, True):
                    self.selected_style = 'Neon'
                elif self.back_button.is_clicked(mouse_pos, True):
                    self.show_settings = False
        else:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self.input1_active = self.input1_rect.collidepoint(mouse_pos)
                self.input2_active = self.input2_rect.collidepoint(mouse_pos)
                
                if self.start_button.is_clicked(mouse_pos, True):
                    if len(self.player1_name) > 0 and len(self.player2_name) > 0:
                        return 'start'
                elif self.settings_button.is_clicked(mouse_pos, True):
                    self.show_settings = True
                elif self.exit_button.is_clicked(mouse_pos, True):
                    return 'exit'
                    
            elif event.type == pygame.KEYDOWN:
                if self.input1_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.player1_name = self.player1_name[:-1]
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_TAB:
                        self.input1_active = False
                        self.input2_active = True
                    elif len(self.player1_name) < 15 and event.unicode.isprintable():
                        self.player1_name += event.unicode
                        
                elif self.input2_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.player2_name = self.player2_name[:-1]
                    elif event.key == pygame.K_RETURN:
                        if len(self.player1_name) > 0 and len(self.player2_name) > 0:
                            return 'start'
                    elif len(self.player2_name) < 15 and event.unicode.isprintable():
                        self.player2_name += event.unicode
        
        return None

    def draw(self):
        """Draw menu"""
        self.screen.fill(BLACK)
        
        if self.show_settings:
            # Settings screen
            title = self.font_large.render("Settings", True, WHITE)
            self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 100))
            
            style_text = self.font_medium.render("Visual Style:", True, WHITE)
            self.screen.blit(style_text, (WINDOW_WIDTH//2 - style_text.get_width()//2, 220))
            
            # Draw style buttons
            mouse_pos = pygame.mouse.get_pos()
            self.classic_button.check_hover(mouse_pos)
            self.Neon_button.check_hover(mouse_pos)
            self.back_button.check_hover(mouse_pos)
            
            # Highlight selected style
            if self.selected_style == 'classic':
                self.classic_button.color = NEON_GREEN
            else:
                self.classic_button.color = DARK_GRAY
                
            if self.selected_style == 'Neon':
                self.Neon_button.color = NEON_GREEN
            else:
                self.Neon_button.color = DARK_GRAY
            
            self.classic_button.draw(self.screen)
            self.Neon_button.draw(self.screen)
            self.back_button.draw(self.screen)
        else:
            # Main menu
            title = self.font_large.render("VECTOR PONG", True, WHITE)
            self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 100))
            
            # Player 1 name input
            prompt1 = self.font_small.render("Player 1 (Left - W/S):", True, WHITE)
            self.screen.blit(prompt1, (WINDOW_WIDTH//2 - prompt1.get_width()//2, 180))
            
            color1 = WHITE if self.input1_active else GRAY
            pygame.draw.rect(self.screen, color1, self.input1_rect, 2, border_radius=5)
            name1_surface = self.font_medium.render(self.player1_name, True, WHITE)
            self.screen.blit(name1_surface, (self.input1_rect.x + 10, self.input1_rect.y + 8))
            
            # Player 2 name input
            prompt2 = self.font_small.render("Player 2 (Right - ↑/↓):", True, WHITE)
            self.screen.blit(prompt2, (WINDOW_WIDTH//2 - prompt2.get_width()//2, 275))
            
            color2 = WHITE if self.input2_active else GRAY
            pygame.draw.rect(self.screen, color2, self.input2_rect, 2, border_radius=5)
            name2_surface = self.font_medium.render(self.player2_name, True, WHITE)
            self.screen.blit(name2_surface, (self.input2_rect.x + 10, self.input2_rect.y + 8))
            
            # Buttons
            mouse_pos = pygame.mouse.get_pos()
            self.start_button.check_hover(mouse_pos)
            self.settings_button.check_hover(mouse_pos)
            self.exit_button.check_hover(mouse_pos)
            
            self.start_button.draw(self.screen)
            self.settings_button.draw(self.screen)
            self.exit_button.draw(self.screen)

class PostGameMenu:
    """Post-game menu showing match results"""
    def __init__(self, screen):
        self.screen = screen
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        self.font_tiny = pygame.font.Font(None, 24)
        
        # Buttons
        self.play_again_button = Button(WINDOW_WIDTH//2 - 220, 500, 200, 60, "Play Again")
        self.main_menu_button = Button(WINDOW_WIDTH//2 + 20, 500, 200, 60, "Main Menu")

    def draw(self, player1_name, player2_name, left_score, right_score, player_log, style):
        """Draw post-game menu"""
        self.screen.fill(style.bg_color)
        
        # Title
        title = self.font_large.render("Game Over!", True, style.text_color)
        self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 80))
        
        # Winner announcement
        if left_score > right_score:
            winner_text = f"{player1_name} Wins!"
        else:
            winner_text = f"{player2_name} Wins!"
        
        winner_surface = self.font_medium.render(winner_text, True, style.text_color)
        self.screen.blit(winner_surface, (WINDOW_WIDTH//2 - winner_surface.get_width()//2, 170))
        
        # Final score
        score_text = f"{player1_name}: {left_score} - {player2_name}: {right_score}"
        score_surface = self.font_small.render(score_text, True, style.text_color)
        self.screen.blit(score_surface, (WINDOW_WIDTH//2 - score_surface.get_width()//2, 240))
        
        # Recent matches
        logs = player_log.get_recent_logs(5)
        log_y = 320
        log_title = self.font_small.render("Recent Matches:", True, style.text_color)
        self.screen.blit(log_title, (WINDOW_WIDTH//2 - log_title.get_width()//2, log_y))
        log_y += 50
        
        for log in logs:
            log_text = self.font_tiny.render(log, True, style.text_color)
            self.screen.blit(log_text, (WINDOW_WIDTH//2 - log_text.get_width()//2, log_y))
            log_y += 30
        
        # Buttons
        mouse_pos = pygame.mouse.get_pos()
        self.play_again_button.check_hover(mouse_pos)
        self.main_menu_button.check_hover(mouse_pos)
        
        self.play_again_button.draw(self.screen)
        self.main_menu_button.draw(self.screen)

    def handle_click(self, mouse_pos):
        """Handle button clicks"""
        if self.play_again_button.is_clicked(mouse_pos, True):
            return 'play_again'
        elif self.main_menu_button.is_clicked(mouse_pos, True):
            return 'main_menu'
        return None

class Game:
    """Main game class"""
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Vector Pong")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = 'menu'  # menu, playing, paused, postgame
        
        # Game objects
        self.left_paddle = Paddle(50, WINDOW_HEIGHT//2 - 50)
        self.right_paddle = Paddle(WINDOW_WIDTH - 65, WINDOW_HEIGHT//2 - 50)
        self.ball = Ball(WINDOW_WIDTH//2, WINDOW_HEIGHT//2)
        
        # Scores
        self.left_score = 0
        self.right_score = 0
        self.winning_score = 5  # Game ends at 5 points
        
        # Player data
        self.player1_name = ""
        self.player2_name = ""
        self.player_log = PlayerLog()
        
        # Visual style
        self.current_style = STYLES['classic']
        
        # Menus
        self.start_menu = StartMenu(self.screen)
        self.postgame_menu = PostGameMenu(self.screen)
        
        # Pause menu
        self.pause_font = pygame.font.Font(None, 72)
        self.resume_button = Button(WINDOW_WIDTH//2 - 100, 180, 200, 60, "Resume")
        self.reset_button = Button(WINDOW_WIDTH//2 - 100, 260, 200, 60, "Reset")
        self.end_button = Button(WINDOW_WIDTH//2 - 100, 340, 200, 60, "End Game")
        
        # Settings sliders
        self.game_speed_slider = Slider(WINDOW_WIDTH//2 - 150, 440, 300, 0.5, 2.0, 1.0, "Game Speed")
        self.paddle_speed_slider = Slider(WINDOW_WIDTH//2 - 150, 510, 300, 0.5, 2.0, 1.0, "Paddle Speed")
        self.ball_speed_slider = Slider(WINDOW_WIDTH//2 - 150, 580, 300, 0.5, 2.0, 1.0, "Ball Speed")
        self.acceleration_toggle = Toggle(WINDOW_WIDTH//2 - 30, 660, "Ball Acceleration", True)
        
        # Fonts
        self.score_font = pygame.font.Font(None, 64)
        self.name_font = pygame.font.Font(None, 28)

    def reset_round(self):
        """Reset ball and paddles for new round"""
        self.left_paddle = Paddle(50, WINDOW_HEIGHT//2 - 50)
        self.right_paddle = Paddle(WINDOW_WIDTH - 65, WINDOW_HEIGHT//2 - 50)
        self.ball.reset(WINDOW_WIDTH//2, WINDOW_HEIGHT//2)

    def reset_game(self):
        """Reset entire game"""
        self.left_score = 0
        self.right_score = 0
        self.reset_round()

    def handle_input(self, dt):
        """Handle keyboard input for paddle movement"""
        keys = pygame.key.get_pressed()
        paddle_speed_mult = self.paddle_speed_slider.value
        
        # Left paddle (W/S)
        if keys[pygame.K_w]:
            self.left_paddle.move(-1, dt, paddle_speed_mult)
        elif keys[pygame.K_s]:
            self.left_paddle.move(1, dt, paddle_speed_mult)
        
        # Right paddle (UP/DOWN)
        if keys[pygame.K_UP]:
            self.right_paddle.move(-1, dt, paddle_speed_mult)
        elif keys[pygame.K_DOWN]:
            self.right_paddle.move(1, dt, paddle_speed_mult)

    def update(self, dt):
        """Update game state"""
        if self.state != 'playing':
            return
        
        # Apply game speed multiplier
        effective_dt = dt * self.game_speed_slider.value
        
        # Update ball
        self.ball.acceleration_enabled = self.acceleration_toggle.state
        self.ball.update(effective_dt, self.ball_speed_slider.value)
        
        # Check collisions
        self.ball.check_paddle_collision(self.left_paddle)
        self.ball.check_paddle_collision(self.right_paddle)
        self.ball.check_wall_collision()
        
        # Check scoring
        scorer = self.ball.check_score()
        if scorer == 'left':
            self.left_score += 1
            self.reset_round()
            if self.left_score >= self.winning_score:
                self.state = 'postgame'
                self.player_log.add_log(self.player1_name, self.player2_name, 
                                       self.left_score, self.right_score)
        elif scorer == 'right':
            self.right_score += 1
            self.reset_round()
            if self.right_score >= self.winning_score:
                self.state = 'postgame'
                self.player_log.add_log(self.player1_name, self.player2_name,
                                       self.left_score, self.right_score)

    def draw(self):
        """Draw game elements"""
        self.screen.fill(self.current_style.bg_color)
        
        if self.state == 'menu':
            self.start_menu.draw()
        elif self.state == 'postgame':
            self.postgame_menu.draw(self.player1_name, self.player2_name,
                                   self.left_score, self.right_score,
                                   self.player_log, self.current_style)
        else:
            # Draw center line
            for i in range(0, WINDOW_HEIGHT, 20):
                pygame.draw.rect(self.screen, self.current_style.line_color,
                               (WINDOW_WIDTH//2 - 2, i, 4, 10))
            
            # Draw paddles
            pygame.draw.rect(self.screen, self.current_style.paddle_color,
                           self.left_paddle.get_rect())
            pygame.draw.rect(self.screen, self.current_style.paddle_color,
                           self.right_paddle.get_rect())
            
            # Draw ball
            pygame.draw.circle(self.screen, self.current_style.ball_color,
                             (int(self.ball.position.x), int(self.ball.position.y)),
                             self.ball.radius)
            
            # Draw scores
            left_score_surf = self.score_font.render(str(self.left_score), True,
                                                     self.current_style.text_color)
            right_score_surf = self.score_font.render(str(self.right_score), True,
                                                      self.current_style.text_color)
            self.screen.blit(left_score_surf, (WINDOW_WIDTH//4 - 20, 30))
            self.screen.blit(right_score_surf, (3*WINDOW_WIDTH//4 - 20, 30))
            
            # Draw player names
            name1_surf = self.name_font.render(self.player1_name, True,
                                              self.current_style.text_color)
            name2_surf = self.name_font.render(self.player2_name, True,
                                              self.current_style.text_color)
            self.screen.blit(name1_surf, (50, 10))
            self.screen.blit(name2_surf, (WINDOW_WIDTH - 50 - name2_surf.get_width(), 10))
            
            # Draw pause overlay
            if self.state == 'paused':
                # Semi-transparent overlay
                overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
                overlay.set_alpha(200)
                overlay.fill(BLACK)
                self.screen.blit(overlay, (0, 0))
                
                # Pause title
                pause_text = self.pause_font.render("PAUSED", True, WHITE)
                self.screen.blit(pause_text, (WINDOW_WIDTH//2 - pause_text.get_width()//2, 80))
                
                # Buttons
                mouse_pos = pygame.mouse.get_pos()
                self.resume_button.check_hover(mouse_pos)
                self.reset_button.check_hover(mouse_pos)
                self.end_button.check_hover(mouse_pos)
                
                self.resume_button.draw(self.screen)
                self.reset_button.draw(self.screen)
                self.end_button.draw(self.screen)
                
                # Sliders and toggles
                self.game_speed_slider.draw(self.screen)
                self.paddle_speed_slider.draw(self.screen)
                self.ball_speed_slider.draw(self.screen)
                self.acceleration_toggle.draw(self.screen)

    def run(self):
        """Main game loop"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                # Menu state
                if self.state == 'menu':
                    result = self.start_menu.handle_event(event)
                    if result == 'start':
                        self.player1_name = self.start_menu.player1_name
                        self.player2_name = self.start_menu.player2_name
                        self.current_style = STYLES[self.start_menu.selected_style]
                        self.reset_game()
                        self.state = 'playing'
                    elif result == 'exit':
                        self.running = False
                
                # Playing state
                elif self.state == 'playing':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                            self.state = 'paused'
                
                # Paused state
                elif self.state == 'paused':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                            self.state = 'playing'
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()
                        if self.resume_button.is_clicked(mouse_pos, True):
                            self.state = 'playing'
                        elif self.reset_button.is_clicked(mouse_pos, True):
                            self.reset_game()
                            self.state = 'playing'
                        elif self.end_button.is_clicked(mouse_pos, True):
                            self.player_log.add_log(self.player1_name, self.player2_name,
                                                   self.left_score, self.right_score)
                            self.state = 'postgame'
                        else:
                            self.acceleration_toggle.handle_click(mouse_pos)
                    
                    # Handle slider events
                    self.game_speed_slider.handle_event(event)
                    self.paddle_speed_slider.handle_event(event)
                    self.ball_speed_slider.handle_event(event)
                
                # Post-game state
                elif self.state == 'postgame':
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()
                        result = self.postgame_menu.handle_click(mouse_pos)
                        if result == 'play_again':
                            self.reset_game()
                            self.state = 'playing'
                        elif result == 'main_menu':
                            self.state = 'menu'
            
            # Update
            if self.state == 'playing':
                self.handle_input(dt)
                self.update(dt)
            
            # Draw
            self.draw()
            pygame.display.flip()
        
        pygame.quit()

# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()
