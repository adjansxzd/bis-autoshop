"""
Procedural 3D models of simple-shaped parts — made in code by our team, so no license is needed.

    BR-002.glb  ventilated, cross-drilled brake disc
    FL-001.glb  spin-on oil filter
    TR-003.glb  tire on an alloy wheel (225/65 R17)

Re-generate (developer tool, not needed to run the shop):
    pip install trimesh manifold3d
    python make_models.py        # run inside this folder
Units: metres, Y up (glTF). Colours are PBR materials (metal / rubber / paint).
"""
import numpy as np
import trimesh
from trimesh.creation import annulus, box, cylinder, revolve, torus
from trimesh.visual.material import PBRMaterial
from trimesh.visual import TextureVisuals

MM = 0.001

def mat(rgb, metal, rough):
    return PBRMaterial(baseColorFactor=[*rgb, 1.0], metallicFactor=metal, roughnessFactor=rough)

def paint(mesh, m):
    mesh.visual = TextureVisuals(material=m)
    return mesh

def zcyl(r, h, z0=0.0, sections=96):
    c = cylinder(radius=r, height=h, sections=sections)
    c.apply_translation([0, 0, z0 + h / 2]); return c

def zring(r_in, r_out, h, z0=0.0, sections=128):
    a = annulus(r_min=r_in, r_max=r_out, height=h, sections=sections)
    a.apply_translation([0, 0, z0 + h / 2]); return a

def to_y_up(scene_meshes):
    rot = trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0])
    for m in scene_meshes: m.apply_transform(rot)

def brake_disc():
    R_out, R_in, plate, gap = 150, 92, 9, 10
    steel = mat([0.62, 0.63, 0.65], 1.0, 0.38)
    hub_paint = mat([0.16, 0.17, 0.19], 0.6, 0.5)
    lower = zring(R_in, R_out, plate, 0)
    upper = zring(R_in, R_out, plate, plate + gap)
    vanes = []
    for k in range(36):  # cooling vanes between the plates
        v = box(extents=[R_out - R_in - 6, 4, gap + 0.2])
        v.apply_translation([(R_out + R_in) / 2, 0, plate + gap / 2])
        v.apply_transform(trimesh.transformations.rotation_matrix(2 * np.pi * k / 36, [0, 0, 1]))
        vanes.append(v)
    ring = trimesh.boolean.union([lower, upper] + vanes)
    # cross-drilled holes: 3 rows, 18 per row
    holes = []
    for row, r in enumerate([105, 120, 135]):
        for k in range(18):
            a = 2 * np.pi * (k + row / 3) / 18
            h = zcyl(3.2, 2 * plate + gap + 4, -2, sections=24)
            h.apply_translation([r * np.cos(a), r * np.sin(a), 0]); holes.append(h)
    ring = trimesh.boolean.difference([ring] + holes)
    # hat (hub) with centre bore and 5 wheel-bolt holes
    hat_wall = zring(78, 92, 40, 2 * plate + gap - 1)
    hat_top = zcyl(92, 7, 2 * plate + gap + 39)
    cut = [zcyl(34, 20, 2 * plate + gap + 33)]
    for k in range(5):
        a = 2 * np.pi * k / 5
        b = zcyl(7, 20, 2 * plate + gap + 33, sections=32); b.apply_translation([57 * np.cos(a), 57 * np.sin(a), 0]); cut.append(b)
    hat = trimesh.boolean.difference([trimesh.boolean.union([hat_wall, hat_top])] + cut)
    parts = [paint(ring, steel), paint(hat, hub_paint)]
    for p in parts: p.apply_scale(MM)
    to_y_up(parts)
    return parts

def oil_filter():
    can_paint = mat([0.08, 0.27, 0.55], 0.35, 0.35)
    steel = mat([0.70, 0.71, 0.73], 1.0, 0.3)
    rubber = mat([0.05, 0.05, 0.05], 0.0, 0.8)
    body = trimesh.boolean.union([zcyl(38, 84, 6), zcyl(34, 4, 90), torus(major_radius=34, minor_radius=4, major_sections=96, minor_sections=24).apply_translation([0, 0, 90])])
    # 16 grip flutes near the top
    flutes = []
    for k in range(16):
        f = box(extents=[3, 5, 18]); f.apply_translation([38.5, 0, 80]); f.apply_transform(trimesh.transformations.rotation_matrix(2 * np.pi * k / 16, [0, 0, 1])); flutes.append(f)
    body = trimesh.boolean.difference([body] + flutes)
    plate_cuts = [zcyl(10, 12, -2, sections=48)]
    for k in range(8):
        a = 2 * np.pi * k / 8
        c = zcyl(3.5, 12, -2, sections=24); c.apply_translation([21 * np.cos(a), 21 * np.sin(a), 0]); plate_cuts.append(c)
    plate = trimesh.boolean.difference([zcyl(36, 6, 0)] + plate_cuts)
    thread = zring(10, 12.5, 10, -3, sections=48)
    gasket = torus(major_radius=30, minor_radius=2.6, major_sections=96, minor_sections=24)
    gasket.apply_translation([0, 0, -0.5])
    parts = [paint(body, can_paint), paint(plate, steel), paint(thread, steel), paint(gasket, rubber)]
    for p in parts: p.apply_scale(MM)
    to_y_up(parts)
    return parts

def tire_wheel():
    rubber = mat([0.06, 0.06, 0.07], 0.0, 0.85)
    alloy = mat([0.78, 0.79, 0.81], 1.0, 0.25)
    dark = mat([0.25, 0.26, 0.28], 0.8, 0.4)
    # tire cross-section (r, z) in mm: 225/65 R17 → width 225, sidewall ~146, rim radius 216
    W, r_rim, r_out, c = 225, 216, 362, 22
    # rounded profile: bead → sidewall → shoulder → tread → shoulder → sidewall → bead
    pts = [[r_rim, -W/2 + 14], [r_rim + 40, -W/2 + 2], [r_out - c, -W/2]]
    for a in np.linspace(-np.pi/2, 0, 8): pts.append([r_out - c + c*np.cos(a), -W/2 + c + c*np.sin(a)])
    for a in np.linspace(0, np.pi/2, 8): pts.append([r_out - c + c*np.cos(a), W/2 - c + c*np.sin(a)])
    pts += [[r_out - c, W/2], [r_rim + 40, W/2 - 2], [r_rim, W/2 - 14]]
    pts.append(pts[0])
    tire = revolve(np.array(pts), sections=128)   # around Z
    if not tire.is_volume:
        tire = revolve(np.array(pts[::-1]), sections=128)
    # tread: 3 circumferential grooves + 64 lateral sipes
    cuts = []
    for z in (-55, 0, 55):
        g = annulus(r_min=r_out - 9, r_max=r_out + 5, height=12, sections=128); g.apply_translation([0, 0, z]); cuts.append(g)
    for k in range(64):
        s = box(extents=[20, 5, W * 0.8]); s.apply_translation([r_out, 0, 0])
        s.apply_transform(trimesh.transformations.rotation_matrix(2*np.pi*k/64 + 0.15, [0, 0, 1]))
        s.apply_transform(trimesh.transformations.rotation_matrix(0.25, [np.cos(2*np.pi*k/64), np.sin(2*np.pi*k/64), 0]))
        cuts.append(s)
    tire = trimesh.boolean.difference([tire] + cuts)
    # rim: barrel + front face with 5 double spokes
    barrel = annulus(r_min=r_rim - 12, r_max=r_rim + 4, height=W - 20, sections=128)
    lip = annulus(r_min=r_rim - 6, r_max=r_rim + 14, height=10, sections=128); lip.apply_translation([0, 0, W/2 - 14])
    hub = cylinder(radius=70, height=30, sections=64); hub.apply_translation([0, 0, W/2 - 30])
    spokes = []
    for k in range(10):
        a = 2*np.pi*(k//2)/5 + (0.13 if k % 2 else -0.13)
        sp = box(extents=[r_rim - 75, 22, 18]); sp.apply_translation([(r_rim + 60)/2, 0, W/2 - 26])
        sp.apply_transform(trimesh.transformations.rotation_matrix(a, [0, 0, 1])); spokes.append(sp)
    rim = trimesh.boolean.union([barrel, lip, hub] + spokes)
    holes = [cylinder(radius=8, height=40, sections=24).apply_translation([45*np.cos(2*np.pi*k/5), 45*np.sin(2*np.pi*k/5), W/2 - 25]) for k in range(5)]
    rim = trimesh.boolean.difference([rim] + holes)
    cap = cylinder(radius=28, height=8, sections=48); cap.apply_translation([0, 0, W/2 - 10])
    parts = [paint(tire, rubber), paint(rim, alloy), paint(cap, dark)]
    for p in parts: p.apply_scale(MM)
    # axle along Z = the wheel stands upright in glTF (Y up), spoke face towards the viewer
    return parts

for name, fn in [("BR-002", brake_disc), ("FL-001", oil_filter), ("TR-003", tire_wheel)]:
    parts = fn()
    scene = trimesh.Scene()
    for i, p in enumerate(parts): scene.add_geometry(p, node_name=f"{name}-{i}")
    data = scene.export(file_type="glb")
    open(f"{name}.glb", "wb").write(data)
    print(name, len(data), [len(p.faces) for p in parts], [p.is_watertight for p in parts])
