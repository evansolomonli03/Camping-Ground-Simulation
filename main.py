import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import random
import math
from pyglm import glm

s_width, s_height = 800, 600
plot_l = 50.0
plot_h = 0.0

class WeatherSystem:
    def __init__(self):
        self.rp  = []
        self.fd  = 0.0
        self.rain  = False
        self.lightning = False
        self.la = False
        self.li = 0.0
        self.lt = 0.0
        self.lc = random.uniform(5,15)
    def update(self, dt):
        if self.rain:
            if len(self.rp) < 1000:
                for _ in range(10):
                    x = random.uniform(-20,20)
                    y = random.uniform(10,20)
                    z = random.uniform(-20,20)
                    sp = random.uniform(9,12)
                    self.rp.append([x,y,z,sp])
            self.rp = [
                [x, y - sp*dt, z, sp]
                for x,y,z,sp in self.rp
                if (y - sp*dt) > 0
            ]
        else:
            self.rp.clear()
        if self.lightning and self.rain:
            if self.la:
                self.lt -= dt
                if self.lt <= 0:
                    self.la = False
                    self.li = 0.0
                    self.lc = random.uniform(5,15)
            else:
                self.lc -= dt
                if self.lc <= 0 and random.random() < 0.1:
                    self.la = True
                    self.li = random.uniform(0.5,1.0)
                    self.lt = random.uniform(0.05,0.2)
        else:
            self.la = False
            self.li = 0.0
            self.lc = random.uniform(5,15)
    def render(self):
        if self.fd > 0:
            glFogi(GL_FOG_MODE, GL_EXP2)
            glFogfv(GL_FOG_COLOR, (0.5,0.5,0.5,1.0))
            glFogf(GL_FOG_DENSITY, self.fd)
            glEnable(GL_FOG)
        else:
            glDisable(GL_FOG)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glColor3f(0.7,0.8,1.0)
        for x,y,z,_ in self.rp:
            glVertex3f(x, y, z)
            glVertex3f(x, y-1, z)
        glEnd()
        glLineWidth(1.0)
        if self.la:
            ambient = self.li
        else:
            ambient = 0.2
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (ambient, ambient, ambient, 1.0))

class LSystem:
    def __init__(self, axiom, rules, iterations):
        self.axiom = axiom
        self.rules = rules
        self.iterations = iterations
    def generate(self):
        result = self.axiom
        for _ in range(self.iterations):
            new_result = ""
            for char in result:
                if char in self.rules:
                    new_result += self.rules[char]
                else:
                    new_result += char
            result = new_result
        return result

tree_count = 1000
tent_buffer = 1.0
pit_buffer = 0.5
sp_rad = 60.0

class Tree:
    def __init__(self, position, scale, rotation, params):
        self.position = position
        self.scale = scale
        self.rotation = rotation
        axiom = params.get("axiom", "F")
        rules = params.get("rules", {"F": "FF+[+F-F-F]-[-F+F+F]"})
        iterations = params.get("iterations", 3)
        self.lsys = LSystem(axiom, rules, iterations)
        self.display_list = self._build_display_list()
    def _build_display_list(self):
        dl = glGenLists(1)
        glNewList(dl, GL_COMPILE)
        glPushMatrix()
        glTranslatef(self.position[0], self.position[1], self.position[2])
        glRotatef(self.rotation[1], 0, 1, 0)  
        glRotatef(-90, 1, 0, 0)                
        glColor3f(0.6, 0.3, 0.1)
        q = gluNewQuadric()
        base_radius = 0.1 * self.scale[0]
        top_radius = 0.08 * self.scale[0]
        height_trunk = 1.0 * self.scale[1]
        gluCylinder(q, base_radius, top_radius, height_trunk, 8, 4)
        gluDeleteQuadric(q)
        glTranslatef(0, 0, 0.7 * self.scale[1])
        glColor3f(0.1, 0.6, 0.1)
        q2 = gluNewQuadric()
        base_foliage = 0.5 * self.scale[0]
        height_foliage = 1.5 * self.scale[1]
        gluCylinder(q2, base_foliage, 0.0, height_foliage, 10, 4)
        gluDeleteQuadric(q2)
        glPopMatrix()
        glEndList()
        return dl
    def render(self):
        glCallList(self.display_list)

class Terrain:
    def __init__(self, size=plot_l):
        self.size = size
    def render_ground(self):
        glColor3f(0.3, 0.5, 0.2)
        half = self.size
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        glVertex3f(-half, plot_h, -half)
        glVertex3f(-half, plot_h,  half)
        glVertex3f( half, plot_h,  half)
        glVertex3f( half, plot_h, -half)
        glEnd()

class DayNightCycle:
    def __init__(self):
        self.t = 0.25
        self.size = 5.0
        self.slist = self.make_sun()
        self.spos = [0.0, 0.0, 0.0]
    def make_sun(self):
        sun_id = glGenLists(1)
        glNewList(sun_id, GL_COMPILE)
        quad = gluNewQuadric()
        gluSphere(quad, self.size, 20, 20)
        gluDeleteQuadric(quad)
        glEndList()
        return sun_id
    def update(self, mode):
        if mode == "day":
            self.t = 0.25
        else:
            self.t = 0.75
        angle = self.t * 2 * math.pi
        radius = 80.0
        height = max(0.0, math.sin(angle)) * radius
        horiz = -math.cos(angle) * radius
        self.spos = [0.0, height, horiz]
    def get_light_dir(self):
        angle = self.t * 2 * math.pi
        y = max(0.1, math.sin(angle))
        return (0.0, y, -math.cos(angle), 0.0)
    def apply(self):
        if self.t < 0.5:
            base_color = (1.0, 1.0, 1.0, 1.0)
        else:
            base_color = (0.05, 0.05, 0.1, 1.0)
        fade = max(0.0, math.sin(self.t * 2 * math.pi))
        diffuse = tuple(c * fade for c in base_color)
        glLightfv(GL_LIGHT0, GL_POSITION, self.get_light_dir())
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  diffuse)
        glLightfv(GL_LIGHT0, GL_SPECULAR, diffuse)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, diffuse)
    def render_sun(self):
        if self.spos[1] <= 0:
            return
        glDisable(GL_LIGHTING)
        glColor3f(1.0, 1.0, 0.8)
        glPushMatrix()
        glTranslatef(self.spos[0], self.spos[1], self.spos[2])
        glCallList(self.slist)
        glPopMatrix()
        glEnable(GL_LIGHTING)

rotation_sense = 0.3
zoom = 1.0

class Camera:
    def __init__(self):
        self.position = glm.vec3(0.0, 2.0, 10.0)
        self.front = glm.vec3(0.0, 0.0, -1.0)
        self.up = glm.vec3(0.0, 1.0, 0.0)
        self.yaw = -90.0
        self.pitch = 0.0
        self.move_speed = 5.0
        self.sensitivity = 0.05
        self._update_vectors()
    def _update_vectors(self):
        fx = math.cos(math.radians(self.yaw)) * math.cos(math.radians(self.pitch))
        fy = math.sin(math.radians(self.pitch))
        fz = math.sin(math.radians(self.yaw)) * math.cos(math.radians(self.pitch))
        self.front = glm.normalize(glm.vec3(fx, fy, fz))
        right = glm.cross(self.front, glm.vec3(0,1,0))
        self.up = glm.normalize(glm.cross(right, self.front))
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
        self.yaw += dx * self.sensitivity
        self.pitch -= dy * self.sensitivity
        self.pitch = max(-89.0, min(89.0, self.pitch))
        self._update_vectors()
    def zoom(self, amt):
        self.position += self.front * amt
    def apply(self):
        view = glm.lookAt(self.position, self.position + self.front, self.up)
        data = [view[i][j] for i in range(4) for j in range(4)]
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glMultMatrixf(data)

t_base = 1.0
t_height = 1.5

def draw_tent():
    hs = t_base
    apex = (0.0, t_height, 0.0)
    corners = [(-hs, 0, -hs), ( hs, 0, -hs), ( hs, 0,  hs), (-hs, 0,  hs), ]
    glColor3f(0.0, 0.0, 0.0)
    glBegin(GL_TRIANGLES)
    for i in range(4):
        glVertex3f(*apex)
        glVertex3f(*corners[i])
        glVertex3f(*corners[(i + 1) % 4])
    glEnd()
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(4)
    glBegin(GL_LINES)
    glVertex3f(0.0, t_height, 0.0)
    glVertex3f(0.0, 0.0, -hs)
    glEnd()
    glLineWidth(1)

cf_cent = (-1.2, -1.7)
cf_rad = 0.5
s_amount = 13
s_rad = 0.12

def draw_stones():
    quad = gluNewQuadric()
    glColor3f(0.6, 0.6, 0.6)
    for i in range(s_amount):
        angle = 2 * math.pi * i / s_amount
        x = cf_cent[0] + cf_rad * math.cos(angle)
        z = cf_cent[1] + cf_rad * math.sin(angle)
        y = plot_h + s_rad
        glPushMatrix()
        glTranslatef(x, y, z)
        gluSphere(quad, s_rad, 16, 16)
        glPopMatrix()
    gluDeleteQuadric(quad)

f_height = 0.6
f_base = 0.1
f_pos = [ (cf_cent[0] + 0.2, cf_cent[1]), (cf_cent[0] - 0.2, cf_cent[1]), (cf_cent[0], cf_cent[1] + 0.2), ]

def draw_flames():
    quad = gluNewQuadric()
    glColor3f(1.0, 0.5, 0.0)
    for fx, fz in f_pos:
        glPushMatrix()
        glTranslatef(fx, plot_h, fz)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quad, f_base, 0.0, f_height, 16, 1)
        glPopMatrix()
    gluDeleteQuadric(quad)

s_rs = 1.0
s_life = 3.0
s_bh = plot_h + 0.05
s_bs = 0.1

smoke_p = []
q_smoke = None
smoke_t = 0.0

def spawn_smoke():
    for _ in range(4):
        x = cf_cent[0] + random.uniform(-s_bs, s_bs)
        y = s_bh
        z = cf_cent[1] + random.uniform(-s_bs, s_bs)
        smoke_p.append({
            'x': x,
            'y': y,
            'z': z,
            'age': 0.0
        })

def update_smoke(dt):
    new_list = []
    for p in smoke_p:
        p['age'] += dt
        if p['age'] < s_life:
            p['y'] += s_rs * dt
            new_list.append(p)
    smoke_p[:] = new_list

def draw_smoke():
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    for puff in smoke_p:
        alpha = 1.0 - (puff['age'] / s_life)
        if alpha < 0.0:
            alpha = 0.0
        size = 0.2 + 0.15 * puff['age']
        glColor4f(0.8, 0.8, 0.8, alpha)
        glPushMatrix()
        glTranslatef(puff['x'], puff['y'], puff['z'])
        gluSphere(q_smoke, size, 8, 8)
        glPopMatrix()
    glDisable(GL_BLEND)

def main():
    global q_smoke, smoke_t

    pygame.init()
    pygame.display.set_mode((s_width, s_height), DOUBLEBUF | OPENGL)
    pygame.mouse.set_visible(True)
    clock = pygame.time.Clock()

    glClearColor(0.5,0.7,1.0,1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING); 
    glEnable(GL_LIGHT0); 
    glEnable(GL_LIGHT1)
    glEnable(GL_COLOR_MATERIAL); 
    glEnable(GL_NORMALIZE)
    glEnable(GL_BLEND); 
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glMatrixMode(GL_PROJECTION); 
    gluPerspective(45, s_width/s_height, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)

    cam = Camera()
    day = DayNightCycle()
    weather = WeatherSystem()
    terra = Terrain(plot_l)

    trees = []
    while len(trees) < tree_count:
        x = random.uniform(-sp_rad, sp_rad)
        z = random.uniform(-sp_rad, sp_rad)
        if abs(x) < t_base + tent_buffer and abs(z) < t_base + tent_buffer:
            continue
        if (x - cf_cent[0])**2 + (z - cf_cent[1])**2 < (cf_rad + pit_buffer)**2:
            continue
        trees.append(Tree((x,0,z), (1, random.uniform(2,4)), (0, random.uniform(0,360)), {}))

    q_smoke = gluNewQuadric()
    smoke_t = 0.0
    is_day = True

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        smoke_t += dt

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
                    weather.rain = not weather.rain
                    weather.rp= [] if not weather.rain else [
                        [random.uniform(-20,20), random.uniform(10,20), random.uniform(-20,20), random.uniform(9,12)]
                        for _ in range(10)
                    ]
                elif ev.key == K_f:
                    weather.fd = 0.02 if weather.fd == 0 else 0.0
                elif ev.key == K_l:
                    weather.lightning = not weather.lightning
                    if weather.lightning and not weather.rain:
                        weather.rain = True
                        weather.rp= [
                            [random.uniform(-20,20), random.uniform(10,20), random.uniform(-20,20), random.uniform(9,12)]
                            for _ in range(10)
                        ]
            elif ev.type == MOUSEBUTTONDOWN:
                if ev.button == 4:
                    cam.zoom(zoom)
                elif ev.button == 5:
                    cam.zoom(-zoom)
            elif ev.type == MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                dx, dy = ev.rel
                cam.process_mouse(dx, dy)

        keys = pygame.key.get_pressed()
        cam.process_keyboard(keys, dt)
        weather.update(dt)
        day.update("day" if is_day else "night")

        if not is_day:
            glEnable(GL_LIGHT1)
            fire_x, fire_z = cf_cent
            fire_y = plot_h + 0.2

            glLightfv(GL_LIGHT1, GL_POSITION, (fire_x, fire_y, fire_z, 1.0))

            glLightfv(GL_LIGHT1, GL_AMBIENT, (0.4, 0.2, 0.1, 1.0))
            glLightfv(GL_LIGHT1, GL_DIFFUSE, (1.0, 0.8, 0.4, 1.0))
            glLightfv(GL_LIGHT1, GL_SPECULAR, (1.0, 0.8, 0.4, 1.0))
            glLightf(GL_LIGHT1, GL_CONSTANT_ATTENUATION, 0.1)
            glLightf(GL_LIGHT1, GL_LINEAR_ATTENUATION, 0.01)
            glLightf(GL_LIGHT1, GL_QUADRATIC_ATTENUATION, 0.002)
        else:
            glDisable(GL_LIGHT1)

        if smoke_t > 0.1:
            spawn_smoke()
            smoke_t = 0.0
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

    gluDeleteQuadric(q_smoke)
    pygame.quit()

if __name__ == "__main__":
    main()
