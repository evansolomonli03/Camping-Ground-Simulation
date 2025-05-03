# camping_sim.py

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import random
import math
from pyglm import glm

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
GROUND_EXTENT = 50.0
GROUND_Y      = 0.0

TENT_BASE   = 1.0
TENT_HEIGHT = 1.5

PIT_CENTER   = (-1.2, -1.7)
PIT_RADIUS   = 0.5
N_STONES     = 13
STONE_RADIUS = 0.12

FLAME_HEIGHT = 0.6
FLAME_BASE   = 0.1
FLAME_POS    = [
    (PIT_CENTER[0] + 0.2, PIT_CENTER[1]),
    (PIT_CENTER[0] - 0.2, PIT_CENTER[1]),
    (PIT_CENTER[0],       PIT_CENTER[1] + 0.2),
]

SMOKE_RISE_SPEED  = 1.0
SMOKE_LIFETIME    = 3.0
SMOKE_BASE_HEIGHT = GROUND_Y + 0.05
SMOKE_BASE_SPREAD = 0.1

NUM_TREES        = 1000
TREE_TENT_BUFFER = 1.0
TREE_PIT_BUFFER  = 0.5
SPAWN_RADIUS     = 60.0

ROT_SENS    = 0.3
ZOOM_AMOUNT = 1.0

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

        if self.rain_enabled and self.lightning_enabled:
            if self.lightning_active:
                self.lightning_duration -= dt
                if self.lightning_duration <= 0:
                    self.lightning_active   = False
                    self.lightning_intensity= 0.0
                    self.lightning_cooldown = random.uniform(5,15)
            else:
                self.lightning_cooldown -= dt
                if self.lightning_cooldown <= 0 and random.random() < 0.1:
                    self.lightning_active   = True
                    self.lightning_intensity= random.uniform(0.5,1.0)
                    self.lightning_duration = random.uniform(0.05,0.2)
        else:
            self.lightning_active    = False
            self.lightning_intensity = 0.0

    def render(self):
        if self.fog_density > 0:
            glFogi(GL_FOG_MODE, GL_EXP2)
            glFogfv(GL_FOG_COLOR, (0.5,0.5,0.5,1.0))
            glFogf(GL_FOG_DENSITY, self.fog_density)
            glEnable(GL_FOG)
        else:
            glDisable(GL_FOG)

        glLineWidth(2.0)
        glBegin(GL_LINES)
        glColor3f(0.7,0.8,1.0)
        for p in self.rain_particles:
            glVertex3f(p[0], p[1], p[2])
            glVertex3f(p[0], p[1] - 1.0, p[2])
        glEnd()
        glLineWidth(1.0)

        if self.lightning_active:
            amb = (self.lightning_intensity,) * 3 + (1.0,)
            glLightModelfv(GL_LIGHT_MODEL_AMBIENT, amb)
        else:
            glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.2,0.2,0.2,1.0))

class LSystem:
    def __init__(self, axiom, rules, iterations):
        self.axiom      = axiom
        self.rules      = rules
        self.iterations = iterations

    def generate(self):
        res = self.axiom
        for _ in range(self.iterations):
            res = "".join(self.rules.get(c, c) for c in res)
        return res

class Tree:
    def __init__(self, position, scale, rotation, params):
        self.position = position
        self.scale    = scale
        self.rotation = rotation
        ax = params.get("axiom", "F")
        rules = params.get("rules", {"F":"FF+[+F-F-F]-[-F+F+F]"})
        it = params.get("iterations", 3)
        self.lsys = LSystem(ax, rules, it)
        self.dl   = self._compile()

    def _compile(self):
        dl = glGenLists(1)
        glNewList(dl, GL_COMPILE)
        glPushMatrix()
        glTranslatef(*self.position)
        glRotatef(self.rotation[1], 0, 1, 0)
        glRotatef(-90, 1, 0, 0)
        # Trunk
        glColor3f(0.6,0.3,0.1)
        q = gluNewQuadric()
        gluCylinder(q, 0.1*self.scale[0], 0.08*self.scale[0], 1.0*self.scale[1], 8, 4)
        gluDeleteQuadric(q)
        # Foliage
        glTranslatef(0, 0, 0.7*self.scale[1])
        glColor3f(0.1,0.6,0.1)
        q2 = gluNewQuadric()
        gluCylinder(q2, 0.5*self.scale[0], 0.0, 1.5*self.scale[1], 10, 4)
        gluDeleteQuadric(q2)
        glPopMatrix()
        glEndList()
        return dl

    def render(self):
        glCallList(self.dl)

class Terrain:
    def __init__(self, size=GROUND_EXTENT):
        self.size = size

    def render_ground(self):
        glColor3f(0.3,0.5,0.2)
        glBegin(GL_QUADS)
        glNormal3f(0,1,0)
        s = self.size
        glVertex3f(-s, GROUND_Y, -s)
        glVertex3f(-s, GROUND_Y,  s)
        glVertex3f( s, GROUND_Y,  s)
        glVertex3f( s, GROUND_Y, -s)
        glEnd()

class DayNightCycle:
    def __init__(self):
        self.time     = 0.25
        self.sun_size = 5.0
        self.sun_dl   = self._make_sun()
        self.sun_pos  = [0.0, 0.0, 0.0]

    def _make_sun(self):
        dl = glGenLists(1)
        glNewList(dl, GL_COMPILE)
        q = gluNewQuadric()
        gluSphere(q, self.sun_size, 20, 20)
        gluDeleteQuadric(q)
        glEndList()
        return dl

    def update(self, mode):
        self.time = 0.25 if mode == "day" else 0.75
        ang = self.time * 2 * math.pi
        d   = 80.0
        sy  = math.sin(ang)
        cy  = math.cos(ang)
        self.sun_pos = [0.0, max(0.0, sy)*d, -cy*d]

    def get_light_dir(self):
        ang = self.time * 2 * math.pi
        y   = math.sin(ang)
        return (0.0, max(0.1, y), -math.cos(ang), 0.0)

    def apply(self):
        diff_col = (1.0,1.0,1.0,1.0) if self.time < 0.5 else (0.05,0.05,0.1,1.0)
        f = max(0.0, math.sin(self.time * 2 * math.pi))
        diff = tuple(c * f for c in diff_col)
        glLightfv(GL_LIGHT0, GL_POSITION, self.get_light_dir())
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  diff)
        glLightfv(GL_LIGHT0, GL_SPECULAR, diff)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, diff)

    def render_sun(self):
        if self.sun_pos[1] <= 0:
            return
        glDisable(GL_LIGHTING)
        glColor3f(1.0,1.0,0.8)
        glPushMatrix()
        glTranslatef(*self.sun_pos)
        glCallList(self.sun_dl)
        glPopMatrix()
        glEnable(GL_LIGHTING)

class Camera:
    def __init__(self):
        self.position    = glm.vec3(0.0, 2.0, 10.0)
        self.front       = glm.vec3(0.0, 0.0, -1.0)
        self.up          = glm.vec3(0.0, 1.0,  0.0)
        self.yaw         = -90.0
        self.pitch       =   0.0
        self.move_speed  = 5.0
        self.sensitivity = 0.05
        self._update_vectors()

    def _update_vectors(self):
        fx = math.cos(math.radians(self.yaw)) * math.cos(math.radians(self.pitch))
        fy = math.sin(math.radians(self.pitch))
        fz = math.sin(math.radians(self.yaw)) * math.cos(math.radians(self.pitch))
        self.front = glm.normalize(glm.vec3(fx, fy, fz))
        right      = glm.cross(self.front, glm.vec3(0,1,0))
        self.up    = glm.normalize(glm.cross(right, self.front))

    def process_keyboard(self, keys, dt):
        v = self.move_speed * dt
        if keys[K_w]:
            self.position += self.front * v
        if keys[K_s]:
            self.position -= self.front * v
        if keys[K_a]:
            self.position -= glm.cross(self.front, self.up) * v
        if keys[K_d]:
            self.position += glm.cross(self.front, self.up) * v
        if keys[K_SPACE]:
            self.position.y += v
        if keys[K_LSHIFT]:
            self.position.y -= v

    def process_mouse(self, dx, dy):
        if abs(dx) > 100 or abs(dy) > 100:
            return
        self.yaw   += dx * self.sensitivity
        self.pitch -= dy * self.sensitivity
        self.pitch  = max(-89.0, min(89.0, self.pitch))
        self._update_vectors()

    def zoom(self, amt):
        self.position += self.front * amt

    def apply(self):
        view = glm.lookAt(self.position, self.position + self.front, self.up)
        data = [view[i][j] for i in range(4) for j in range(4)]
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glMultMatrixf(data)

def draw_tent():
    glColor3f(0.0,0.0,0.0)
    hs   = TENT_BASE
    apex = (0.0, TENT_HEIGHT, 0.0)
    base = [(-hs,0,-hs),(hs,0,-hs),(hs,0,hs),(-hs,0,hs)]
    glBegin(GL_TRIANGLES)
    for p1, p2 in zip(base, base[1:]+base[:1]):
        glVertex3f(*apex)
        glVertex3f(*p1)
        glVertex3f(*p2)
    glEnd()
    glColor3f(1.0,1.0,1.0)
    glLineWidth(4)
    glBegin(GL_LINES)
    glVertex3f(0.0, TENT_HEIGHT, 0.0)
    glVertex3f(0.0, 0.0, -hs)
    glEnd()
    glLineWidth(1)

def draw_stones():
    quad = gluNewQuadric()
    glColor3f(0.6,0.6,0.6)
    for angle in np.linspace(0, 2*math.pi, N_STONES, endpoint=False):
        x = PIT_CENTER[0] + PIT_RADIUS * math.cos(angle)
        z = PIT_CENTER[1] + PIT_RADIUS * math.sin(angle)
        glPushMatrix()
        glTranslatef(x, GROUND_Y + STONE_RADIUS, z)
        gluSphere(quad, STONE_RADIUS, 16, 16)
        glPopMatrix()
    gluDeleteQuadric(quad)

def draw_flames():
    quad = gluNewQuadric()
    glColor3f(1.0,0.5,0.0)
    for x, z in FLAME_POS:
        glPushMatrix()
        glTranslatef(x, GROUND_Y, z)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quad, FLAME_BASE, 0.0, FLAME_HEIGHT, 16, 1)
        glPopMatrix()
    gluDeleteQuadric(quad)

# Smoke globals
smoke_particles = []
quad_smoke      = None
smoke_timer     = 0.0

def spawn_smoke():
    for _ in range(4):
        smoke_particles.append({
            'x': PIT_CENTER[0] + random.uniform(-SMOKE_BASE_SPREAD, SMOKE_BASE_SPREAD),
            'y': SMOKE_BASE_HEIGHT,
            'z': PIT_CENTER[1] + random.uniform(-SMOKE_BASE_SPREAD, SMOKE_BASE_SPREAD),
            'age': 0.0
        })

def update_smoke(dt):
    global smoke_particles
    smoke_particles = [
        {'x': p['x'], 'y': p['y'] + dt * SMOKE_RISE_SPEED,'z': p['z'],'age': p['age'] + dt}
        for p in smoke_particles if p['age'] + dt < SMOKE_LIFETIME
    ]

def draw_smoke():
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    for p in smoke_particles:
        alpha = max(0.0, 1.0 - p['age']/SMOKE_LIFETIME)
        size  = 0.2 + 0.15 * p['age']
        glColor4f(0.8,0.8,0.8,alpha)
        glPushMatrix()
        glTranslatef(p['x'], p['y'], p['z'])
        gluSphere(quad_smoke, size, 8, 8)
        glPopMatrix()
    glDisable(GL_BLEND)

def main():
    global quad_smoke, smoke_timer

    pygame.init()
    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), DOUBLEBUF | OPENGL)
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()

    glClearColor(0.5,0.7,1.0,1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING); glEnable(GL_LIGHT0); glEnable(GL_LIGHT1)
    glEnable(GL_COLOR_MATERIAL); glEnable(GL_NORMALIZE)
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glMatrixMode(GL_PROJECTION); gluPerspective(45, SCREEN_WIDTH/SCREEN_HEIGHT, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)

    cam     = Camera()
    day     = DayNightCycle()
    weather = WeatherSystem()
    terra   = Terrain(GROUND_EXTENT)

    trees = []
    while len(trees) < NUM_TREES:
        x = random.uniform(-SPAWN_RADIUS, SPAWN_RADIUS)
        z = random.uniform(-SPAWN_RADIUS, SPAWN_RADIUS)
        if abs(x) < TENT_BASE + TREE_TENT_BUFFER and abs(z) < TENT_BASE + TREE_TENT_BUFFER:
            continue
        if (x - PIT_CENTER[0])**2 + (z - PIT_CENTER[1])**2 < (PIT_RADIUS + TREE_PIT_BUFFER)**2:
            continue
        trees.append(Tree((x,0,z), (1, random.uniform(2,4)), (0, random.uniform(0,360)), {}))

    quad_smoke  = gluNewQuadric()
    smoke_timer = 0.0
    is_day      = True

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        smoke_timer += dt

        for ev in pygame.event.get():
            if ev.type == QUIT:
                running = False
            elif ev.type == KEYDOWN:
                if ev.key == K_ESCAPE:
                    running = False
                elif ev.key == K_b:
                    is_day = True
                elif ev.key == K_n:
                    is_day = False
                elif ev.key == K_r:
                    weather.rain_enabled = not weather.rain_enabled
                    weather.rain_particles = [] if not weather.rain_enabled else [
                        [random.uniform(-20,20), random.uniform(10,20), random.uniform(-20,20), random.uniform(9,12)]
                        for _ in range(10)
                    ]
                elif ev.key == K_f:
                    weather.fog_density = 0.02 if weather.fog_density == 0 else 0.0
                elif ev.key == K_l:
                    weather.lightning_enabled = not weather.lightning_enabled
                    if weather.lightning_enabled and not weather.rain_enabled:
                        weather.rain_enabled = True
                        weather.rain_particles = [
                            [random.uniform(-20,20), random.uniform(10,20), random.uniform(-20,20), random.uniform(9,12)]
                            for _ in range(10)
                        ]
            elif ev.type == MOUSEBUTTONDOWN:
                if ev.button == 4:
                    cam.zoom(ZOOM_AMOUNT)
                elif ev.button == 5:
                    cam.zoom(-ZOOM_AMOUNT)
            elif ev.type == MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                dx, dy = ev.rel
                cam.process_mouse(dx, dy)

        keys = pygame.key.get_pressed()
        cam.process_keyboard(keys, dt)
        weather.update(dt)
        day.update("day" if is_day else "night")

        if not is_day:
            glEnable(GL_LIGHT1)
            fire_x, fire_z = PIT_CENTER
            fire_y = GROUND_Y + 0.2

            glLightfv(GL_LIGHT1, GL_POSITION, (fire_x, fire_y, fire_z, 1.0))

            glLightfv(GL_LIGHT1, GL_AMBIENT,  (0.4, 0.2, 0.1, 1.0))
            glLightfv(GL_LIGHT1, GL_DIFFUSE,  (1.0, 0.8, 0.4, 1.0))
            glLightfv(GL_LIGHT1, GL_SPECULAR, (1.0, 0.8, 0.4, 1.0))
            glLightf(GL_LIGHT1, GL_CONSTANT_ATTENUATION,  0.1)
            glLightf(GL_LIGHT1, GL_LINEAR_ATTENUATION,    0.01)
            glLightf(GL_LIGHT1, GL_QUADRATIC_ATTENUATION, 0.002)
        else:
            glDisable(GL_LIGHT1)


        if smoke_timer > 0.1:
            spawn_smoke()
            smoke_timer = 0.0
        update_smoke(dt)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        cam.apply()
        day.apply()
        day.render_sun()
        terra.render_ground()
        for t in trees:
            t.render()
        draw_tent()
        draw_stones()
        draw_flames()
        weather.render()
        draw_smoke()
        pygame.display.flip()

    gluDeleteQuadric(quad_smoke)
    pygame.quit()

if __name__ == "__main__":
    main()
