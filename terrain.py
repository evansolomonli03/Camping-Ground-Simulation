from OpenGL.GL import *

class Terrain:
    def __init__(self, size=50.0):
        self.size = size

    def render_ground(self):
        glColor3f(0.3,0.5,0.2)
        glBegin(GL_QUADS)
        glNormal3f(0,1,0)
        s = self.size
        glVertex3f(-s, 0, -s)
        glVertex3f(-s, 0,  s)
        glVertex3f( s, 0,  s)
        glVertex3f( s, 0, -s)
        glEnd()
