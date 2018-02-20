import bpy
import os

# the file paths for the script
path = os.path.dirname(__file__)
split_path = os.path.split(path)
table_path = os.path.join(split_path[0], r'blender_test_project-master\assets\models\table\table.obj')
env_map_path = os.path.join(split_path[0], r"blender_test_project-master\assets\HDRIs\cayley_interior")
texture_path = os.path.join(
    split_path[0],
    r"blender_test_project-master\assets\textures\table\WoodFine26\WoodFine26\1K")
output_path = os.path.join(
    split_path[0],
    r"blender_test_project-master\outputs\render")
#floor doesn't have its own texture

print('split_path is ' + split_path[0])

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

    #material only works in Cycles render engine
    bpy.data.scenes[0].render.engine = 'CYCLES'
    
    # creates a new material and adds it to the object
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
        print('full path is ' + full_path)
        image = bpy.ops.image.open(filepath=full_path)
        complete_images.append(compl_tex_name)
        print('Complete texture name is ' + compl_tex_name)
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
    
    text_gloss_node.projection = 'BOX'
    text_diff_node.projection = 'BOX'
    text_normal_node.projection = 'BOX'
    text_ref_node.projection = 'BOX'
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


def set_enviroment_tex(file_path, texture_name, light_scene=False):
    '''creates a HDRI material and applies it to the enviroment

    Keywork Arguments

    file_path -- string that contains filepath of HDRI
    texture_name -- the name of the texture, including its extention
    light_scene -- bool, HDRI lights scene vs only visible to camera
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
    
    if not light_scene:
        light_node = world.node_tree.nodes.new('ShaderNodeLightPath')
        mix_shader = world.node_tree.nodes.new('ShaderNodeMixShader')
        darkness_shader = world.node_tree.nodes.new('ShaderNodeBackground')
    

        world.node_tree.links.new(
            env_node.outputs['Color'],
            bg_shader.inputs['Color'])
        world.node_tree.links.new(
            bg_shader.outputs['Background'],
            mix_shader.inputs[2])
        world.node_tree.links.new(
            darkness_shader.outputs['Background'],
            mix_shader.inputs[1])
        world.node_tree.links.new(
            light_node.outputs['Is Camera Ray'],
            mix_shader.inputs['Fac'])
        world.node_tree.links.new(
            mix_shader.outputs['Shader'],
            output_node.inputs['Surface'])    
        env_node.image = bpy.data.images[0]
        darkness_shader.inputs[1].default_value = 0
        
    else:
        world.node_tree.links.new(
            env_node.outputs['Color'],
            bg_shader.inputs['Color'])
        world.node_tree.links.new(
            bg_shader.outputs['Background'],
            output_node.inputs['Surface'])
            

def create_light_mat(object, blackbody=55000, light_str=1):
    '''adds a light material to the object that is
    passes as an argument.

    object -- blender object class
    blackbody -- float, color temperature in Kelvin
    light_str -- float, emission strength
    ''' 

    # material only works in cycles render engine    
    bpy.data.scenes[0].render.engine = 'CYCLES'
    
    # creates a new material and adds it to the object
    material = bpy.data.materials.new(object.name)
    object.data.materials.append(material)

    # applies the material to all material slots
    for slots in range(0, len(object.material_slots)):
        object.material_slots[slots].material = material

    # enables nodes & clears all nodes
    material.use_nodes = True
    for node in material.node_tree.nodes:
        material.node_tree.nodes.remove(node)
        
    # Creates necessary nodes
    emission_shader = material.node_tree.nodes.new('ShaderNodeEmission')
    blackbody_node = material.node_tree.nodes.new('ShaderNodeBlackbody')
    output_node = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
    
    # creates links
    material.node_tree.links.new(
        blackbody_node.outputs['Color'],
        emission_shader.inputs['Color'])
    material.node_tree.links.new(
        emission_shader.outputs['Emission'],
        output_node.inputs['Surface'])
        
    # Sets the nodes values
    blackbody_node.inputs[0].default_value = blackbody
    emission_shader.inputs[1].default_value = light_str
    

def comp_nodes_setup():
    '''sets up a custom configuration of node in 
    Blender"s node compositor'''
    
    # enables nodes 
    bpy.data.scenes[0].use_nodes = True
    
    # note: blender UI shows wrong path for composite node tree
    comp_tree = bpy.data.scenes[0].node_tree
    
    # clears all nodes
    for node in comp_tree.nodes:
        comp_tree.nodes.remove(node)
        
    # creates all the nodes    
    defocus_node = comp_tree.nodes.new('CompositorNodeDefocus')
    sep_node = comp_tree.nodes.new('CompositorNodeSepHSVA')
    math_node = comp_tree.nodes.new('CompositorNodeMath')
    ramp_node = comp_tree.nodes.new('CompositorNodeValToRGB')
    comb_node = comp_tree.nodes.new('CompositorNodeCombHSVA')
    gamma_node = comp_tree.nodes.new('CompositorNodeGamma')
    layers_node = comp_tree.nodes.new('CompositorNodeRLayers')
    output_node = comp_tree.nodes.new('CompositorNodeComposite')
    balance_node = comp_tree.nodes.new('CompositorNodeColorBalance')
    
    # change all nodes' settings
    defocus_node.bokeh = 'OCTAGON'
    defocus_node.use_gamma_correction = True
    defocus_node.f_stop = 1
    defocus_node.blur_max = 32
    defocus_node.threshold = 14
    defocus_node.use_zbuffer = True
    
    math_node.operation = 'MULTIPLY'
    
    gamma_node.inputs[1].default_value = 1.1
    
    ramp_node.color_ramp.elements.new(0.361)    
    ramp_node.color_ramp.elements[0].position = 0
    ramp_node.color_ramp.elements[1].position = 0.045
    ramp_node.color_ramp.elements[2].position = 0.361
    ramp_node.color_ramp.elements[0].color[0] = 0.015
    ramp_node.color_ramp.elements[0].color[1] = 0.015
    ramp_node.color_ramp.elements[0].color[2] = 0.015
    ramp_node.color_ramp.elements[1].color[0] = 1
    ramp_node.color_ramp.elements[1].color[1] = 1
    ramp_node.color_ramp.elements[1].color[2] = 1
    ramp_node.color_ramp.elements[2].color[0] = 0
    ramp_node.color_ramp.elements[2].color[1] = 0
    ramp_node.color_ramp.elements[2].color[2] = 0
    ramp_node.color_ramp.interpolation = 'LINEAR'
    
    balance_node.lift[0] = 0.92
    balance_node.lift[1] = 0.92
    balance_node.lift[2] = 0.92
    balance_node.gamma[0] = 1.06
    balance_node.gamma[1] = 1.06
    balance_node.gamma[2] = 1.06
    balance_node.gain[0] = 1.56
    balance_node.gain[1] = 1.56
    balance_node.gain[2] = 1.56
    
    #creates all the links
    comp_tree.links.new(
        layers_node.outputs['Image'],
        defocus_node.inputs['Image'])
    comp_tree.links.new(
        layers_node.outputs['Depth'],
        defocus_node.inputs['Z'])
    comp_tree.links.new(
        defocus_node.outputs['Image'],
        sep_node.inputs['Image'])
    comp_tree.links.new(
        layers_node.outputs['Image'],
        defocus_node.inputs['Image'])
    comp_tree.links.new(
        sep_node.outputs['H'],
        comb_node.inputs['H'])
    comp_tree.links.new(
        sep_node.outputs['S'],
        math_node.inputs[0])
    comp_tree.links.new(
        sep_node.outputs['V'],
        comb_node.inputs['V'])
    comp_tree.links.new(
        sep_node.outputs['V'],
        ramp_node.inputs['Fac'])
    comp_tree.links.new(
        ramp_node.outputs['Image'],
        math_node.inputs[1])
    comp_tree.links.new(
        math_node.outputs['Value'],
        comb_node.inputs['S'])
    comp_tree.links.new(
        comb_node.outputs['Image'],
        gamma_node.inputs['Image'])
    comp_tree.links.new(
        gamma_node.outputs['Image'],
        balance_node.inputs['Image'])
    comp_tree.links.new(
        balance_node.outputs['Image'],
        output_node.inputs['Image'])
    
# _____________script_______________

objects = bpy.data.objects
print('table path is ' + table_path)
# clears Scene, Imports table, scales and transforms
table = set_up_table(table_path)

# adds a ground plane, scales, and centers it
bpy.ops.mesh.primitive_plane_add()
ground_plane = objects[0]
ground_plane.name = "ground_plane"
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

# Add camera and lighting
# rotation units are radians
bpy.ops.object.camera_add()
bpy.ops.mesh.primitive_plane_add()
bpy.ops.mesh.primitive_plane_add()

objects['Plane'].name = 'key_light'
objects['Plane.001'].name = 'fill_light'

camera = objects['Camera']
fill_light = objects['fill_light']
key_light = objects['key_light']

# Positioning of camera
camera.rotation_euler[0] = 0.928418
camera.rotation_euler[1] = 0
camera.rotation_euler[2] = -0.547109

camera.location[0] = -55.27895
camera.location[1] = -57.611
camera.location[2] = 104.11497

# set as active camera
bpy.data.scenes[0].camera = camera

# positioning of fill_light
fill_light.scale[0] = 110
fill_light.scale[1] = 110
fill_light.scale[2] = 110

fill_light.rotation_euler[0] = 0
fill_light.rotation_euler[1] = 0.677965
fill_light.rotation_euler[2] = 1.570796

fill_light.location[0] = -15.85
fill_light.location[1] = 247.74
fill_light.location[2] = 93.55

# positioning of key_light
key_light.scale[0] = 60.5
key_light.scale[1] = 60.5
key_light.scale[2] = 60.5

key_light.location[0] = 81.9
key_light.location[1] = -2.63
key_light.location[2] = 46.77

key_light.rotation_euler[0] = 0
key_light.rotation_euler[1] = 1.486875
key_light.rotation_euler[2] = 0

# applies light mat to both objects
create_light_mat(fill_light, blackbody=4000)
create_light_mat(key_light, blackbody=60000, light_str=25)

# Render Settings
cycles = bpy.data.scenes[0].cycles
render = bpy.data.scenes[0].render

render.filepath = output_path
render.resolution_x = 1280
render.resolution_y = 960
render.resolution_percentage = 100
cycles.samples = 512
cycles.film_exposure = .25
cycles.film_transparent = False

render.tile_x = 256
render.tile_y = 256

bpy.data.scenes[0].view_settings.view_transform = 'Filmic'

bpy.data.scenes[0].render.layers[0].cycles.use_denoising = True

cycles.device = 'GPU'

# Function for setting up Compositing Nodes
comp_nodes_setup()

# Renders!!!
bpy.ops.render.render(write_still=True)

# test from command line
