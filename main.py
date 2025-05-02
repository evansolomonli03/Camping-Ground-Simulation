import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import random
import math
from pyglm import glm

# ───── Configuration ─────────────────────────────────────────────────────────────
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600

# Ground
GROUND_SIZE = 6.0    # reduced from 8.0 to make plot smaller
GROUND_Y    = 0.0

# Tent (pyramid)
TENT_BASE   = 1.0
TENT_HEIGHT = 1.5

# Fire‑pit
PIT_CENTER  = (-1.2, -1.7)
PIT_RADIUS  = 0.5
N_STONES    = 13
STONE_RADIUS= 0.12

# Flames
FLAME_HEIGHT = 0.6
FLAME_BASE   = 0.1
FLAME_POS    = [
    (PIT_CENTER[0] + 0.2, PIT_CENTER[1]),
    (PIT_CENTER[0] - 0.2, PIT_CENTER[1]),
    (PIT_CENTER[0],       PIT_CENTER[1] + 0.2),
]

# Smoke
SMOKE_RISE_SPEED  = 1.0
SMOKE_LIFETIME    = 3.0
SMOKE_BASE_HEIGHT = GROUND_Y + 0.05
SMOKE_BASE_SPREAD = 0.1

# Tree spawn buffers
TREE_TENT_BUFFER = 1.0
TREE_PIT_BUFFER  = 0.5

# Mouse‑drag sensitivity
ROT_SENS = 0.3

# Zoom amount per scroll
ZOOM_AMOUNT = 1.0

# ───── Weather System ─────────────────────────────────────────────────────────────
class WeatherSystem:
    def __init__(self):
        self.rain_particles = []
        self.fog_density = 0.0
        self.lightning_active = False
        self.lightning_intensity = 0.0
        self.lightning_duration = 0.0
        self.lightning_cooldown = 0.0
        self.rain_enabled = False
        self.lightning_enabled = False

    def update(self, dt):
        self._update_rain(dt)
        if self.rain_enabled and self.lightning_enabled:
            self._update_lightning(dt)
        else:
            self.lightning_active = False
            self.lightning_intensity = 0.0

    def _update_rain(self, dt):
        if not self.rain_enabled: return
        if len(self.rain_particles) < 1000:
            for _ in range(10):
                x = random.uniform(-20,20)
                y = random.uniform(10,20)
                z = random.uniform(-20,20)
                speed = random.uniform(9,12)
                self.rain_particles.append([x,y,z,speed])
        new = []
        for p in self.rain_particles:
            p[1] -= p[3] * dt
            if p[1] > 0: new.append(p)
        self.rain_particles = new

    def _update_lightning(self, dt):
        if self.lightning_active:
            self.lightning_duration -= dt
            if self.lightning_duration <= 0:
                self.lightning_active = False
                self.lightning_intensity = 0.0
                self.lightning_cooldown = random.uniform(5,15)
        else:
            self.lightning_cooldown -= dt
            if self.lightning_cooldown <= 0 and random.random() < 0.1:
                self.lightning_active = True
                self.lightning_intensity = random.uniform(0.5,1.0)
                self.lightning_duration = random.uniform(0.05,0.2)

    def render(self):
        # Fog
        if self.fog_density > 0:
            glFogi(GL_FOG_MODE, GL_EXP2)
            glFogfv(GL_FOG_COLOR, (0.5,0.5,0.5,1.0))
            glFogf(GL_FOG_DENSITY, self.fog_density)
            glEnable(GL_FOG)
        else:
            glDisable(GL_FOG)
        # Rain
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glColor3f(0.7,0.8,1.0)
        for p in self.rain_particles:
            glVertex3f(p[0],p[1],p[2])
            glVertex3f(p[0],p[1]-1.0,p[2])
        glEnd(); glLineWidth(1.0)
        # Lightning flicker
        if self.lightning_active:
            amb = (self.lightning_intensity,)*3 + (1.0,)
            glLightModelfv(GL_LIGHT_MODEL_AMBIENT, amb)
        else:
            glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.2,0.2,0.2,1.0))

# ───── L-System & Tree ────────────────────────────────────────────────────────────
class LSystem:
    def __init__(self, axiom, rules, iterations):
        self.axiom = axiom; self.rules = rules; self.iterations = iterations
    def generate(self):
        res = self.axiom
        for _ in range(self.iterations):
            nxt = ""
            for c in res: nxt += self.rules.get(c,c)
            res = nxt
        return res

class Tree:
    def __init__(self,pos,scale,rot,params):
        self.pos = pos; self.scale = scale; self.rot = rot
        ax = params.get("axiom","F")
        rules = params.get("rules",{"F":"FF+[+F-F-F]-[-F+F+F]"})
        it = params.get("iterations",3)
        self.lsys = LSystem(ax,rules,it)
        self.dl = self._compile()
    def _compile(self):
        dl = glGenLists(1); glNewList(dl,GL_COMPILE)
        glPushMatrix()
        glTranslatef(*self.pos)
        glRotatef(self.rot[1],0,1,0)
        glRotatef(-90,1,0,0)
        glColor3f(0.6,0.3,0.1)
        q=gluNewQuadric();gluCylinder(q,0.1*self.scale[0],0.08*self.scale[0],1.0*self.scale[1],8,4);gluDeleteQuadric(q)
        glTranslatef(0,0,0.7*self.scale[1])
        glColor3f(0.1,0.6,0.1)
        q2=gluNewQuadric();gluCylinder(q2,0.5*self.scale[0],0,1.5*self.scale[1],10,4);gluDeleteQuadric(q2)
        glPopMatrix(); glEndList()
        return dl
    def render(self): glCallList(self.dl)

# ───── Terrain ───────────────────────────────────────────────────────────────────
class Terrain:
    def __init__(self,size=50): self.size=size
    def render_ground(self):
        glColor3f(0.3,0.5,0.2)
        glBegin(GL_QUADS)
        glNormal3f(0,1,0)
        s=self.size
        glVertex3f(-s,0,-s);glVertex3f(-s,0, s)
        glVertex3f( s,0, s);glVertex3f( s,0,-s)
        glEnd()

# ───── Day-Night Cycle ───────────────────────────────────────────────────────────
class DayNightCycle:
    def __init__(self):
        self.time = 0.0; self.day_duration = 60.0
        self.dawn_light=(0.8,0.6,0.4,1.0);self.day_light=(1.0,1.0,1.0,1.0)
        self.dusk_light=(0.6,0.4,0.3,1.0);self.night_light=(0.1,0.1,0.2,1.0)
        self.dawn_amb=(0.3,0.2,0.2,1.0);self.day_amb=(0.4,0.4,0.4,1.0)
        self.dusk_amb=(0.2,0.2,0.3,1.0);self.night_amb=(0.05,0.05,0.1,1.0)
        self.sun_pos=[0,0,0];self.sun_size=5.0;self.sun_dl=self._make_sun()
    def _make_sun(self):
        dl=glGenLists(1);glNewList(dl,GL_COMPILE)
        q=gluNewQuadric();gluSphere(q,self.sun_size,20,20);gluDeleteQuadric(q)
        glEndList();return dl
    def update(self,dt):
        self.time=(self.time+dt/self.day_duration)%1.0
        ang=self.time*2*math.pi;d=80.0
        sy=math.sin(ang); cy=math.cos(ang)
        # move vertically (y) and forward/back (z) for true arc
        self.sun_pos[0]=0.0
        self.sun_pos[1]=max(0,sy)*d
        self.sun_pos[2]=-cy*d
    def get_light_dir(self):
        ang=self.time*2*math.pi; y=math.sin(ang)
        return (0.0, max(0.1,y), -math.cos(ang), 0.0)
    def _interp(self,c1,c2,t): return tuple(c1[i]*(1-t)+c2[i]*t for i in range(4))
    def get_light_col(self):
        t=self.time
        if t<0.25: return self._interp(self.dawn_light,self.day_light,t/0.25)
        if t<0.5:  return self._interp(self.day_light,self.dusk_light,(t-0.25)/0.25)
        if t<0.75: return self._interp(self.dusk_light,self.night_light,(t-0.5)/0.25)
        return self._interp(self.night_light,self.dawn_light,(t-0.75)/0.25)
    def get_amb(self):
        t=self.time
        if t<0.25: return self._interp(self.dawn_amb,self.day_amb,t/0.25)
        if t<0.5: return self._interp(self.day_amb,self.dusk_amb,(t-0.25)/0.25)
        if t<0.75:return self._interp(self.dusk_amb,self.night_amb,(t-0.5)/0.25)
        return self._interp(self.night_amb,self.dawn_amb,(t-0.75)/0.25)
    def apply(self,weather=None):
        ang=self.time*2*math.pi; f=max(0,math.sin(ang))
        glLightfv(GL_LIGHT0,GL_POSITION,self.get_light_dir())
        lc=self.get_light_col(); ac=self.get_amb()
        lc=tuple(c*f for c in lc);ac=tuple(a*f for a in ac)
        if weather:
            if weather.fog_density>0: lc=tuple(c*(1-weather.fog_density*10) for c in lc)
            if weather.rain_enabled: lc=tuple(c*0.7 for c in lc); ac=tuple(a*0.7 for a in ac)
        glLightfv(GL_LIGHT0,GL_DIFFUSE,lc);glLightfv(GL_LIGHT0,GL_SPECULAR,lc)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT,ac)
    def render_sun(self,weather=None):
        if self.sun_pos[1]<=0: return
        glDisable(GL_LIGHTING)
        t=self.time; col=(1.0,0.7,0.3) if t<0.25 or t>0.75 else (1.0,1.0,0.8)
        if weather and weather.fog_density>0: fogf=max(0.2,1-weather.fog_density*5);col=tuple(c*fogf for c in col)
        if weather and weather.rain_enabled: col=tuple(c*0.6 for c in col)
        glColor3fv(col)
        glPushMatrix();glTranslatef(*self.sun_pos);glCallList(self.sun_dl);glPopMatrix()
        glEnable(GL_LIGHTING)

# ───── Camera ───────────────────────────────────────────────────────────────────
class Camera:
    def __init__(self):
        self.position=glm.vec3(0,2,10);self.front=glm.vec3(0,0,-1);self.up=glm.vec3(0,1,0)
        self.yaw=-90;self.pitch=0;self.speed=5;self.sens=0.05;self._update_vectors()
    def _update_vectors(self):
        fx=math.cos(math.radians(self.yaw))*math.cos(math.radians(self.pitch))
        fy=math.sin(math.radians(self.pitch))
        fz=math.sin(math.radians(self.yaw))*math.cos(math.radians(self.pitch))
        self.front=glm.normalize(glm.vec3(fx,fy,fz)); right=glm.cross(self.front,glm.vec3(0,1,0))
        self.up=glm.normalize(glm.cross(right,self.front))
    def process_keyboard(self,keys,dt):
        v=self.speed*dt
        if keys[K_w]: self.position+=self.front*v
        if keys[K_s]: self.position-=self.front*v
        if keys[K_a]: self.position-=glm.cross(self.front,self.up)*v
        if keys[K_d]: self.position+=glm.cross(self.front,self.up)*v
        if keys[K_SPACE]:self.position.y+=v
        if keys[K_LSHIFT]:self.position.y-=v
    def process_mouse(self,dx,dy):
        if abs(dx)>100 or abs(dy)>100:return
        self.yaw+=dx*self.sens; self.pitch-=dy*self.sens
        self.pitch=max(-89,min(89,self.pitch));self._update_vectors()
    def zoom(self, amount):
        self.position += self.front * amount
    def get_view(self): return glm.lookAt(self.position,self.position+self.front,self.up)
    def apply(self):
        m=self.get_view(); data=[m[i][j] for i in range(4) for j in range(4)]
        glMatrixMode(GL_MODELVIEW);glLoadIdentity();glMultMatrixf(data)

# ───── Drawing Helpers ────────────────────────────────────────────────────────────
def draw_tent():
    glColor3f(0,0,0); hs=TENT_BASE; apex=(0,TENT_HEIGHT,0)
    base=[(-hs,0,-hs),(hs,0,-hs),(hs,0,hs),(-hs,0,hs)]
    glBegin(GL_TRIANGLES)
    for p1,p2 in zip(base,base[1:]+base[:1]):glVertex3f(*apex);glVertex3f(*p1);glVertex3f(*p2)
    glEnd()
    glColor3f(1,1,1);glLineWidth(4)
    glBegin(GL_LINES);glVertex3f(0,TENT_HEIGHT,0);glVertex3f(0,0,-hs);glEnd();glLineWidth(1)

def draw_stones():
    q=gluNewQuadric();glColor3f(0.6,0.6,0.6)
    for a in np.linspace(0,2*math.pi,N_STONES,endpoint=False):
        x=PIT_CENTER[0]+PIT_RADIUS*math.cos(a);z=PIT_CENTER[1]+PIT_RADIUS*math.sin(a)
        glPushMatrix();glTranslatef(x,GROUND_Y+STONE_RADIUS,z);gluSphere(q,STONE_RADIUS,16,16);glPopMatrix()
    gluDeleteQuadric(q)

def draw_flames():
    q=gluNewQuadric();glColor3f(1,0.5,0)
    for x,z in FLAME_POS:
        glPushMatrix();glTranslatef(x,0,z);glRotatef(-90,1,0,0)
        gluCylinder(q,FLAME_BASE,0,FLAME_HEIGHT,16,1);glPopMatrix()
    gluDeleteQuadric(q)

# ───── Smoke ─────────────────────────────────────────────────────────────────────
smoke_particles=[];quad_smoke=None;smoke_timer=0.0
def spawn_smoke():
    for _ in range(4):smoke_particles.append({'x':PIT_CENTER[0]+random.uniform(-SMOKE_BASE_SPREAD,SMOKE_BASE_SPREAD),
                                              'y':SMOKE_BASE_HEIGHT,'z':PIT_CENTER[1]+random.uniform(-SMOKE_BASE_SPREAD,SMOKE_BASE_SPREAD),'age':0})
def update_smoke(dt):
    global smoke_particles
    smoke_particles=[{**p,'y':p['y']+dt*SMOKE_RISE_SPEED,'age':p['age']+dt} for p in smoke_particles if p['age']+dt<SMOKE_LIFETIME]
def draw_smoke():
    glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    for p in smoke_particles:
        alpha=max(0,1-p['age']/SMOKE_LIFETIME);sz=0.2+0.15*p['age']
        glColor4f(0.8,0.8,0.8,alpha);glPushMatrix();glTranslatef(p['x'],p['y'],p['z']);gluSphere(quad_smoke,sz,8,8);glPopMatrix()
    glDisable(GL_BLEND)

# ───── Main ─────────────────────────────────────────────────────────────────────
def main():
    global quad_smoke,smoke_timer
    pygame.init()
    pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT),DOUBLEBUF|OPENGL)
    pygame.mouse.set_visible(False)
    clock=pygame.time.Clock()

    glClearColor(0.5,0.7,1,1);glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING);glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL);glEnable(GL_NORMALIZE)
    glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glMatrixMode(GL_PROJECTION);gluPerspective(45,SCREEN_WIDTH/SCREEN_HEIGHT,0.1,100);glMatrixMode(GL_MODELVIEW)

    cam=Camera();day=DayNightCycle();weather=WeatherSystem();terra=Terrain(50)

    # tree spawn
    trees=[]
    while len(trees)<20:
        x=random.uniform(-5,5);z=random.uniform(-5,5)
        if abs(x)<TENT_BASE+TREE_TENT_BUFFER and abs(z)<TENT_BASE+TREE_TENT_BUFFER:continue
        if (x-PIT_CENTER[0])**2+(z-PIT_CENTER[1])**2<(PIT_RADIUS+TREE_PIT_BUFFER)**2:continue
        trees.append(Tree((x,0,z),(1,random.uniform(2,4)),(0,random.uniform(0,360)),{}))

    quad_smoke=gluNewQuadric();smoke_timer=0.0

    running=True
    while running:
        dt=clock.tick(60)/1000.0
        smoke_timer+=dt
        for ev in pygame.event.get():
            if ev.type==QUIT:running=False
            elif ev.type==MOUSEBUTTONDOWN:
                if ev.button==4:cam.zoom(ZOOM_AMOUNT)
                elif ev.button==5:cam.zoom(-ZOOM_AMOUNT)
            elif ev.type==KEYDOWN:
                if ev.key==K_ESCAPE:running=False
                elif ev.key==K_r:
                    weather.rain_enabled=not weather.rain_enabled
                    weather.rain_particles=[] if not weather.rain_enabled else [[random.uniform(-20,20),random.uniform(10,20),random.uniform(-20,20),random.uniform(9,12)] for _ in range(10)]
                elif ev.key==K_f:weather.fog_density=0.02 if weather.fog_density==0 else 0
                elif ev.key==K_l:
                    weather.lightning_enabled=not weather.lightning_enabled
                    if weather.lightning_enabled and not weather.rain_enabled:
                        weather.rain_enabled=True
                        weather.rain_particles=[[random.uniform(-20,20),random.uniform(10,20),random.uniform(-20,20),random.uniform(9,12)] for _ in range(10)]
            elif ev.type==MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                dx,dy=ev.rel;cam.process_mouse(dx,dy)

        keys=pygame.key.get_pressed();cam.process_keyboard(keys,dt)
        day.update(dt);weather.update(dt)
        if smoke_timer>0.1:spawn_smoke();smoke_timer=0.0
        update_smoke(dt)

        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        cam.apply();day.apply(weather);day.render_sun(weather)
        terra.render_ground()
        for t in trees:t.render()
        draw_tent();draw_stones();draw_flames();weather.render();draw_smoke()
        pygame.display.flip()

    gluDeleteQuadric(quad_smoke)
    pygame.quit()

if __name__=="__main__":
    main()
