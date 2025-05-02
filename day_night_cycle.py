import math
from OpenGL.GL import *
from OpenGL.GLU import *


class DayNightCycle:
    def __init__(self):
        self.time = 0.0  # 0.0 = dawn, 0.25 = noon, 0.5 = dusk, 0.75 = midnight
        self.day_duration = 600.0  # seconds for a full day cycle

        # Light colors for different times
        self.dawn_light = (0.8, 0.6, 0.4, 1.0)
        self.day_light = (1.0, 1.0, 1.0, 1.0)
        self.dusk_light = (0.6, 0.4, 0.3, 1.0)
        self.night_light = (0.1, 0.1, 0.2, 1.0)

        # Ambient colors for different times
        self.dawn_ambient = (0.3, 0.2, 0.2, 1.0)
        self.day_ambient = (0.4, 0.4, 0.4, 1.0)
        self.dusk_ambient = (0.2, 0.2, 0.3, 1.0)
        self.night_ambient = (0.05, 0.05, 0.1, 1.0)

        # Add sun parameters
        self.sun_position = [0.0, 0.0, 0.0]
        self.sun_size = 5.0  # Size of the sun
        self.sun_display_list = self.create_sun_display_list()

    def create_sun_display_list(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)

        quad = gluNewQuadric()
        gluSphere(quad, self.sun_size, 20, 20)
        gluDeleteQuadric(quad)

        glEndList()
        return display_list

    def update(self, delta_time):
        self.time += delta_time / self.day_duration
        if self.time >= 1.0:
            self.time -= 1.0

        # Update sun position based on time
        angle = self.time * 2 * math.pi
        distance = 80.0  # Distance from center
        self.sun_position[0] = math.cos(angle) * distance
        self.sun_position[1] = math.sin(angle) * distance
        if self.sun_position[1] < 0:
            self.sun_position[1] *= 0.2  # Flatten trajectory below horizon
        self.sun_position[2] = 0

    def get_light_direction(self):
        # Light rotates around the scene
        angle = self.time * 2 * math.pi
        x = math.cos(angle)
        y = math.sin(angle)
        if y < 0:
            y *= 0.2  # Flatten trajectory when below horizon
        return (x, max(0.1, y), 0.0, 0.0)

    def get_light_color(self):
        if self.time < 0.25:  # Dawn to day
            t = self.time / 0.25
            return self.interpolate_color(self.dawn_light, self.day_light, t)
        elif self.time < 0.5:  # Day to dusk
            t = (self.time - 0.25) / 0.25
            return self.interpolate_color(self.day_light, self.dusk_light, t)
        elif self.time < 0.75:  # Dusk to night
            t = (self.time - 0.5) / 0.25
            return self.interpolate_color(self.dusk_light, self.night_light, t)
        else:  # Night to dawn
            t = (self.time - 0.75) / 0.25
            return self.interpolate_color(self.night_light, self.dawn_light, t)

    def get_ambient_color(self):
        if self.time < 0.25:  # Dawn to day
            t = self.time / 0.25
            return self.interpolate_color(self.dawn_ambient, self.day_ambient, t)
        elif self.time < 0.5:  # Day to dusk
            t = (self.time - 0.25) / 0.25
            return self.interpolate_color(self.day_ambient, self.dusk_ambient, t)
        elif self.time < 0.75:  # Dusk to night
            t = (self.time - 0.5) / 0.25
            return self.interpolate_color(self.dusk_ambient, self.night_ambient, t)
        else:  # Night to dawn
            t = (self.time - 0.75) / 0.25
            return self.interpolate_color(self.night_ambient, self.dawn_ambient, t)

    def interpolate_color(self, color1, color2, t):
        return (
            color1[0] * (1 - t) + color2[0] * t,
            color1[1] * (1 - t) + color2[1] * t,
            color1[2] * (1 - t) + color2[2] * t,
            color1[3] * (1 - t) + color2[3] * t
        )

    def apply(self, weather_system=None):
        # Set the main directional light
        glLightfv(GL_LIGHT0, GL_POSITION, self.get_light_direction())

        # Adjust light color based on weather
        light_color = self.get_light_color()
        ambient_color = self.get_ambient_color()

        # Dim light if foggy or raining
        if weather_system:
            if weather_system.fog_density > 0:
                # Reduce light intensity by fog density
                light_color = tuple(c * (1 - weather_system.fog_density * 10) for c in light_color)

            if hasattr(weather_system, 'rain_enabled') and weather_system.rain_enabled:
                # Reduce light intensity during rain
                light_color = tuple(c * 0.7 for c in light_color)
                ambient_color = tuple(c * 0.7 for c in ambient_color)

        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_color)
        glLightfv(GL_LIGHT0, GL_SPECULAR, light_color)

        # Set ambient light
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, ambient_color)

    def render_sun(self, weather_system=None):
        # Only render sun when it's above horizon
        if self.sun_position[1] <= 0:
            return

        glPushMatrix()
        glTranslatef(self.sun_position[0], self.sun_position[1], self.sun_position[2])

        # Choose sun color based on time of day
        if self.time < 0.25 or self.time > 0.75:  # Dawn/dusk
            sun_color = (1.0, 0.7, 0.3)  # Orange
        else:  # Day
            sun_color = (1.0, 1.0, 0.8)  # Bright yellow

        # Dim sun color if foggy or raining
        if weather_system:
            if weather_system.fog_density > 0:
                # Make sun appear dimmer in fog
                fog_factor = 1.0 - weather_system.fog_density * 5
                sun_color = tuple(max(0.2, c * fog_factor) for c in sun_color)

            if hasattr(weather_system, 'rain_enabled') and weather_system.rain_enabled:
                # Make sun even dimmer in rain
                sun_color = tuple(c * 0.6 for c in sun_color)

        # Disable lighting for the sun so it's always bright
        glDisable(GL_LIGHTING)
        glColor3fv(sun_color)

        # Draw the sun
        glCallList(self.sun_display_list)

        # Re-enable lighting
        glEnable(GL_LIGHTING)
        glPopMatrix()