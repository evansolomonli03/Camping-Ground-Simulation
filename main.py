# main.py

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import random
import math

from camera import Camera
from day_night_cycle import DayNightCycle
from weather import WeatherSystem
from tree import Tree
from terrain import Terrain

# Configuration
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

NUM_TREES        = 80
TREE_TENT_BUFFER = 1.0
TREE_PIT_BUFFER  = 0.5
SPAWN_RADIUS     = 60.0

ROT_SENS    = 0.3
ZOOM_AMOUNT = 1.0

# Smoke globals
smoke_particles = []
quad_smoke      = None
smoke_timer     = 0.0

def draw_tent():
    glColor3f(0.0, 0.0, 0.0)
    hs = TENT_BASE
    apex = (0.0, TENT_HEIGHT, 0.0)
    base = [(-hs, 0, -hs), (hs, 0, -hs), (hs, 0, hs), (-hs, 0, hs)]
    glBegin(GL_TRIANGLES)
    for p1, p2 in zip(base, base[1:] + base[:1]):
        glVertex3f(*apex)
        glVertex3f(*p1)
        glVertex3f(*p2)
    glEnd()
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(4)
    glBegin(GL_LINES)
    glVertex3f(0.0, TENT_HEIGHT, 0.0)
    glVertex3f(0.0, 0.0, -hs)
    glEnd()
    glLineWidth(1)

def draw_stones():
    quad = gluNewQuadric()
    glColor3f(0.6, 0.6, 0.6)
    for angle in np.linspace(0, 2 * math.pi, N_STONES, endpoint=False):
        x = PIT_CENTER[0] + PIT_RADIUS * math.cos(angle)
        z = PIT_CENTER[1] + PIT_RADIUS * math.sin(angle)
        glPushMatrix()
        glTranslatef(x, GROUND_Y + STONE_RADIUS, z)
        gluSphere(quad, STONE_RADIUS, 16, 16)
        glPopMatrix()
    gluDeleteQuadric(quad)

def draw_flames():
    quad = gluNewQuadric()
    glColor3f(1.0, 0.5, 0.0)
    for x, z in FLAME_POS:
        glPushMatrix()
        glTranslatef(x, GROUND_Y, z)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quad, FLAME_BASE, 0.0, FLAME_HEIGHT, 16, 1)
        glPopMatrix()
    gluDeleteQuadric(quad)

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
        {'x': p['x'], 'y': p['y'] + dt * SMOKE_RISE_SPEED, 'z': p['z'], 'age': p['age'] + dt}
        for p in smoke_particles if p['age'] + dt < SMOKE_LIFETIME
    ]

def draw_smoke():
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    for p in smoke_particles:
        alpha = max(0.0, 1.0 - p['age'] / SMOKE_LIFETIME)
        size = 0.2 + 0.15 * p['age']
        glColor4f(0.8, 0.8, 0.8, alpha)
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

    # OpenGL setup
    glClearColor(0.5, 0.7, 1.0, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING); glEnable(GL_LIGHT0); glEnable(GL_LIGHT1)
    glEnable(GL_COLOR_MATERIAL); glEnable(GL_NORMALIZE)
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glMatrixMode(GL_PROJECTION); gluPerspective(45, SCREEN_WIDTH / SCREEN_HEIGHT, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)

    cam     = Camera()
    day     = DayNightCycle()
    weather = WeatherSystem()
    terra   = Terrain(GROUND_EXTENT)

    # Spawn trees
    trees = []
    while len(trees) < NUM_TREES:
        x = random.uniform(-SPAWN_RADIUS, SPAWN_RADIUS)
        z = random.uniform(-SPAWN_RADIUS, SPAWN_RADIUS)
        if abs(x) < TENT_BASE + TREE_TENT_BUFFER and abs(z) < TENT_BASE + TREE_TENT_BUFFER:
            continue
        if (x - PIT_CENTER[0])**2 + (z - PIT_CENTER[1])**2 < (PIT_RADIUS + TREE_PIT_BUFFER)**2:
            continue
        trees.append(Tree((x, 0, z), (1, random.uniform(2, 4)), (0, random.uniform(0, 360)), {}))

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

        # Update systems
        keys = pygame.key.get_pressed()
        cam.process_keyboard(keys, dt)
        weather.update(dt)
        day.update("day" if is_day else "night")

        # Campfire light at night
        if not is_day:
            glEnable(GL_LIGHT1)
            fire_x, fire_z = PIT_CENTER
            fire_y = GROUND_Y + 0.2
            glLightfv(GL_LIGHT1, GL_POSITION,           (fire_x, fire_y, fire_z, 1.0))
            glLightfv(GL_LIGHT1, GL_AMBIENT,            (0.4, 0.2, 0.1, 1.0))
            glLightfv(GL_LIGHT1, GL_DIFFUSE,            (1.0, 0.8, 0.4, 1.0))
            glLightfv(GL_LIGHT1, GL_SPECULAR,           (1.0, 0.8, 0.4, 1.0))
            glLightf(GL_LIGHT1, GL_CONSTANT_ATTENUATION,0.1)
            glLightf(GL_LIGHT1, GL_LINEAR_ATTENUATION,  0.01)
            glLightf(GL_LIGHT1, GL_QUADRATIC_ATTENUATION,0.002)
        else:
            glDisable(GL_LIGHT1)

        # Smoke spawn & update
        if smoke_timer > 0.1:
            spawn_smoke()
            smoke_timer = 0.0
        update_smoke(dt)

        # Render scene
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

                            [random.uniform(-20,20), random.uniform(10,20), random.uniform(-20,20), random.uniform(9,12)]
