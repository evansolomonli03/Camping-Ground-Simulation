import math
import random
from OpenGL.GL import *
from OpenGL.GLU import *


class LSystem:
    def __init__(self, axiom, rules, iterations):
        self.axiom = axiom
        self.rules = rules
        self.iterations = iterations
        self.result = ""

    def generate(self):
        self.result = self.axiom
        for _ in range(self.iterations):
            next_gen = ""
            for char in self.result:
                if char in self.rules:
                    next_gen += self.rules[char]
                else:
                    next_gen += char
            self.result = next_gen
        return self.result


class Tree:
    def __init__(self, position, scale, rotation, lsystem_params):
        self.position = position
        self.scale = scale
        self.rotation = rotation

        # L-System setup
        axiom = lsystem_params.get("axiom", "F")
        rules = lsystem_params.get("rules", {"F": "FF+[+F-F-F]-[-F+F+F]"})
        iterations = lsystem_params.get("iterations", 3)

        self.lsystem = LSystem(axiom, rules, iterations)
        self.commands = self.lsystem.generate()
        self.display_list = self.compile_display_list()

    def compile_display_list(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)

        glPushMatrix()
        # Position at the tree's location
        glTranslatef(self.position[0], self.position[1], self.position[2])
        # Apply rotation around Y axis only
        glRotatef(self.rotation[1], 0, 1, 0)

        # IMPORTANT: Rotate 90 degrees around X-axis to make cylinders stand upright
        glRotatef(-90, 1, 0, 0)  # This is the key change!

        # Draw trunk as cylinder
        glColor3f(0.6, 0.3, 0.1)  # Brown
        trunk = gluNewQuadric()
        gluCylinder(trunk, 0.1 * self.scale[0], 0.08 * self.scale[0], 1.0 * self.scale[1], 8, 4)
        gluDeleteQuadric(trunk)

        # Position for foliage on top of trunk
        glTranslatef(0, 0, 0.7 * self.scale[1])

        # Set foliage color
        glColor3f(0.1, 0.6, 0.1)  # Green

        # Draw foliage as cone
        foliage = gluNewQuadric()
        gluCylinder(foliage, 0.5 * self.scale[0], 0, 1.5 * self.scale[1], 10, 4)
        gluDeleteQuadric(foliage)

        glPopMatrix()
        glEndList()
        return display_list

    def render(self):
        glCallList(self.display_list)