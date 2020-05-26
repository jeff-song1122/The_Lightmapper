import bpy

def init(prev_container):

    store_existing(prev_container)

    set_settings()

    configure_world()

    configure_lights()

    configure_meshes()

def configure_world():
    pass

def configure_lights():
    pass

def configure_meshes():

    iterNum = 0
    currentIterNum = 0

    scene = bpy.context.scene

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            for slot in obj.material_slots:
                if "." + slot.name + '_Original' in bpy.data.materials:
                    print("The material: " + slot.name + " shifted to " + "." + slot.name + '_Original')
                    slot.material = bpy.data.materials["." + slot.name + '_Original']

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:
                iterNum = iterNum + 1

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:

                currentIterNum = currentIterNum + 1

                #Configure selection
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                obs = bpy.context.view_layer.objects
                active = obs.active

                #Provide material if none exists
                preprocess_material(obj, scene)

                #UV Layer management here
                if not obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroup":
                    uv_layers = obj.data.uv_layers
                    if not "UVMap_Lightmap" in uv_layers:
                        print("UVMap made B")
                        uvmap = uv_layers.new(name="UVMap_Lightmap")
                        uv_layers.active_index = len(uv_layers) - 1

                        #If lightmap
                        if obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "Lightmap":
                            if scene.TLM_SceneProperties.tlm_apply_on_unwrap:
                                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                            bpy.ops.uv.lightmap_pack('EXEC_SCREEN', PREF_CONTEXT='ALL_FACES', PREF_MARGIN_DIV=obj.TLM_ObjectProperties.tlm_mesh_unwrap_margin)
                        
                        #If smart project
                        elif obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "SmartProject":
                            print("Smart Project B")
                            if scene.TLM_SceneProperties.tlm_apply_on_unwrap:
                                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                            bpy.ops.object.select_all(action='DESELECT')
                            obj.select_set(True)
                            bpy.ops.object.mode_set(mode='EDIT')
                            bpy.ops.mesh.select_all(action='DESELECT')
                            bpy.ops.object.mode_set(mode='OBJECT')
                            bpy.ops.uv.smart_project(angle_limit=45.0, island_margin=obj.TLM_ObjectProperties.tlm_mesh_unwrap_margin, user_area_weight=1.0, use_aspect=True, stretch_to_bounds=False)
                        
                        elif obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroup":

                            print("ATLAS GROUP: " + obj.TLM_ObjectProperties.tlm_atlas_pointer)
                            
                        else: #if copy existing

                            print("Copied Existing B")

                            #Here we copy an existing map
                            pass
                    else:
                        print("Existing found...skipping")
                        for i in range(0, len(uv_layers)):
                            if uv_layers[i].name == 'UVMap_Lightmap':
                                uv_layers.active_index = i
                                print("Lightmap shift B")
                                break

                #Sort out nodes
                for slot in obj.material_slots:

                    nodetree = slot.material.node_tree

                    outputNode = nodetree.nodes[0] #Presumed to be material output node

                    if(outputNode.type != "OUTPUT_MATERIAL"):
                        for node in nodetree.nodes:
                            if node.type == "OUTPUT_MATERIAL":
                                outputNode = node
                                break

                    mainNode = outputNode.inputs[0].links[0].from_node

                    if mainNode.type not in ['BSDF_PRINCIPLED','BSDF_DIFFUSE','GROUP']:

                        #TODO! FIND THE PRINCIPLED PBR
                        self.report({'INFO'}, "The primary material node is not supported. Seeking first principled.")

                        if len(functions.find_node_by_type(nodetree.nodes, function_constants.Node_Types.pbr_node)) > 0: 
                            mainNode = functions.find_node_by_type(nodetree.nodes, function_constants.Node_Types.pbr_node)[0]
                        else:
                            self.report({'INFO'}, "No principled found. Seeking diffuse")
                            if len(functions.find_node_by_type(nodetree.nodes, function_constants.Node_Types.diffuse)) > 0: 
                                mainNode = functions.find_node_by_type(nodetree.nodes, function_constants.Node_Types.diffuse)[0]
                            else:
                                self.report({'INFO'}, "No supported nodes. Continuing anyway.")
                                pass

                    if mainNode.type == 'GROUP':
                        if mainNode.node_tree != "Armory PBR":
                            print("The material group is not supported!")
                            pass

                    if (mainNode.type == "BSDF_PRINCIPLED"):
                        print("BSDF_Principled")
                        if scene.TLM_EngineProperties.tlm_directional_mode == "None":
                            print("Directional mode")
                            if not len(mainNode.inputs[19].links) == 0:
                                print("NOT LEN 0")
                                ninput = mainNode.inputs[19].links[0]
                                noutput = mainNode.inputs[19].links[0].from_node
                                nodetree.links.remove(noutput.outputs[0].links[0])

                        #Clamp metallic
                        if(mainNode.inputs[4].default_value == 1 and scene.TLM_SceneProperties.tlm_clamp_metallic):
                            mainNode.inputs[4].default_value = 0.99

                    if (mainNode.type == "BSDF_DIFFUSE"):
                        print("BSDF_Diffuse")

                for slot in obj.material_slots:

                    nodetree = bpy.data.materials[slot.name].node_tree
                    nodes = nodetree.nodes

                    #First search to get the first output material type
                    for node in nodetree.nodes:
                        if node.type == "OUTPUT_MATERIAL":
                            mainNode = node
                            break

                    #Fallback to get search
                    if not mainNode.type == "OUTPUT_MATERIAL":
                        mainNode = nodetree.nodes.get("Material Output")

                    #Last resort to first node in list
                    if not mainNode.type == "OUTPUT_MATERIAL":
                        mainNode = nodetree.nodes[0].inputs[0].links[0].from_node

                    for node in nodes:
                        if "LM" in node.name:
                            nodetree.links.new(node.outputs[0], mainNode.inputs[0])

                    for node in nodes:
                        if "Lightmap" in node.name:
                                nodes.remove(node)

def preprocess_material(obj, scene):
    if len(obj.material_slots) == 0:
        single = False
        number = 0
        while single == False:
            matname = obj.name + ".00" + str(number)
            if matname in bpy.data.materials:
                single = False
                number = number + 1
            else:
                mat = bpy.data.materials.new(name=matname)
                mat.use_nodes = True
                obj.data.materials.append(mat)
                single = True

    #Make the materials unique if multiple users (Prevent baking over existing)
    for slot in obj.material_slots:
        mat = slot.material
        if mat.users > 1:
                copymat = mat.copy()
                slot.material = copymat 

    #Make a material backup and restore original if exists
    # if scene.TLM_SceneProperties.tlm_caching_mode == "Copy":
    #     for slot in obj.material_slots:
    #         matname = slot.material.name
    #         originalName = "." + matname + "_Original"
    #         hasOriginal = False
    #         if originalName in bpy.data.materials:
    #             hasOriginal = True
    #         else:
    #             hasOriginal = False

    #         if hasOriginal:
    #             matcache.backup_material_restore(slot)

    #         matcache.backup_material_copy(slot)

    # else: #Cache blend
    #     #TEST CACHE
    #     filepath = bpy.data.filepath
    #     dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_SceneProperties.tlm_lightmap_savedir)
    #     path = dirpath + "/cache.blend"
    #     bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
        #print("Warning: Cache blend not supported")

    # for mat in bpy.data.materials:
    #     if mat.name.endswith('_baked'):
    #         bpy.data.materials.remove(mat, do_unlink=True)
    # for img in bpy.data.images:
    #     if img.name == obj.name + "_baked":
    #         bpy.data.images.remove(img, do_unlink=True)


    #SOME ATLAS EXCLUSION HERE?
    ob = obj
    for slot in ob.material_slots:
        #If temporary material already exists
        if slot.material.name.endswith('_temp'):
            continue
        n = slot.material.name + '_' + ob.name + '_temp'
        if not n in bpy.data.materials:
            slot.material = slot.material.copy()
        slot.material.name = n

    #Add images for baking
    img_name = obj.name + '_baked'
    #Resolution is object lightmap resolution divided by global scaler

    res = int(obj.TLM_ObjectProperties.tlm_mesh_lightmap_resolution) / int(scene.TLM_EngineProperties.tlm_resolution_scale)

    #If image not in bpy.data.images or if size changed, make a new image
    if img_name not in bpy.data.images or bpy.data.images[img_name].size[0] != res or bpy.data.images[img_name].size[1] != res:
        img = bpy.data.images.new(img_name, res, res, alpha=True, float_buffer=True)

        num_pixels = len(img.pixels)
        result_pixel = list(img.pixels)

        for i in range(0,num_pixels,4):
            # result_pixel[i+0] = scene.TLM_SceneProperties.tlm_default_color[0]
            # result_pixel[i+1] = scene.TLM_SceneProperties.tlm_default_color[1]
            # result_pixel[i+2] = scene.TLM_SceneProperties.tlm_default_color[2]
            result_pixel[i+0] = 0.0
            result_pixel[i+1] = 0.0
            result_pixel[i+2] = 0.0
            result_pixel[i+3] = 1.0

        img.pixels = result_pixel

        img.name = img_name
    else:
        img = bpy.data.images[img_name]

    for slot in obj.material_slots:
        mat = slot.material
        mat.use_nodes = True
        nodes = mat.node_tree.nodes

        if "Baked Image" in nodes:
            img_node = nodes["Baked Image"]
        else:
            img_node = nodes.new('ShaderNodeTexImage')
            img_node.name = 'Baked Image'
            img_node.location = (100, 100)
            img_node.image = img
        img_node.select = True
        nodes.active = img_node

def set_settings():

    scene = bpy.context.scene
    cycles = scene.cycles
    sceneProperties = scene.TLM_SceneProperties
    engineProperties = scene.TLM_EngineProperties
    cycles.device = scene.TLM_EngineProperties.tlm_mode
    scene.render.engine = "CYCLES"
    
    if engineProperties.tlm_quality == "Preview":
        cycles.samples = 32
        cycles.max_bounces = 1
        cycles.diffuse_bounces = 1
        cycles.glossy_bounces = 1
        cycles.transparent_max_bounces = 1
        cycles.transmission_bounces = 1
        cycles.volume_bounces = 1
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif engineProperties.tlm_quality == "Preview2":
        cycles.samples = 64
        cycles.max_bounces = 2
        cycles.diffuse_bounces = 2
        cycles.glossy_bounces = 2
        cycles.transparent_max_bounces = 2
        cycles.transmission_bounces = 2
        cycles.volume_bounces = 2
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif engineProperties.tlm_quality == "Medium":
        cycles.samples = 512
        cycles.max_bounces = 2
        cycles.diffuse_bounces = 2
        cycles.glossy_bounces = 2
        cycles.transparent_max_bounces = 2
        cycles.transmission_bounces = 2
        cycles.volume_bounces = 2
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif engineProperties.tlm_quality == "High":
        cycles.samples = 1024
        cycles.max_bounces = 256
        cycles.diffuse_bounces = 256
        cycles.glossy_bounces = 256
        cycles.transparent_max_bounces = 256
        cycles.transmission_bounces = 256
        cycles.volume_bounces = 256
        cycles.caustics_reflective = False
        cycles.caustics_refractive = False
    elif engineProperties.tlm_quality == "Production":
        cycles.samples = 2048
        cycles.max_bounces = 512
        cycles.diffuse_bounces = 512
        cycles.glossy_bounces = 512
        cycles.transparent_max_bounces = 512
        cycles.transmission_bounces = 512
        cycles.volume_bounces = 512
        cycles.caustics_reflective = True
        cycles.caustics_refractive = True
    else: #Custom
        pass

def store_existing(prev_container):

    scene = bpy.context.scene
    cycles = scene.cycles

    selected = []

    for obj in bpy.data.objects:
        if obj.select_get():
            selected.append(obj.name)

    prev_container["settings"] = [
        cycles.samples,
        cycles.max_bounces,
        cycles.diffuse_bounces,
        cycles.glossy_bounces,
        cycles.transparent_max_bounces,
        cycles.transmission_bounces,
        cycles.volume_bounces,
        cycles.caustics_reflective,
        cycles.caustics_refractive,
        cycles.device,
        scene.render.engine,
        bpy.context.view_layer.objects.active,
        selected
    ]