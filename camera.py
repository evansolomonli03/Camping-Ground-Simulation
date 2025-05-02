import math
import pygame
from pyglm import glm
from OpenGL.GL import *


class Camera:
    def __init__(self):
        self.position = glm.vec3(0.0, 2.0, 10.0)
        self.front = glm.vec3(0.0, 0.0, -1.0)
        self.up = glm.vec3(0.0, 1.0, 0.0)
        self.right = glm.vec3(1.0, 0.0, 0.0)

        self.yaw = -90.0
        self.pitch = 0.0
        self.move_speed = 5.0
        self.mouse_sensitivity = 0.05  # Reduced from 0.1 for smoother movement

        self.update_vectors()

    def update_vectors(self):
        # Calculate new front vector
        self.front.x = math.cos(math.radians(self.yaw)) * math.cos(math.radians(self.pitch))
        self.front.y = math.sin(math.radians(self.pitch))
        self.front.z = math.sin(math.radians(self.yaw)) * math.cos(math.radians(self.pitch))
        self.front = glm.normalize(self.front)

        # Recalculate right and up vectors
        self.right = glm.normalize(glm.cross(self.front, glm.vec3(0.0, 1.0, 0.0)))
        self.up = glm.normalize(glm.cross(self.right, self.front))

    def process_keyboard(self, keys, delta_time):
        velocity = self.move_speed * delta_time

        if keys[pygame.K_w]:
            self.position += self.front * velocity
        if keys[pygame.K_s]:
            self.position -= self.front * velocity
        if keys[pygame.K_a]:
            self.position -= self.right * velocity
        if keys[pygame.K_d]:
            self.position += self.right * velocity
        if keys[pygame.K_SPACE]:
            self.position.y += velocity
        if keys[pygame.K_LSHIFT]:
            self.position.y -= velocity

    def process_mouse(self, x_offset, y_offset):
        # Make sure we're getting reasonable values for mouse movement
        if abs(x_offset) > 100 or abs(y_offset) > 100:
            return  # Skip processing if movement is too large

        self.yaw += x_offset * self.mouse_sensitivity
        self.pitch -= y_offset * self.mouse_sensitivity

        # Constrain pitch
        if self.pitch > 89.0:
            self.pitch = 89.0
        if self.pitch < -89.0:
            self.pitch = -89.0

        self.update_vectors()

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.position + self.front, self.up)

    def apply(self):
        view_matrix = self.get_view_matrix()
        # Convert to a flat list that OpenGL can use
        matrix_data = []
        for i in range(4):
            for j in range(4):
                matrix_data.append(view_matrix[i][j])

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glMultMatrixf(matrix_data)