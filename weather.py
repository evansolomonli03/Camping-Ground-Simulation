import random
from OpenGL.GL import *

class WeatherSystem:
    def __init__(self):
        self.rain_particles     = []
        self.fog_density        = 0.0
        self.lightning_active   = False
        self.lightning_intensity= 0.0
        self.lightning_duration = 0.0
        self.lightning_cooldown = 0.0
        self.rain_enabled       = False
        self.lightning_enabled  = False

    def update(self, dt):
        # Rain
        if self.rain_enabled:
            if len(self.rain_particles) < 1000:
                for _ in range(10):
                    x, y, z = random.uniform(-20,20), random.uniform(10,20), random.uniform(-20,20)
                    speed = random.uniform(9,12)
                    self.rain_particles.append([x,y,z,speed])
            new = []
            for p in self.rain_particles:
                p[1] -= p[3] * dt
                if p[1] > 0:
                    new.append(p)
            self.rain_particles = new

        # Lightning
        if self.rain_enabled and self.lightning_enabled:
            if self.lightning_active:
                self.lightning_duration -= dt
                if self.lightning_duration <= 0:
                    self.lightning_active    = False
                    self.lightning_intensity = 0.0
                    self.lightning_cooldown  = random.uniform(5,15)
            else:
                self.lightning_cooldown -= dt
                if self.lightning_cooldown <= 0 and random.random() < 0.1:
                    self.lightning_active    = True
                    self.lightning_intensity = random.uniform(0.5,1.0)
                    self.lightning_duration  = random.uniform(0.05,0.2)
        else:
            self.lightning_active    = False
            self.lightning_intensity = 0.0

    def render(self):
        # Fog
        if self.fog_density > 0:
            glFogi(GL_FOG_MODE, GL_EXP2)
            glFogfv(GL_FOG_COLOR, (0.5,0.5,0.5,1.0))
            glFogf(GL_FOG_DENSITY, self.fog_density)
            glEnable(GL_FOG)
        else:
            glDisable(GL_FOG)

        # Rain
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glColor3f(0.7,0.8,1.0)
        for p in self.rain_particles:
            glVertex3f(p[0], p[1], p[2])
            glVertex3f(p[0], p[1]-1.0, p[2])
        glEnd()
        glLineWidth(1.0)

        # Lightning flicker
        if self.lightning_active:
            amb = (self.lightning_intensity,) * 3 + (1.0,)
            glLightModelfv(GL_LIGHT_MODEL_AMBIENT, amb)
        else:
            glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.2,0.2,0.2,1.0))
