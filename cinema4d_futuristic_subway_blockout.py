"""
Cinema 4D Python blockout generator

Creates a rough futuristic white subway / escalator interior based on the
provided reference image. The scene is intentionally simple, symmetrical,
editable, and made from named primitives.

Run this from Cinema 4D's Script Manager.
"""

import math

import c4d
from c4d import Vector


ROOT_NAME = "AUTO_FUTURISTIC_SUBWAY_BLOCKOUT"


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def deg(value):
    """Convert degrees to radians for Cinema 4D rotations."""
    return math.radians(value)


def set_if_exists(node, constant_name, value):
    """Safely assign a C4D parameter only when the running C4D version has it."""
    if hasattr(c4d, constant_name):
        node[getattr(c4d, constant_name)] = value


def remove_previous_blockout(doc):
    """Remove only this generated blockout, leaving unrelated scene work alone."""
    old_root = doc.SearchObject(ROOT_NAME)
    if old_root:
        old_root.Remove()

    mat = doc.GetFirstMaterial()
    while mat:
        next_mat = mat.GetNext()
        if mat.GetName().startswith("BLK_"):
            mat.Remove()
        mat = next_mat


def make_material(doc, name, color, luminance=False, transparent=False, metallic=False):
    """Create a simple viewport/render material for blockout readability."""
    mat = c4d.BaseMaterial(c4d.Mmaterial)
    mat.SetName("BLK_" + name)
    mat[c4d.MATERIAL_COLOR_COLOR] = Vector(color[0], color[1], color[2])

    if luminance:
        set_if_exists(mat, "MATERIAL_USE_LUMINANCE", True)
        set_if_exists(mat, "MATERIAL_LUMINANCE_COLOR", Vector(color[0], color[1], color[2]))
        set_if_exists(mat, "MATERIAL_LUMINANCE_BRIGHTNESS", 1.8)

    if transparent:
        set_if_exists(mat, "MATERIAL_USE_TRANSPARENCY", True)
        set_if_exists(mat, "MATERIAL_TRANSPARENCY_COLOR", Vector(color[0], color[1], color[2]))
        set_if_exists(mat, "MATERIAL_TRANSPARENCY_BRIGHTNESS", 0.45)

    if metallic:
        set_if_exists(mat, "MATERIAL_USE_REFLECTION", True)
        set_if_exists(mat, "MATERIAL_REFLECTION_BRIGHTNESS", 0.35)
        set_if_exists(mat, "MATERIAL_SPECULAR_WIDTH", 0.18)
        set_if_exists(mat, "MATERIAL_SPECULAR_HEIGHT", 0.75)

    mat.Update(True, True)
    doc.InsertMaterial(mat)
    return mat


def assign_material(obj, mat):
    """Assign a material tag and matching viewport color."""
    if not mat:
        return

    tag = c4d.BaseTag(c4d.Ttexture)
    tag[c4d.TEXTURETAG_MATERIAL] = mat
    obj.InsertTag(tag)

    obj[c4d.ID_BASEOBJECT_USECOLOR] = c4d.ID_BASEOBJECT_USECOLOR_ALWAYS
    obj[c4d.ID_BASEOBJECT_COLOR] = mat[c4d.MATERIAL_COLOR_COLOR]


def insert_object(doc, obj, parent=None):
    """Insert an object into the document or below a parent null."""
    if parent:
        doc.InsertObject(obj, parent)
    else:
        doc.InsertObject(obj)
    return obj


def make_null(doc, name, parent=None):
    obj = c4d.BaseObject(c4d.Onull)
    obj.SetName(name)
    return insert_object(doc, obj, parent)


def make_box(doc, name, pos, size, mat=None, rot=Vector(0, 0, 0), parent=None):
    """Create a named cube scaled to a given rectangular size."""
    obj = c4d.BaseObject(c4d.Ocube)
    obj.SetName(name)
    obj[c4d.PRIM_CUBE_LEN] = Vector(size[0], size[1], size[2])
    obj.SetAbsPos(Vector(pos[0], pos[1], pos[2]))
    obj.SetAbsRot(rot)
    assign_material(obj, mat)
    return insert_object(doc, obj, parent)


def make_cylinder(doc, name, pos, radius, height, mat=None, rot=Vector(0, 0, 0), parent=None, segments=24):
    """Create a named cylinder, useful for simple metallic rails."""
    obj = c4d.BaseObject(c4d.Ocylinder)
    obj.SetName(name)
    obj[c4d.PRIM_CYLINDER_RADIUS] = radius
    obj[c4d.PRIM_CYLINDER_HEIGHT] = height
    set_if_exists(obj, "PRIM_CYLINDER_SEG", segments)
    obj.SetAbsPos(Vector(pos[0], pos[1], pos[2]))
    obj.SetAbsRot(rot)
    assign_material(obj, mat)
    return insert_object(doc, obj, parent)


def make_torus(doc, name, pos, outer_radius, tube_radius, mat=None,
               rot=Vector(0, 0, 0), scale=Vector(1, 1, 1), parent=None):
    """Create a torus ring for the large oval architectural opening."""
    obj = c4d.BaseObject(c4d.Otorus)
    obj.SetName(name)
    set_if_exists(obj, "PRIM_TORUS_OUTERRAD", outer_radius)
    set_if_exists(obj, "PRIM_TORUS_INNERRAD", tube_radius)
    set_if_exists(obj, "PRIM_TORUS_SUB", 96)
    set_if_exists(obj, "PRIM_TORUS_CSUB", 12)
    obj.SetAbsPos(Vector(pos[0], pos[1], pos[2]))
    obj.SetAbsRot(rot)
    obj.SetAbsScale(scale)
    assign_material(obj, mat)
    return insert_object(doc, obj, parent)


def look_at(obj, target):
    """Aim an object so its forward axis points at a target position."""
    direction = Vector(target[0], target[1], target[2]) - obj.GetAbsPos()
    obj.SetAbsRot(c4d.utils.VectorToHPB(direction))


# ---------------------------------------------------------------------------
# Architectural sections
# ---------------------------------------------------------------------------

def build_floor_and_path(doc, root, mats):
    """Create the long low-angle corridor floor and central path."""
    floor = make_box(
        doc,
        "FLOOR",
        pos=(0, -12, 3200),
        size=(3900, 24, 9200),
        mat=mats["white"],
        parent=root,
    )

    central_path = make_box(
        doc,
        "CENTRAL_PATH",
        pos=(0, 8, 3250),
        size=(900, 18, 7700),
        mat=mats["path"],
        parent=root,
    )

    # Fine floor tile seams: light gray lines to preserve the clean blockout.
    tile_group = make_null(doc, "FLOOR_TILE_SEAMS", root)
    for x in range(-1600, 1800, 400):
        make_box(doc, "floor_longitudinal_seam", (x, 23, 3200), (6, 4, 8500), mats["seam"], parent=tile_group)
    for z in range(-700, 7600, 700):
        make_box(doc, "floor_cross_seam", (0, 24, z), (3650, 4, 6), mats["seam"], parent=tile_group)

    # Dark linear trims echo the black base strips in the reference.
    make_box(doc, "LEFT_FLOOR_TRIM", (-1050, 28, 3250), (34, 16, 7600), mats["dark"], parent=root)
    make_box(doc, "RIGHT_FLOOR_TRIM", (1050, 28, 3250), (34, 16, 7600), mats["dark"], parent=root)

    return floor, central_path


def build_walls(doc, root, mats):
    """Create smooth white side walls with light bands and base trim."""
    wall_rot_left = Vector(0, 0, deg(-5))
    wall_rot_right = Vector(0, 0, deg(5))

    left_wall = make_box(
        doc,
        "LEFT_WALL",
        pos=(-1820, 385, 3200),
        size=(95, 830, 9200),
        rot=wall_rot_left,
        mat=mats["white"],
        parent=root,
    )
    right_wall = make_box(
        doc,
        "RIGHT_WALL",
        pos=(1820, 385, 3200),
        size=(95, 830, 9200),
        rot=wall_rot_right,
        mat=mats["white"],
        parent=root,
    )

    detail_group = make_null(doc, "WALL_LIGHTS_AND_PANEL_LINES", root)

    make_box(doc, "LEFT_WALL_LIGHT_STRIP", (-1710, 540, 3200), (26, 38, 8500), mats["light"], rot=wall_rot_left, parent=detail_group)
    make_box(doc, "RIGHT_WALL_LIGHT_STRIP", (1710, 540, 3200), (26, 38, 8500), mats["light"], rot=wall_rot_right, parent=detail_group)
    make_box(doc, "LEFT_BLACK_BASE_STRIP", (-1730, 80, 3200), (30, 45, 8500), mats["dark"], rot=wall_rot_left, parent=detail_group)
    make_box(doc, "RIGHT_BLACK_BASE_STRIP", (1730, 80, 3200), (30, 45, 8500), mats["dark"], rot=wall_rot_right, parent=detail_group)

    # Sparse panel seams suggest the white tiled subway shell without detailed modeling.
    for z in range(-500, 7600, 900):
        make_box(doc, "left_wall_vertical_panel_seam", (-1700, 385, z), (10, 720, 6), mats["seam"], rot=wall_rot_left, parent=detail_group)
        make_box(doc, "right_wall_vertical_panel_seam", (1700, 385, z), (10, 720, 6), mats["seam"], rot=wall_rot_right, parent=detail_group)

    return left_wall, right_wall


def build_architecture_rings(doc, root, mats):
    """Create the large oval opening and secondary curved architectural bands."""
    # Main circular/oval opening: a vertical torus scaled wide, positioned ahead.
    main_arch = make_torus(
        doc,
        "MAIN_ARCH",
        pos=(0, 820, 2350),
        outer_radius=1080,
        tube_radius=135,
        rot=Vector(0, deg(90), 0),
        scale=Vector(1.45, 1.0, 0.82),
        mat=mats["white"],
        parent=root,
    )

    # Thin inner metallic trace to read as a machined edge.
    make_torus(
        doc,
        "MAIN_ARCH_INNER_METAL_EDGE",
        pos=(0, 820, 2365),
        outer_radius=900,
        tube_radius=18,
        rot=Vector(0, deg(90), 0),
        scale=Vector(1.45, 1.0, 0.82),
        mat=mats["metal"],
        parent=root,
    )

    # Background oval rings add the layered futuristic station depth.
    make_torus(
        doc,
        "UPPER_BACKGROUND_OVAL_PATH",
        pos=(0, 1180, 4550),
        outer_radius=980,
        tube_radius=58,
        rot=Vector(0, deg(90), 0),
        scale=Vector(1.8, 1.0, 0.55),
        mat=mats["white"],
        parent=root,
    )
    make_torus(
        doc,
        "RIGHT_REAR_OVAL_OPENING",
        pos=(980, 730, 5650),
        outer_radius=560,
        tube_radius=48,
        rot=Vector(0, deg(90), deg(-6)),
        scale=Vector(1.25, 1.0, 0.72),
        mat=mats["white"],
        parent=root,
    )

    return main_arch


def ramp_midpoint(start, end):
    return (
        (start[0] + end[0]) * 0.5,
        (start[1] + end[1]) * 0.5,
        (start[2] + end[2]) * 0.5,
    )


def ramp_length_and_pitch(start, end):
    dz = end[2] - start[2]
    dy = end[1] - start[1]
    length = math.sqrt(dz * dz + dy * dy)
    pitch = -math.atan2(dy, dz)
    return length, pitch


def make_ramp_box(doc, name, start, end, x_offset, y_offset, size_x, size_y, mat, parent):
    """Create a box aligned between two z/y points for escalator pieces."""
    length, pitch = ramp_length_and_pitch(start, end)
    mid = ramp_midpoint(start, end)
    pos = (mid[0] + x_offset, mid[1] + y_offset, mid[2])
    return make_box(
        doc,
        name,
        pos=pos,
        size=(size_x, size_y, length),
        rot=Vector(0, pitch, 0),
        mat=mat,
        parent=parent,
    )


def build_escalator(doc, root, mats, name, x, start_z, end_z, end_y, width):
    """Build one simple escalator-like ramp with belt, treads, sides, and rails."""
    group = make_null(doc, name, root)

    start = (x, 55, start_z)
    end = (x, end_y, end_z)

    make_ramp_box(doc, name + "_SILVER_BODY", start, end, 0, 8, width + 170, 64, mats["metal_light"], group)
    make_ramp_box(doc, name + "_DARK_MOVING_STEPS", start, end, 0, 52, width - 90, 28, mats["dark"], group)

    # Simplified escalator treads as repeated transverse bars.
    tread_count = 22
    dz = end[2] - start[2]
    dy = end[1] - start[1]
    _, pitch = ramp_length_and_pitch(start, end)
    for i in range(tread_count):
        t = (i + 0.5) / float(tread_count)
        z = start[2] + dz * t
        y = start[1] + dy * t + 73
        make_box(
            doc,
            name + "_TREAD_%02d" % (i + 1),
            pos=(x, y, z),
            size=(width - 110, 10, 26),
            rot=Vector(0, pitch, 0),
            mat=mats["step_line"],
            parent=group,
        )

    # Yellow safety plates at the top and bottom, matching escalator language.
    make_box(doc, name + "_BOTTOM_YELLOW_PLATE", (x, start[1] + 58, start[2] + 95), (width - 80, 12, 60), mats["yellow"], rot=Vector(0, pitch, 0), parent=group)
    make_box(doc, name + "_TOP_YELLOW_PLATE", (x, end[1] + 16, end[2] - 95), (width - 80, 12, 60), mats["yellow"], rot=Vector(0, pitch, 0), parent=group)

    # Glass-like balustrades plus metallic rails on both sides.
    for side, side_x in (("L", -1), ("R", 1)):
        rail_x = side_x * (width * 0.5 + 62)
        make_ramp_box(doc, name + "_GLASS_BALUSTRADE_" + side, start, end, rail_x, 126, 24, 165, mats["glass"], group)
        make_ramp_box(doc, name + "_CHROME_HANDRAIL_" + side, start, end, rail_x, 224, 34, 28, mats["metal"], group)

    # Entry newel blocks at the foot of each escalator.
    make_box(doc, name + "_BOTTOM_LEFT_NEWEL", (x - width * 0.5 - 90, 110, start_z + 40), (100, 170, 120), mats["metal"], parent=group)
    make_box(doc, name + "_BOTTOM_RIGHT_NEWEL", (x + width * 0.5 + 90, 110, start_z + 40), (100, 170, 120), mats["metal"], parent=group)

    return group


def build_escalator_array(doc, root, mats):
    """Create several escalator-like forms to echo the reference composition."""
    left = build_escalator(doc, root, mats, "LEFT_ESCALATOR", -430, 1280, 5120, 930, 390)
    right = build_escalator(doc, root, mats, "RIGHT_ESCALATOR", 430, 1280, 5120, 930, 390)

    # A higher central escalator reads as the dramatic upward architectural spine.
    center = build_escalator(doc, root, mats, "CENTRAL_STEEP_ESCALATOR", 0, 250, 4100, 1640, 310)
    center.SetAbsRot(Vector(0, 0, 0))

    # Add two slim overhead track strips to lengthen perspective depth.
    make_ramp_box(doc, "LEFT_OVERHEAD_ESCALATOR_SILHOUETTE", (0, 1450, 350), (0, 2300, 5000), -210, 0, 125, 44, mats["dark"], root)
    make_ramp_box(doc, "RIGHT_OVERHEAD_ESCALATOR_SILHOUETTE", (0, 1450, 350), (0, 2300, 5000), 210, 0, 125, 44, mats["dark"], root)

    return left, right, center


def build_handrails(doc, root, mats):
    """Create the required HANDRAILS object with corridor and path rails."""
    rails = make_null(doc, "HANDRAILS", root)

    # Long wall rails: cylinders run along the corridor depth.
    make_cylinder(doc, "LEFT_WALL_HANDRAIL", (-1625, 185, 3200), 18, 8050, mats["metal"], rot=Vector(0, deg(90), 0), parent=rails)
    make_cylinder(doc, "RIGHT_WALL_HANDRAIL", (1625, 185, 3200), 18, 8050, mats["metal"], rot=Vector(0, deg(90), 0), parent=rails)

    # Central path low guard rails, simple chrome rails on low supports.
    make_cylinder(doc, "LEFT_CENTRAL_PATH_RAIL", (-560, 72, 3350), 14, 5900, mats["metal"], rot=Vector(0, deg(90), 0), parent=rails)
    make_cylinder(doc, "RIGHT_CENTRAL_PATH_RAIL", (560, 72, 3350), 14, 5900, mats["metal"], rot=Vector(0, deg(90), 0), parent=rails)

    for z in range(850, 6100, 600):
        make_box(doc, "left_path_rail_support", (-560, 42, z), (24, 70, 18), mats["metal"], parent=rails)
        make_box(doc, "right_path_rail_support", (560, 42, z), (24, 70, 18), mats["metal"], parent=rails)
        make_box(doc, "left_wall_rail_support", (-1625, 122, z), (26, 88, 18), mats["metal"], parent=rails)
        make_box(doc, "right_wall_rail_support", (1625, 122, z), (26, 88, 18), mats["metal"], parent=rails)

    return rails


def build_lighting(doc, root, mats):
    """Create basic scene lights and luminous strips for a clean white interior."""
    light_group = make_null(doc, "SIMPLE_SCENE_LIGHTING", root)

    key = c4d.BaseObject(c4d.Olight)
    key.SetName("SOFT_OVERHEAD_AREA_LIGHT")
    set_if_exists(key, "LIGHT_TYPE", getattr(c4d, "LIGHT_TYPE_AREA", 8))
    set_if_exists(key, "LIGHT_BRIGHTNESS", 0.95)
    set_if_exists(key, "LIGHT_AREADETAILS_SIZEX", 2800)
    set_if_exists(key, "LIGHT_AREADETAILS_SIZEY", 1200)
    key.SetAbsPos(Vector(0, 1900, 2100))
    insert_object(doc, key, light_group)

    fill = c4d.BaseObject(c4d.Olight)
    fill.SetName("FRONT_LOW_FILL_LIGHT")
    set_if_exists(fill, "LIGHT_BRIGHTNESS", 0.35)
    fill.SetAbsPos(Vector(0, 260, -1450))
    insert_object(doc, fill, light_group)

    # Bright ceiling-like strips nested near the arch.
    make_box(doc, "ARCH_TOP_LIGHT_BAND", (0, 1560, 2350), (2150, 28, 48), mats["light"], parent=light_group)
    make_box(doc, "REAR_TOP_LIGHT_BAND", (0, 1510, 5200), (2500, 28, 48), mats["light"], parent=light_group)


def build_camera(doc, root):
    """Set a low, wide, cinematic camera looking down the corridor."""
    cam = c4d.BaseObject(c4d.Ocamera)
    cam.SetName("CAMERA_MAIN")
    cam.SetAbsPos(Vector(0, 170, -2550))
    look_at(cam, (0, 610, 3550))
    set_if_exists(cam, "CAMERAOBJECT_FOV", deg(92))
    set_if_exists(cam, "CAMERAOBJECT_FOCUS", 18.0)
    set_if_exists(cam, "CAMERAOBJECT_TARGETDISTANCE", 6100)
    insert_object(doc, cam, root)
    doc.SetActiveObject(cam)
    active_view = doc.GetActiveBaseDraw()
    if active_view:
        active_view.SetSceneCamera(cam)
    return cam


def set_render_settings(doc):
    """Set a wide render frame to match the reference image's panoramic feel."""
    rd = doc.GetActiveRenderData()
    set_if_exists(rd, "RDATA_XRES", 2560)
    set_if_exists(rd, "RDATA_YRES", 1080)
    set_if_exists(rd, "RDATA_PIXELRESOLUTION", 72.0)


# ---------------------------------------------------------------------------
# Main script
# ---------------------------------------------------------------------------

def main():
    doc = c4d.documents.GetActiveDocument()
    if doc is None:
        return

    doc.StartUndo()
    try:
        remove_previous_blockout(doc)

        root = make_null(doc, ROOT_NAME)
        doc.AddUndo(c4d.UNDOTYPE_NEWOBJ, root)

        mats = {
            "white": make_material(doc, "warm_white_panels", (0.91, 0.93, 0.92)),
            "path": make_material(doc, "slightly_warmer_floor_path", (0.78, 0.80, 0.78)),
            "seam": make_material(doc, "soft_gray_panel_seams", (0.34, 0.36, 0.36)),
            "dark": make_material(doc, "dark_escalator_rubber", (0.035, 0.038, 0.04)),
            "step_line": make_material(doc, "dark_step_ridges", (0.18, 0.19, 0.19)),
            "yellow": make_material(doc, "muted_safety_yellow", (0.95, 0.71, 0.18)),
            "metal": make_material(doc, "chrome_handrails", (0.62, 0.65, 0.66), metallic=True),
            "metal_light": make_material(doc, "brushed_silver_panels", (0.70, 0.73, 0.74), metallic=True),
            "glass": make_material(doc, "pale_glass_balustrades", (0.70, 0.86, 0.92), transparent=True),
            "light": make_material(doc, "white_luminous_strips", (1.0, 1.0, 0.95), luminance=True),
        }

        build_floor_and_path(doc, root, mats)
        build_walls(doc, root, mats)
        build_architecture_rings(doc, root, mats)
        build_escalator_array(doc, root, mats)
        build_handrails(doc, root, mats)
        build_lighting(doc, root, mats)
        build_camera(doc, root)
        set_render_settings(doc)

    finally:
        doc.EndUndo()
        c4d.EventAdd()


if __name__ == "__main__":
    main()
