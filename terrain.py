from OpenGL.GL import *


class Terrain:
    def __init__(self):
        # We'll keep it simple for now
        pass

    def render_ground(self):
        glBegin(GL_QUADS)
        glColor3f(0.3, 0.5, 0.2)  # Grass color
        glNormal3f(0, 1, 0)
        glVertex3f(-50, 0, -50)
        glVertex3f(-50, 0, 50)
        glVertex3f(50, 0, 50)
        glVertex3f(50, 0, -50)
        glEnd()