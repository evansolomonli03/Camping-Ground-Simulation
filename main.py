import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import random

# Import modules
from camera import Camera
from day_night_cycle import DayNightCycle
from weather import WeatherSystem
from tree import Tree
from terrain import Terrain


class CampingGroundGenerator:
    def __init__(self, width=800, height=600):
        pygame.init()
        self.width = width
        self.height = height
        self.display = pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Camping Ground Generator")

        # OpenGL initialization
        glClearColor(0.5, 0.7, 1.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_NORMALIZE)

        # Setup perspective projection
        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, (width / height), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

        # Initialize systems
        self.camera = Camera()
        self.day_night_cycle = DayNightCycle()
        self.weather_system = WeatherSystem()
        self.terrain = Terrain()

        # Initialize scene objects
        self.trees = self._generate_trees(20)

        # Mouse handling
        self.last_mouse_pos = (width // 2, height // 2)
        pygame.mouse.set_pos(self.last_mouse_pos)
        pygame.mouse.set_visible(False)

        self.running = True
        self.clock = pygame.time.Clock()

    def _generate_trees(self, count):
        trees = []
        for _ in range(count):
            position = (
                random.uniform(-20, 20),
                0,  # At ground level
                random.uniform(-20, 20)
            )
            scale = (
                random.uniform(0.8, 1.5),
                random.uniform(2.0, 4.0),  # Make trees taller
                random.uniform(0.8, 1.5)
            )
            rotation = (
                0,
                random.uniform(0, 360),
                0
            )

            # Simplified L-System parameters - just for variation
            tree_type = random.choice(["pine", "spruce", "oak"])
            if tree_type == "pine":
                lsystem_params = {"axiom": "F", "rules": {"F": "F"}, "iterations": 1}
            elif tree_type == "spruce":
                lsystem_params = {"axiom": "F", "rules": {"F": "F"}, "iterations": 1}
            else:  # oak
                lsystem_params = {"axiom": "F", "rules": {"F": "F"}, "iterations": 1}

            trees.append(Tree(position, scale, rotation, lsystem_params))
        return trees

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    # Toggle rain ON/OFF
                    if not hasattr(self.weather_system, 'rain_enabled'):
                        self.weather_system.rain_enabled = True
                    else:
                        self.weather_system.rain_enabled = not self.weather_system.rain_enabled

                    # Clear or initialize particles based on toggle state
                    if self.weather_system.rain_enabled:
                        # Start with a few particles, more will be added each update
                        self.weather_system.rain_particles = [
                            [random.uniform(-50, 50), random.uniform(20, 25), random.uniform(-50, 50),
                             random.uniform(9, 12)]
                            for _ in range(10)
                        ]
                    else:
                        # Clear all rain particles
                        self.weather_system.rain_particles = []
                elif event.key == pygame.K_f:
                    # Toggle fog
                    if self.weather_system.fog_density == 0:
                        self.weather_system.fog_density = 0.02
                    else:
                        self.weather_system.fog_density = 0
                # In handle_events method of main.py, add this to the KEYDOWN section:
                elif event.key == pygame.K_l:
                    # Toggle lightning
                    if not hasattr(self.weather_system, 'lightning_enabled'):
                        self.weather_system.lightning_enabled = False

                    self.weather_system.lightning_enabled = not self.weather_system.lightning_enabled

                    # If lightning is enabled but rain isn't, enable rain too
                    if self.weather_system.lightning_enabled and not hasattr(self.weather_system, 'rain_enabled'):
                        self.weather_system.rain_enabled = True
                        self.weather_system.rain_particles = [
                            [random.uniform(-50, 50), random.uniform(20, 25), random.uniform(-50, 50),
                             random.uniform(9, 12)]
                            for _ in range(10)
                        ]

            # Mouse movement handling for camera control
            elif event.type == pygame.MOUSEMOTION:
                mouse_pos = pygame.mouse.get_pos()
                x_offset = mouse_pos[0] - self.last_mouse_pos[0]
                y_offset = mouse_pos[1] - self.last_mouse_pos[1]

                # Apply smoothing by reducing extreme movements
                x_offset = max(min(x_offset, 15), -15)  # Limit maximum movement per frame
                y_offset = max(min(y_offset, 15), -15)

                # Process mouse movement for camera
                self.camera.process_mouse(x_offset, y_offset)

                # Reset mouse to center with a slight delay to reduce jitter
                if abs(x_offset) > 1 or abs(y_offset) > 1:  # Only reset if there was significant movement
                    pygame.mouse.set_pos((self.width // 2, self.height // 2))
                    self.last_mouse_pos = (self.width // 2, self.height // 2)
                else:
                    self.last_mouse_pos = mouse_pos  # Otherwise update the last position

    def update(self, delta_time):
        # Process keyboard for camera movement
        keys = pygame.key.get_pressed()
        self.camera.process_keyboard(keys, delta_time)

        # Update day-night cycle
        self.day_night_cycle.update(delta_time)

        # Update weather
        self.weather_system.update(delta_time)

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Apply camera
        self.camera.apply()

        # Apply day-night cycle lighting with weather awareness
        self.day_night_cycle.apply(self.weather_system)

        # Render the sun
        self.day_night_cycle.render_sun(self.weather_system)

        # Render weather effects
        self.weather_system.render()

        # Render scene
        self.terrain.render_ground()
        for tree in self.trees:
            tree.render()

    def run(self):
        while self.running:
            delta_time = self.clock.tick(60) / 1000.0

            self.handle_events()
            self.update(delta_time)
            self.render()

            pygame.display.flip()

        pygame.quit()


# Run the application
if __name__ == "__main__":
    app = CampingGroundGenerator()
    app.run()