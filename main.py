def main():
    global quad_smoke, smoke_timer

    pygame.init()
    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), DOUBLEBUF | OPENGL)
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()

    # OpenGL init
    glClearColor(0.5,0.7,1.0,1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING);   glEnable(GL_LIGHT0); glEnable(GL_LIGHT1)
    glEnable(GL_COLOR_MATERIAL); glEnable(GL_NORMALIZE)
    glEnable(GL_BLEND);       glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, SCREEN_WIDTH/SCREEN_HEIGHT, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)

    # Instantiate systems
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
        trees.append(Tree((x,0,z), (1, random.uniform(2,4)), (0, random.uniform(0,360)), {}))

    quad_smoke  = gluNewQuadric()
    smoke_timer = 0.0
    is_day      = True

    # Main loop
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
                    if weather.rain_enabled:
                        weather.rain_particles = [
                            [random.uniform(-20,20),
                             random.uniform(10,20),
                             random.uniform(-20,20),
                             random.uniform(9,12)]
                            for _ in range(10)
                        ]
                    else:
                        weather.rain_particles = []
                elif ev.key == K_f:
                    weather.fog_density = 0.02 if weather.fog_density == 0 else 0.0
                elif ev.key == K_l:
                    weather.lightning_enabled = not weather.lightning_enabled
                    if weather.lightning_enabled and not weather.rain_enabled:
                        weather.rain_enabled = True
                        weather.rain_particles = [
                            [random.uniform(-20,20),
                             random.uniform(10,20),
                             random.uniform(-20,20),
                             random.uniform(9,12)]
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
            glLightfv(GL_LIGHT1, GL_POSITION,              (fire_x, fire_y, fire_z, 1.0))
            glLightfv(GL_LIGHT1, GL_AMBIENT,               (0.4, 0.2, 0.1, 1.0))
            glLightfv(GL_LIGHT1, GL_DIFFUSE,               (1.0, 0.8, 0.4, 1.0))
            glLightfv(GL_LIGHT1, GL_SPECULAR,              (1.0, 0.8, 0.4, 1.0))
            glLightf(GL_LIGHT1, GL_CONSTANT_ATTENUATION,   0.1)
            glLightf(GL_LIGHT1, GL_LINEAR_ATTENUATION,     0.01)
            glLightf(GL_LIGHT1, GL_QUADRATIC_ATTENUATION,  0.002)
        else:
            glDisable(GL_LIGHT1)

        # Smoke spawn & update
        if smoke_timer > 0.1:
            spawn_smoke()
            smoke_timer = 0.0
        update_smoke(dt)

        # Render
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

    # Clean up
    gluDeleteQuadric(quad_smoke)
    pygame.quit()

if __name__ == "__main__":
    main()
