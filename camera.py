import math
from pyglm import glm
from pygame.locals import *

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
        if keys[K_w]:       self.position += self.front * v
        if keys[K_s]:       self.position -= self.front * v
        if keys[K_a]:       self.position -= glm.cross(self.front, self.up) * v
        if keys[K_d]:       self.position += glm.cross(self.front, self.up) * v
        if keys[K_SPACE]:   self.position.y += v
        if keys[K_LSHIFT]:  self.position.y -= v

    def process_mouse(self, dx, dy):
        if abs(dx)>100 or abs(dy)>100: return
        self.yaw   += dx * self.sensitivity
        self.pitch -= dy * self.sensitivity
        self.pitch  = max(-89.0, min(89.0, self.pitch))
        self._update_vectors()

    def zoom(self, amount):
        self.position += self.front * amount

    def apply(self):
        view = glm.lookAt(self.position, self.position + self.front, self.up)
        data = [view[i][j] for i in range(4) for j in range(4)]
        from OpenGL.GL import glMatrixMode, glLoadIdentity, glMultMatrixf, GL_MODELVIEW
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glMultMatrixf(data)
