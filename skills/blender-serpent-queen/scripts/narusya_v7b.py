import bpy
import math
import random

# ============================================================
# NARUSYA v7b — Serpent Queen Avatar (Blender 4.0.2, headless)
# Smooth helical coil, tapered body, dark purple + purple rim,
# green accents on data/wire elements only, gold crown, red eyes
# 
# Run: blender --background --python narusya_v7b.py
# Output: /tmp/narusya_v7b.png (1024x1024)
# ============================================================

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# --- COLORS ---
C_BODY      = (0.03, 0.008, 0.06, 1.0)     # Dark purple core
C_PURPLE    = (0.4, 0.0, 0.8, 1.0)          # Purple edge glow
C_GREEN     = (0.0, 0.95, 0.35, 1.0)        # Electric green
C_GOLD      = (1.0, 0.85, 0.15, 1.0)        # Rich gold
C_RED       = (1.0, 0.02, 0.06, 1.0)        # Blood red

def mat(name, base, emit, emit_str, metal=0, rough=0.4):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes['Principled BSDF']
    n.inputs['Base Color'].default_value = base
    n.inputs['Emission Color'].default_value = emit
    n.inputs['Emission Strength'].default_value = emit_str
    n.inputs['Metallic'].default_value = metal
    n.inputs['Roughness'].default_value = rough
    return m

# KEY LESSON: Keep emission LOW (0.3-15 range) to avoid blown-out look
m_body = mat("Body", C_BODY, C_PURPLE, 0.3, 0.85, 0.18)
m_green = mat("Green", C_GREEN, C_GREEN, 8.0, 0, 0.05)
m_wire = mat("Wire", (0,0,0,1), C_GREEN, 10.0, 0, 0.0)
m_gold = mat("Gold", C_GOLD, C_GOLD, 3.0, 1.0, 0.06)
m_violet = mat("Violet", (0.2,0,0.4,1), (0.2,0,0.4,1), 4.0, 0.5, 0.15)
m_red = mat("Red", C_RED, C_RED, 15.0, 0, 0.0)
m_black = mat("Black", (0,0,0,1), (0,0,0,1), 0, 0, 0.5)

# --- HELIX PARAMETERS ---
def helix(t, turns=2.8, base_radius=1.3, height=3.8):
    angle = t * turns * 2 * math.pi
    r = base_radius * (1.0 - 0.15 * t * t)
    x = r * math.cos(angle)
    y = r * math.sin(angle)
    z = t * height - height * 0.45
    return (x, y, z)

def body_rad(t):
    """Thickness: thin tail → thick body → thicker hood"""
    if t < 0.15:
        return 0.04 + 0.06 * (t / 0.15)
    elif t < 0.5:
        return 0.10 + 0.06 * ((t - 0.15) / 0.35)
    elif t < 0.75:
        return 0.16 + 0.06 * ((t - 0.5) / 0.25)
    else:
        return 0.22 + 0.05 * ((t - 0.75) / 0.25)

# --- BUILD BODY (mesh tube along helix) ---
SEGS, R_SEGS = 400, 14
verts, faces = [], []

for i in range(SEGS):
    t = i / (SEGS - 1)
    cx, cy, cz = helix(t)
    rad = body_rad(t)
    dt = 0.001
    if t + dt <= 1.0:
        nx, ny, nz = helix(t + dt)
    else:
        nx, ny, nz = helix(t - dt)
    tx, ty, tz = nx - cx, ny - cy, nz - cz
    tl = math.sqrt(tx*tx + ty*ty + tz*tz)
    if tl > 1e-8:
        tx, ty, tz = tx/tl, ty/tl, tz/tl
    else:
        tx, ty, tz = 0, 0, 1
    if abs(tz) < 0.9:
        bx, by, bz = -ty, tx, 0
    else:
        bx, by, bz = 1, 0, 0
    bl = math.sqrt(bx*bx + by*by + bz*bz)
    bx, by, bz = bx/bl, by/bl, bz/bl
    cx2 = ty*bz - tz*by
    cy2 = tz*bx - tx*bz
    cz2 = tx*by - ty*bx
    for j in range(R_SEGS):
        a = j / R_SEGS * 2 * math.pi
        px = cx + rad * (bx * math.cos(a) + cx2 * math.sin(a))
        py = cy + rad * (by * math.cos(a) + cy2 * math.sin(a))
        pz = cz + rad * (bz * math.cos(a) + cz2 * math.sin(a))
        verts.append((px, py, pz))

for i in range(SEGS - 1):
    for j in range(R_SEGS):
        jn = (j + 1) % R_SEGS
        faces.append((i*R_SEGS+j, i*R_SEGS+jn, (i+1)*R_SEGS+jn, (i+1)*R_SEGS+j))

mesh = bpy.data.meshes.new("Body")
mesh.from_pydata(verts, [], faces)
mesh.update()
body_obj = bpy.data.objects.new("Body", mesh)
bpy.context.collection.objects.link(body_obj)
body_obj.data.materials.append(m_body)
bpy.ops.object.select_all(action='DESELECT')
body_obj.select_set(True)
bpy.context.view_layer.objects.active = body_obj
bpy.ops.object.shade_smooth()

hx, hy, hz = helix(0.98)
ha = 0.98 * 2.8 * 2 * math.pi

# --- HEAD ---
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.28, segments=20, ring_count=12)
head = bpy.context.active_object
head.scale = (0.8, 1.3, 0.65)
head.location = (hx, hy, hz + 0.1)
bpy.ops.object.transform_apply(scale=True)
head.data.materials.append(m_body)
bpy.ops.object.shade_smooth()

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.14, segments=14, ring_count=8)
snout = bpy.context.active_object
snout.scale = (0.5, 1.1, 0.45)
snout.location = (hx + 0.25 * math.cos(ha), hy + 0.25 * math.sin(ha), hz + 0.08)
bpy.ops.object.transform_apply(scale=True)
snout.data.materials.append(m_body)
bpy.ops.object.shade_smooth()

# --- EYES (red, with slit pupils) ---
for s, side in enumerate([-1, 1]):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, segments=14, ring_count=8)
    eye = bpy.context.active_object
    eye.scale = (0.4, 0.9, 0.55)
    eye.location = (
        hx + 0.22 * math.cos(ha) + side * 0.12 * math.sin(ha),
        hy + 0.22 * math.sin(ha) - side * 0.12 * math.cos(ha),
        hz + 0.18
    )
    bpy.ops.object.transform_apply(scale=True)
    eye.data.materials.append(m_red)
    bpy.ops.object.shade_smooth()
    
    bpy.ops.mesh.primitive_cube_add(size=0.018)
    pupil = bpy.context.active_object
    pupil.scale = (0.2, 0.6, 2.5)
    pupil.location = (eye.location[0] + 0.05 * math.cos(ha),
                      eye.location[1] + 0.05 * math.sin(ha),
                      eye.location[2])
    bpy.ops.object.transform_apply(scale=True)
    pupil.data.materials.append(m_black)

# --- CROWN (gold with spikes + gems) ---
crown_z = hz + 0.5

bpy.ops.mesh.primitive_torus_add(major_radius=0.22, minor_radius=0.016, major_segments=48, minor_segments=10)
band = bpy.context.active_object
band.location = (hx, hy, crown_z)
band.rotation_euler = (math.radians(-5), 0, 0)
band.data.materials.append(m_gold)

spikes = [
    (0, 0.85, True), (0.35, 0.6, True), (-0.35, 0.6, True),
    (0.7, 0.42, False), (-0.7, 0.42, False),
    (1.05, 0.3, False), (-1.05, 0.3, False),
    (1.4, 0.2, False), (-1.4, 0.2, False),
]

for i, (ao, h, is_gold) in enumerate(spikes):
    bpy.ops.mesh.primitive_cone_add(
        radius1=0.04 if is_gold else 0.028, radius2=0.003, depth=h, vertices=6
    )
    spk = bpy.context.active_object
    spk.location = (hx + 0.18 * math.sin(ao), hy + 0.18 * math.cos(ao), crown_z + h/2 + 0.01)
    tilt = math.radians(10)
    spk.rotation_euler = (tilt * math.cos(ao), tilt * math.sin(ao), ao)
    spk.data.materials.append(m_gold if is_gold else m_violet)

bpy.ops.mesh.primitive_ico_sphere_add(radius=0.04, subdivisions=3)
gem = bpy.context.active_object
gem.location = (hx, hy, crown_z + 0.88)
gem.data.materials.append(m_green)

# --- WIREFRAME RINGS ---
for i, gt in enumerate([0.2, 0.4, 0.6, 0.8]):
    gx, gy, gz = helix(gt)
    r = body_rad(gt) * 2.0
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.004, major_segments=32, minor_segments=6)
    ring = bpy.context.active_object
    ring.location = (gx, gy, gz)
    ring.rotation_euler = (gt * 1.5, gt * 5, i * 0.5)
    ring.data.materials.append(m_wire)

# Data fragments
random.seed(77)
for i in range(30):
    gt = random.choice([0.2, 0.4, 0.6, 0.8, 0.9]) + random.uniform(-0.06, 0.06)
    gx, gy, gz = helix(gt)
    gx += random.uniform(-0.6, 0.6)
    gy += random.uniform(-0.6, 0.6)
    gz += random.uniform(-0.15, 0.15)
    s = random.uniform(0.008, 0.028)
    if random.random() > 0.5:
        bpy.ops.mesh.primitive_cube_add(size=s)
    else:
        bpy.ops.mesh.primitive_ico_sphere_add(radius=s, subdivisions=1)
    frag = bpy.context.active_object
    frag.location = (gx, gy, gz)
    frag.rotation_euler = (random.uniform(0,6.28), random.uniform(0,6.28), random.uniform(0,6.28))
    frag.data.materials.append(random.choice([m_wire, m_green, m_violet]))

# Dissolving tail
for i in range(25):
    t = i / 25
    tx, ty, tz = helix(max(0, -t * 0.05))
    tz -= t * 2.2
    tx += 0.2 * t * math.cos(t * 2)
    ty += 0.2 * t * math.sin(t * 2)
    sz = body_rad(0) * (1.0 - t * 0.9)
    if i % 3 == 0:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=max(sz, 0.006))
    elif i % 3 == 1:
        bpy.ops.mesh.primitive_cube_add(size=max(sz, 0.008))
    else:
        bpy.ops.mesh.primitive_ico_sphere_add(radius=max(sz * 0.7, 0.005), subdivisions=1)
    seg = bpy.context.active_object
    seg.location = (tx, ty, tz)
    seg.rotation_euler = (t * 3, t * 4, t * 2)
    seg.data.materials.append([m_body, m_violet, m_wire][min(int(t * 3), 2)])

# --- ENVIRONMENT ---
world = bpy.data.worlds.new("Void")
scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0, 0.001, 0.005, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.015

# Key: blue-white
bpy.ops.object.light_add(type='AREA', location=(4, -3, 5))
key = bpy.context.active_object
key.data.energy = 300
key.data.color = (0.5, 0.6, 1.0)
key.data.size = 5

# Rim: purple from behind
bpy.ops.object.light_add(type='SPOT', location=(-4, 4, 1))
rim = bpy.context.active_object
rim.data.energy = 400
rim.data.color = (0.4, 0.05, 0.8)
rim.data.spot_size = math.radians(55)

# Fill: dim warm
bpy.ops.object.light_add(type='AREA', location=(-2, 1, 0))
fill = bpy.context.active_object
fill.data.energy = 25
fill.data.color = (0.6, 0.4, 0.25)
fill.data.size = 3

# Under-glow: subtle green
bpy.ops.object.light_add(type='AREA', location=(0, 0, -3))
under = bpy.context.active_object
under.data.energy = 20
under.data.color = C_GREEN[:3]
under.data.size = 4

# Eye point lights
for s, side in enumerate([-1, 1]):
    bpy.ops.object.light_add(type='POINT', location=(
        hx + 0.24 * math.cos(ha) + side * 0.12 * math.sin(ha),
        hy + 0.24 * math.sin(ha) - side * 0.12 * math.cos(ha),
        hz + 0.18
    ))
    el = bpy.context.active_object
    el.data.energy = 8
    el.data.color = C_RED[:3]

# Camera
bpy.ops.object.camera_add(location=(4.5, -5, 2.5))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(75), 0, math.radians(42))
cam.data.lens = 60
scene.camera = cam

# --- RENDER ---
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 150
scene.cycles.use_denoising = False
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.filepath = '/tmp/narusya_avatar.png'

# Bloom (keep threshold HIGH to avoid blowout)
scene.use_nodes = True
tree = scene.node_tree
for n in tree.nodes:
    tree.nodes.remove(n)
rl = tree.nodes.new('CompositorNodeRLayers')
glare = tree.nodes.new('CompositorNodeGlare')
glare.glare_type = 'FOG_GLOW'
glare.quality = 'HIGH'
glare.threshold = 0.65
glare.size = 6
out = tree.nodes.new('CompositorNodeComposite')
tree.links.new(rl.outputs['Image'], glare.inputs['Image'])
tree.links.new(glare.outputs['Image'], out.inputs['Image'])

bpy.ops.render.render(write_still=True)
print("=== NARUSYA RENDERED ===")
