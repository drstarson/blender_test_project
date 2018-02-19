import bpy
import os

# the file paths for the script
path = os.path.dirname(__file__)
split_path = os.path.split(path)
table_path = os.path.join(split_path[0], r'assets\models\table\table.obj')
env_map_path = os.path.join(split_path[0], r"assets\HDRIs\cayley_interior")
texture_path = os.path.join(
    split_path[0],
    r"assets\textures\table\WoodFine26\WoodFine26\1K")

# _________________Functions___________________


def set_up_table(obj_path, clear_scene=True):
    '''Imports an obj file, scales is so that the height is 76.2 blender units,
    sets to highest point in Z=0, centers on the other two axies

    Keywork Arguments

    obj_path -- the absolute path of the obj file, including the file itself.
    clear_scene -- Boolean, deletes all objects (default = True)
    '''

    objects = bpy.data.objects
    # cleared any default objects from the scene
    if clear_scene:
        for i in objects:
            objects.remove(i)
    bpy.ops.import_scene.obj(filepath=obj_path)

    obj_name = os.path.split(obj_path)
    bpy.data.objects[0].name = obj_name[1]
    table = bpy.data.objects[obj_name[1]]

    # changes the hight of the table & scales accordingly
    table.dimensions.y = 76.2
    table.scale.x = table.scale.y
    table.scale.z = table.scale.y

    # finds the vertical bounds of the table to align to z=0

    verticalBounds = []
    for v in table.data.vertices:
        verticalBounds.append(table.matrix_world*v.co)
    verticalMax = max(verticalBounds)
    table.location[2] -= verticalMax[2]

    return table


def create_PBR_mat(object, file_path, texture_name):
    '''Creates a material, PBR node tree, and textures and applies it to the object
    Textures must use the Poliigon.com naming scheme.

    Keywork Arguments

    object -- a bpy.data.objects class
    file_path -- the file path to the image textures
    texture_name -- the name of the texture group. e.g. WoodFine26

    note: automatically enables Cycles

    todo: have function check if file is 1k,2k,4k,6k.'''

    objects = bpy.data.objects

    # makes sure the end fo the path does not include a file
    path_check = os.path.split(file_path)
    filepath = path_check[0]

    # creates a new material and adds it to the object
    bpy.data.scenes[0].render.engine = 'CYCLES'
    material = bpy.data.materials.new(object.name)
    object.data.materials.append(material)

    # applies the material to all material slots
    for slots in range(0, len(object.material_slots)):
        object.material_slots[slots].material = material

    # enables nodes & clears all nodes
    material.use_nodes = True
    for node in material.node_tree.nodes:
        material.node_tree.nodes.remove(node)

    # creates the node
    textures = ["COL", "GLOSS", "NRM", "REFL"]
    complete_images = []
    for texture_types in textures:
        compl_tex_name = texture_name + "_" + texture_types + "_1K.jpg"
        full_path = os.path.join(file_path, compl_tex_name)
        image = bpy.ops.image.open(filepath=full_path)
        complete_images.append(compl_tex_name)
        nodes = material.node_tree.nodes
    principled_shader = nodes.new('ShaderNodeBsdfPrincipled')
    text_diff_node = nodes.new('ShaderNodeTexImage')
    text_gloss_node = nodes.new('ShaderNodeTexImage')
    text_normal_node = nodes.new('ShaderNodeTexImage')
    text_ref_node = nodes.new('ShaderNodeTexImage')
    normal_map_node = nodes.new('ShaderNodeNormalMap')
    invert_node = nodes.new('ShaderNodeInvert')
    mat_output_node = nodes.new('ShaderNodeOutputMaterial')
    tex_coor_node = nodes.new('ShaderNodeTexCoord')
    tex_map_node = nodes.new('ShaderNodeMapping')
    text_gloss_node.color_space = 'NONE'
    text_normal_node.color_space = 'NONE'
    text_ref_node.color_space = 'NONE'

    material.node_tree.links.new(
        text_diff_node.outputs['Color'],
        principled_shader.inputs['Base Color'])
    material.node_tree.links.new(
        text_gloss_node.outputs['Color'],
        invert_node.inputs['Color'])
    material.node_tree.links.new(
        invert_node.outputs['Color'],
        principled_shader.inputs['Roughness'])
    material.node_tree.links.new(
        text_diff_node.outputs['Color'],
        principled_shader.inputs['Base Color'])
    material.node_tree.links.new(
        text_ref_node.outputs['Color'],
        principled_shader.inputs['Specular'])
    material.node_tree.links.new(
        text_normal_node.outputs['Color'],
        normal_map_node.inputs['Color'])
    material.node_tree.links.new(
        normal_map_node.outputs['Normal'],
        principled_shader.inputs['Normal'])
    material.node_tree.links.new(
        principled_shader.outputs['BSDF'],
        mat_output_node.inputs['Surface'])
    material.node_tree.links.new(
        tex_coor_node.outputs['Generated'],
        tex_map_node.inputs['Vector'])
    material.node_tree.links.new(
        tex_map_node.outputs['Vector'],
        text_diff_node.inputs['Vector'])
    material.node_tree.links.new(
        tex_map_node.outputs['Vector'],
        text_gloss_node.inputs['Vector'])
    material.node_tree.links.new(
        tex_map_node.outputs['Vector'],
        text_normal_node.inputs['Vector'])
    material.node_tree.links.new(
        tex_map_node.outputs['Vector'],
        text_ref_node.inputs['Vector'])

    text_diff_node.image = bpy.data.images[complete_images[0]]
    text_gloss_node.image = bpy.data.images[complete_images[1]]
    text_normal_node.image = bpy.data.images[complete_images[2]]
    text_ref_node.image = bpy.data.images[complete_images[3]]


def set_enviroment_tex(file_path, texture_name):
    '''creates a HDRI material and applies it to the enviroment

    Keywork Arguments

    file_path -- string that contains filepath of HDRI
    texture_name -- the name of the texture, including its extention
    '''

    # makes sure the end of the path does not include a file
    path_check = os.path.split(file_path)
    filepath = path_check[0]

    bpy.data.scenes[0].render.engine = 'CYCLES'

    full_path = os.path.join(file_path, texture_name)
    image = bpy.ops.image.open(filepath=full_path)
    world = bpy.data.worlds[0]

    # enables nodes and clears the current node tree
    world.use_nodes = True
    for node in world.node_tree.nodes:
        world.node_tree.nodes.remove(node)

    # creates a new node tree and applies the HDRI
    env_node = world.node_tree.nodes.new('ShaderNodeTexEnvironment')
    bg_shader = world.node_tree.nodes.new('ShaderNodeBackground')
    output_node = world.node_tree.nodes.new('ShaderNodeOutputWorld')

    world.node_tree.links.new(
        env_node.outputs['Color'],
        bg_shader.inputs['Color'])
    world.node_tree.links.new(
        bg_shader.outputs['Background'],
        output_node.inputs['Surface'])
    env_node.image = bpy.data.images[0]

# _____________script_______________

objects = bpy.data.objects

# clears Scene, Imports table, scales and transforms
table = set_up_table(table_path)

# adds a ground plane, scales, and centers it
bpy.ops.mesh.primitive_plane_add()
ground_plane = objects[0]
ground_plane.name = "groundPlane"
ground_plane.dimensions = [1000, 1000, 0]
ground_plane.location = [0, 0, 0]

# clears all materials from the scene
for material in range(len(bpy.data.materials)):
    bpy.data.materials.remove(bpy.data.materials[0])

# creates & assigns materials to objects
create_PBR_mat(table, texture_path, "WoodFine26")
create_PBR_mat(ground_plane, texture_path, "WoodFine26")

# set up HDRI (make sure HDRI is not lighting scene)
set_enviroment_tex(env_map_path, 'cayley_interior_1k.hdr')

# set up render settings
# Add camera and lighting
# test from command line

# path is currently relative to blender file path, not script path
# todo: Set to 8k hdr
# add box projection to material function
# need to find a texture setup for floor
