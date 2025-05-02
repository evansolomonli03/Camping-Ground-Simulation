import random
from OpenGL.GL import *


class WeatherSystem:
    def __init__(self):
        self.rain_particles = []
        self.fog_density = 0.0
        self.lightning_active = False
        self.lightning_intensity = 0.0
        self.lightning_duration = 0
        self.lightning_cooldown = 0
        self.rain_enabled = False
        self.lightning_enabled = False  # Add this line

    def update(self, delta_time):
        # Update rain particles
        self.update_rain(delta_time)

        # Only update lightning if rain is enabled and lightning is enabled
        if self.rain_enabled and self.lightning_enabled:
            self.update_lightning(delta_time)
        else:
            # Make sure lightning is off when disabled
            self.lightning_active = False
            self.lightning_intensity = 0.0

    def update_rain(self, delta_time):
        # Only process rain if it's enabled
        if hasattr(self, 'rain_enabled') and self.rain_enabled:
            # Add new rain particles
            if len(self.rain_particles) < 1000:
                for _ in range(10):
                    x = random.uniform(-50, 50)
                    y = random.uniform(20, 25)
                    z = random.uniform(-50, 50)
                    speed = random.uniform(9, 12)
                    self.rain_particles.append([x, y, z, speed])

            # Update existing particles
            new_particles = []
            for particle in self.rain_particles:
                particle[1] -= particle[3] * delta_time
                if particle[1] > 0:
                    new_particles.append(particle)
            self.rain_particles = new_particles

    def update_lightning(self, delta_time):
        if self.lightning_active:
            self.lightning_duration -= delta_time
            if self.lightning_duration <= 0:
                self.lightning_active = False
                self.lightning_intensity = 0.0
                self.lightning_cooldown = random.uniform(5, 15)
        else:
            self.lightning_cooldown -= delta_time
            if self.lightning_cooldown <= 0 and random.random() < 0.1:
                self.lightning_active = True
                self.lightning_intensity = random.uniform(0.5, 1.0)
                self.lightning_duration = random.uniform(0.05, 0.2)

    def render(self):
        # Render fog
        if self.fog_density > 0:
            glFogi(GL_FOG_MODE, GL_EXP2)
            glFogfv(GL_FOG_COLOR, (0.5, 0.5, 0.5, 1.0))
            glFogf(GL_FOG_DENSITY, self.fog_density)
            glEnable(GL_FOG)
        else:
            glDisable(GL_FOG)

        # Render rain - thicker and more visible
        glLineWidth(2.0)  # Thicker lines for rain
        glBegin(GL_LINES)
        glColor3f(0.7, 0.8, 1.0)  # Lighter blue for rain
        for particle in self.rain_particles:
            glVertex3f(particle[0], particle[1], particle[2])
            glVertex3f(particle[0], particle[1] - 1.0, particle[2])  # Longer rain drops
        glEnd()
        glLineWidth(1.0)  # Reset line width

        # Apply lightning effect
        if self.lightning_active:
            glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (
                self.lightning_intensity,
                self.lightning_intensity,
                self.lightning_intensity,
                1.0
            ))
        else:
            # Reset to normal ambient lighting
            glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.2, 0.2, 0.2, 1.0))