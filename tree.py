import math
from OpenGL.GL import *
from OpenGL.GLU import *

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
