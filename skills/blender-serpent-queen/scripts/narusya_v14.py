import bpy
import math
import random

# ============================================================
# NARUSYA v12 — HEAD PORTRAIT (close-up)
# Just the head/face/crown, camera RIGHT in front
# Big eyes, clear snout, visible scales, gold crown
# ============================================================

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

C_BODY      = (0.03, 0.008, 0.06, 1.0)
C_SCALE_HI  = (0.08, 0.02, 0.14, 1.0)
C_SCALE_EDGE = (0.25, 0.0, 0.5, 1.0)
C_GREEN     = (0.0, 0.85, 0.3, 1.0)
C_GOLD      = (1.0, 0.85, 0.15, 1.0)
C_RED       = (1.0, 0.03, 0.06, 1.0)
C_VIOLET    = (0.3, 0.0, 0.6, 1.0)

def simple_mat(name, base, emit, emit_str, metal=0, rough=0.4):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes['Principled BSDF']
    n.inputs['Base Color'].default_value = base
    n.inputs['Emission Color'].default_value = emit
    n.inputs['Emission Strength'].default_value = emit_str
    n.inputs['Metallic'].default_value = metal
    n.inputs['Roughness'].default_value = rough
    return m

# --- SCALE MATERIAL ---
def make_scale_mat():
    m = bpy.data.materials.new("Scales")
    m.use_nodes = True
    nodes = m.node_tree.nodes
    links = m.node_tree.links
    for n in nodes:
        nodes.remove(n)
    
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (800, 0)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (500, 0)
    bsdf.inputs['Metallic'].default_value = 0.75
    bsdf.inputs['Roughness'].default_value = 0.2
    
    tex = nodes.new('ShaderNodeTexCoord')
    tex.location = (-600, 0)
    mapping = nodes.new('ShaderNodeMapping')
    mapping.location = (-400, 0)
    mapping.inputs['Scale'].default_value = (4, 3, 2)  # BIG scales
    
    wave1 = nodes.new('ShaderNodeTexWave')
    wave1.location = (-150, 150)
    wave1.wave_type = 'BANDS'
    wave1.bands_direction = 'Y'
    wave1.inputs['Scale'].default_value = 3.0
    wave1.inputs['Distortion'].default_value = 5.0
    wave1.inputs['Detail'].default_value = 2.0
    
    wave2 = nodes.new('ShaderNodeTexWave')
    wave2.location = (-150, -150)
    wave2.wave_type = 'BANDS'
    wave2.bands_direction = 'DIAGONAL'
    wave2.inputs['Scale'].default_value = 3.5
    wave2.inputs['Distortion'].default_value = 4.0
    wave2.inputs['Detail'].default_value = 2.0
    
    mult = nodes.new('ShaderNodeMath')
    mult.location = (100, 0)
    mult.operation = 'MULTIPLY'
    
    links.new(tex.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], wave1.inputs['Vector'])
    links.new(mapping.outputs['Vector'], wave2.inputs['Vector'])
    links.new(wave1.outputs['Color'], mult.inputs[0])
    links.new(wave2.outputs['Color'], mult.inputs[1])
    
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (300, 0)
    ramp.color_ramp.elements[0].color = C_BODY
    ramp.color_ramp.elements[1].color = C_SCALE_HI
    elem = ramp.color_ramp.elements.new(0.8)
    elem.color = C_SCALE_EDGE
    links.new(mult.outputs['Value'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    
    bump = nodes.new('ShaderNodeBump')
    bump.location = (300, -300)
    bump.inputs['Strength'].default_value = 0.5
    links.new(mult.outputs['Value'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return m

m_body = make_scale_mat()
m_gold = simple_mat("Gold", C_GOLD, C_GOLD, 0.5, 1.0, 0.08)  # LOW emit
m_red = simple_mat("Red", C_RED, C_RED, 8.0, 0, 0.0)  # Moderate
m_black = simple_mat("Black", (0,0,0,1), (0,0,0,1), 0, 0, 0.5)
m_green = simple_mat("Green", C_GREEN, C_GREEN, 5.0, 0, 0.05)
m_violet = simple_mat("Violet", C_VIOLET, C_VIOLET, 2.0, 0.5, 0.2)
m_catch = simple_mat("Catch", (1,1,1,1), (1,1,1,1), 40.0, 0, 0.0)
m_white = simple_mat("White", (0.8,0.8,0.8,1), (0.8,0.8,0.8,1), 3.0, 0, 0.3)

# --- HEAD (at origin, facing camera) ---
print("Building head...")

# Neck/body stub (coiled behind)
for i in range(8):
    t = i / 8
    angle = t * 1.2 * math.pi
    r = 0.8 - t * 0.2
    z = -0.5 - t * 1.5
    rad = 0.18 + t * 0.05
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=rad, segments=16, ring_count=10)
    seg = bpy.context.active_object
    seg.name = f"Neck_{i}"
    seg.location = (r * math.cos(angle), r * math.sin(angle), z)
    seg.data.materials.append(m_body)
    bpy.ops.object.shade_smooth()

# Main head
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, segments=24, ring_count=16)
head = bpy.context.active_object
head.name = "Head"
head.scale = (0.7, 1.3, 0.55)  # Elongated
head.location = (0, 0, 0)
bpy.ops.object.transform_apply(scale=True)
head.data.materials.append(m_body)
bpy.ops.object.shade_smooth()

# Snout (longer, pointed forward toward camera)
bpy.ops.mesh.primitive_cone_add(radius1=0.12, radius2=0.01, depth=0.6, vertices=16)
snout = bpy.context.active_object
snout.name = "Snout"
snout.location = (0.45, 0, -0.03)
snout.rotation_euler = (0, math.radians(90), 0)  # Point toward camera (+X)
snout.data.materials.append(m_body)
bpy.ops.object.shade_smooth()

# Upper jaw ridge
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.08, segments=12, ring_count=6)
jaw_ridge = bpy.context.active_object
jaw_ridge.name = "JawRidge"
jaw_ridge.scale = (1.5, 0.6, 0.4)
jaw_ridge.location = (0.3, 0, 0.02)
bpy.ops.object.transform_apply(scale=True)
jaw_ridge.data.materials.append(m_body)
bpy.ops.object.shade_smooth()

# Lower jaw
bpy.ops.mesh.primitive_cone_add(radius1=0.07, radius2=0.02, depth=0.3, vertices=10)
jaw = bpy.context.active_object
jaw.name = "Jaw"
jaw.location = (0.3, 0, -0.12)
jaw.rotation_euler = (0, math.radians(80), 0)
jaw.data.materials.append(m_body)
bpy.ops.object.shade_smooth()

# --- EYES (BIG, prominent) ---
print("Building eyes...")
for s, side in enumerate([-1, 1]):
    # Brow ridge
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, segments=12, ring_count=6)
    brow = bpy.context.active_object
    brow.name = f"Brow_{s}"
    brow.scale = (0.7, 0.5, 0.4)
    brow.location = (0.15, side * 0.15, 0.12)
    bpy.ops.object.transform_apply(scale=True)
    brow.data.materials.append(m_body)
    bpy.ops.object.shade_smooth()
    
    # Eye socket (dark recess)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, segments=10, ring_count=6)
    socket = bpy.context.active_object
    socket.name = f"Socket_{s}"
    socket.scale = (0.5, 0.85, 0.55)
    socket.location = (0.2, side * 0.16, 0.1)
    bpy.ops.object.transform_apply(scale=True)
    socket.data.materials.append(m_black)
    bpy.ops.object.shade_smooth()
    
    # Eye orb (RED, glowing) — BIGGER
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.065, segments=12, ring_count=8)
    eye = bpy.context.active_object
    eye.name = f"Eye_{s}"
    eye.scale = (0.4, 0.85, 0.55)
    eye.location = (0.23, side * 0.165, 0.1)
    bpy.ops.object.transform_apply(scale=True)
    eye.data.materials.append(m_red)
    bpy.ops.object.shade_smooth()
    
    # Iris ring (darker ring around pupil)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.04, minor_radius=0.008, major_segments=20, minor_segments=6)
    iris = bpy.context.active_object
    iris.name = f"Iris_{s}"
    iris.location = (0.26, side * 0.17, 0.1)
    iris.rotation_euler = (0, math.radians(90), 0)
    iris.data.materials.append(m_black)
    
    # Pupil slit (vertical)
    bpy.ops.mesh.primitive_cube_add(size=0.012)
    pupil = bpy.context.active_object
    pupil.name = f"Pupil_{s}"
    pupil.scale = (0.2, 0.4, 2.5)
    pupil.location = (0.27, side * 0.17, 0.1)
    bpy.ops.object.transform_apply(scale=True)
    pupil.data.materials.append(m_black)
    
    # Catchlight (two dots for life)
    for ci, (cx_off, cz_off) in enumerate([(0.015, 0.02), (0.01, -0.015)]):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.01, segments=6, ring_count=4)
        catch = bpy.context.active_object
        catch.name = f"Catch_{s}_{ci}"
        catch.location = (0.25 + cx_off, side * 0.168, 0.1 + cz_off)
        catch.data.materials.append(m_catch)

# --- COBRA HOOD (behind head, flared) ---
print("Building hood...")
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, segments=24, ring_count=16)
hood = bpy.context.active_object
hood.name = "Hood"
hood.scale = (0.55, 0.28, 1.5)  # Slightly thicker for visibility
hood.location = (-0.25, 0, 0.15)
bpy.ops.object.transform_apply(scale=True)
hood.data.materials.append(m_body)
bpy.ops.object.shade_smooth()

# Hood edge pattern
for z_off in [0.25, -0.25, 0.0]:
    bpy.ops.mesh.primitive_torus_add(major_radius=0.4, minor_radius=0.008, major_segments=32, minor_segments=6)
    band = bpy.context.active_object
    band.name = f"HoodBand"
    band.location = (-0.25, 0, 0.15 + z_off)
    band.scale = (0.5, 0.25, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    band.data.materials.append(m_violet)

# --- CROWN (atop head) ---
print("Building crown...")
crown_z = 0.5

bpy.ops.mesh.primitive_torus_add(major_radius=0.22, minor_radius=0.018, major_segments=48, minor_segments=12)
band = bpy.context.active_object
band.name = "CrownBand"
band.location = (0, 0, crown_z)
band.rotation_euler = (math.radians(-5), 0, 0)
band.data.materials.append(m_gold)

spikes = [
    (0, 0.8, True), (0.35, 0.55, True), (-0.35, 0.55, True),
    (0.7, 0.35, False), (-0.7, 0.35, False),
    (1.05, 0.22, False), (-1.05, 0.22, False),
]

for i, (ao, h, is_gold) in enumerate(spikes):
    bpy.ops.mesh.primitive_cone_add(radius1=0.04 if is_gold else 0.028, radius2=0.003, depth=h, vertices=6)
    spk = bpy.context.active_object
    spk.name = f"Spk_{i}"
    spk.location = (0.18 * math.sin(ao), 0.18 * math.cos(ao), crown_z + h/2)
    spk.data.materials.append(m_gold if is_gold else m_violet)

# Gems
bpy.ops.mesh.primitive_ico_sphere_add(radius=0.04, subdivisions=3)
gem = bpy.context.active_object
gem.name = "Gem"
gem.location = (0, 0, crown_z + 0.83)
gem.data.materials.append(m_green)

for ao in [0.35, -0.35]:
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.025, subdivisions=2)
    sg = bpy.context.active_object
    sg.name = f"SGem"
    sg.location = (0.18 * math.sin(ao), 0.18 * math.cos(ao), crown_z + 0.57)
    sg.data.materials.append(m_violet)

# --- SCATTERED GREEN RINGS (in background) ---
for i, pos in enumerate([(-1.5, 0.5, -1.2), (-1.2, -0.8, -1.8), (-0.8, 1.0, -2.5)]):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.004, major_segments=24, minor_segments=6)
    ring = bpy.context.active_object
    ring.name = f"BGRing_{i}"
    ring.location = pos
    ring.rotation_euler = (random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1))
    ring.data.materials.append(simple_mat(f"BGRing_{i}", (0,0,0,1), C_GREEN, 4.0, 0, 0.0))


# --- BODY COIL behind head ---
print("Adding body coil...")
for i in range(15):
    t = i / 15
    angle = -0.3 - t * 2.0 * math.pi
    r = 0.6 + t * 0.4
    x = -0.3 - r * math.cos(angle) * 0.6
    y = r * math.sin(angle)
    z = -0.5 - t * 2.5
    rad = 0.15 + 0.04 * (1.0 - t)
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=rad, segments=14, ring_count=8)
    seg = bpy.context.active_object
    seg.name = f"Body_{i}"
    seg.location = (x, y, z)
    seg.data.materials.append(m_body)
    bpy.ops.object.shade_smooth()

# --- ENVIRONMENT ---
world = bpy.data.worlds.new("Void")
scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0, 0.001, 0.005, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.03

# KEY: from right, illuminating face
bpy.ops.object.light_add(type='AREA', location=(3, -1, 1.5))
key = bpy.context.active_object
key.data.energy = 400
key.data.color = (0.6, 0.65, 1.0)
key.data.size = 3

# FILL: from left, warm
bpy.ops.object.light_add(type='AREA', location=(-2, 1.5, 1))
fill = bpy.context.active_object
fill.data.energy = 200
fill.data.color = (0.7, 0.55, 0.4)
fill.data.size = 3

# RIM: behind hood, purple
bpy.ops.object.light_add(type='SPOT', location=(-2, 0, 1))
rim = bpy.context.active_object
rim.data.energy = 500
rim.data.color = (0.4, 0.08, 0.8)
rim.data.spot_size = math.radians(60)

# FACE FRONT: from camera direction
bpy.ops.object.light_add(type='AREA', location=(2.5, 0, 0.5))
front = bpy.context.active_object
front.data.energy = 300
front.data.color = (0.65, 0.6, 0.9)
front.data.size = 2

# Eye lights
for side in [-1, 1]:
    bpy.ops.object.light_add(type='POINT', location=(0.35, side * 0.2, 0.15))
    el = bpy.context.active_object
    el.data.energy = 5
    el.data.color = C_RED[:3]

# Crown light
bpy.ops.object.light_add(type='POINT', location=(0, 0, 1.0))
cl = bpy.context.active_object
cl.data.energy = 15
cl.data.color = C_GOLD[:3]

# Camera — CLOSE UP on face
bpy.ops.object.camera_add(location=(2.0, 0, 0.3))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(90), 0, math.radians(90))  # Looking at face
cam.data.lens = 85  # Telephoto for portrait
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = 2.0
cam.data.dof.aperture_fstop = 2.8
scene.camera = cam

# --- RENDER ---
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 200
scene.cycles.use_denoising = False
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.filepath = '/tmp/narusya_v14.png'

# Subtle bloom
scene.use_nodes = True
tree = scene.node_tree
for n in tree.nodes:
    tree.nodes.remove(n)
rl = tree.nodes.new('CompositorNodeRLayers')
glare = tree.nodes.new('CompositorNodeGlare')
glare.glare_type = 'FOG_GLOW'
glare.quality = 'HIGH'
glare.threshold = 0.6
glare.size = 5
out = tree.nodes.new('CompositorNodeComposite')
tree.links.new(rl.outputs['Image'], glare.inputs['Image'])
tree.links.new(glare.outputs['Image'], out.inputs['Image'])

print("Rendering v14 (v12 base + longer snout + body)...")
bpy.ops.render.render(write_still=True)
print("=== NARUSYA V14 COMPLETE ===")
