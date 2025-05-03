import math
from OpenGL.GL import *
from OpenGL.GLU import *

class DayNightCycle:
    def __init__(self):
        self.time     = 0.25
        self.sun_size = 5.0
        self.sun_dl   = self._make_sun()
        self.sun_pos  = [0.0, 0.0, 0.0]

    def _make_sun(self):
        dl = glGenLists(1)
        glNewList(dl, GL_COMPILE)
        quad = gluNewQuadric()
        gluSphere(quad, self.sun_size, 20, 20)
        gluDeleteQuadric(quad)
        glEndList()
        return dl

    def update(self, mode):
        # mode: "day" or "night"
        self.time = 0.25 if mode == "day" else 0.75
        ang = self.time * 2 * math.pi
        d   = 80.0
        sy, cy = math.sin(ang), math.cos(ang)
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
        if self.sun_pos[1] <= 0: return
        glDisable(GL_LIGHTING)
        glColor3f(1.0,1.0,0.8)
        glPushMatrix()
        glTranslatef(*self.sun_pos)
        glCallList(self.sun_dl)
        glPopMatrix()
        glEnable(GL_LIGHTING)
