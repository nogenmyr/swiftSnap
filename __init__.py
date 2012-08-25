# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "SwiftSnap",
    "author": "Karl-Johan Nogenmyr",
    "version": (0, 1),
    "blender": (2, 6, 1),
    "api": 35622,
    "location": "Tool Shelf",
    "description": "Writes snappyHexMeshDict from a Blender object",
    "warning": "not much tested yet",
    "wiki_url": "None",
    "tracker_url": "",
    "support": 'COMMUNITY',
    "category": "OpenFOAM"}

#----------------------------------------------------------
# File scene_props.py
#----------------------------------------------------------
import bpy
import mathutils
from bpy.props import *
 
def shmpatchColor(patch_no):
    color = [(1.0,0.,0.), (0.0,1.,0.),(0.0,0.,1.),(0.707,0.707,0),(0,0.707,0.707),(0.707,0,0.707)]
    return color[patch_no % len(color)]
    
def writeeMeshFile(path,verts,edges,level):
    filename = 'level%s.eMesh'%level
    f = open(path+'/' + filename, 'w')
    fobj = open(path+'/level%s.obj'%level, 'w')
    
    f.write(utils.foamHeader('featureEdgeMesh','points'))
    f.write('(\n')
    for v in verts:
        f.write('({} {} {})\n'.format(*v))
        fobj.write('v {} {} {}\n'.format(*v))
    f.write(')\n\n')
    f.write('(\n')
    for e in edges:
        f.write('({} {})\n'.format(*e))
        fobj.write('l {} {}\n'.format(e[0]+1,e[1]+1))
    f.write(')\n')
    f.close()
    return filename


def initshmProperties():

    bpy.types.Scene.ctmFloat = FloatProperty(
        name = "convertToMeters", 
        description = "Conversion factor: Blender coords to meter",
        default = 1.0,
        min = 0.)
             
    bpy.types.Scene.snap = BoolProperty(
        name = "Snap mesh", 
        description = "Should snappyHexMesh do the snapping stage?",
        default = True)
     
    bpy.types.Scene.cast = BoolProperty(
        name = "Castellated mesh", 
        description = "Should snappyHexMesh do a castellated mesh?",
        default = True)
     
    bpy.types.Scene.lays = BoolProperty(
        name = "Add layers", 
        description = "Should snappyHexMesh add boundary layer cells?",
        default = False)
         
    bpy.types.Scene.patchMinLevel = IntProperty(
        name = "Min level", 
        description = "The minimum refinement level at this patch",
        min = 0)

    bpy.types.Scene.patchMaxLevel = IntProperty(
        name = "Max level", 
        description = "The maximum refinement level at this patch",
        min = 0)

    bpy.types.Scene.patchLayers = IntProperty(
        name = "Layers", 
        description = "Number of layers to grow at patch",
        min = 0)

    bpy.types.Scene.featLevel = IntProperty(
        name = "Feat. level", 
        description = "Selects feature line refinement level",
        min = 0)

    bpy.types.Scene.refineLevel = IntProperty(
        name = "Level", 
        description = "Sets region's refinement level",
        min = 0)

    bpy.types.Scene.refineDist = FloatProperty(
        name = "Distance", 
        description = "Sets region's refinement distance",
        min = 0.)

    bpy.types.Scene.refineInside = BoolProperty(
        name = "Refine inside object", 
        description = "Should refinement be inside the object?",
        default = True)

    bpy.types.Scene.shmpatchName = StringProperty(
        name = "Name",
        description = "Specify name of patch (max 31 chars)",
        default = "defaultName")
    
    bpy.types.Scene.featAngle = FloatProperty(
        name = "featureAngle", 
        description = "Feature angle",
        default = 150.0,
        min = 0.)
        
    bpy.types.Scene.resFloat = FloatProperty(
        name = "resolution", 
        description = "The spatial resolution of base mesh in meter",
        default = 1.0,
        min = 0)
 
    bpy.types.Scene.makeBMD = BoolProperty(
        name = "Make base mesh", 
        description = "Should a blockMeshDict be auto-generated?",
        default = False)

    bpy.types.Scene.refregName = StringProperty(
        name = "Refine region", 
        description = "Name of object to use as refinement region",
        default = '')

    return


#
#    Menu in UI region
#
class RSUIPanel(bpy.types.Panel):
    bl_label = "SwiftSnap settings"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    
    def draw(self, context):
        layout = self.layout
        scn = context.scene
        obj = context.active_object
        settings = context.tool_settings
        try:
            obj['swiftsnap']
        except:
            layout.operator("enable.swiftsnap")
        else:
            layout.operator("write.shmfile")
#            layout.prop(scn, 'cast') # Always do castalleted mesh
            layout.prop(scn, 'ctmFloat')
            if scn.makeBMD:
                split = layout.split()
                col = split.column()
                col.prop(scn, 'makeBMD')
                col = split.column()
                col.prop(scn, 'resFloat')
            else:
                layout.prop(scn, 'makeBMD')
            split = layout.split()
            col = split.column()
            col.prop(scn, 'snap')
            col = split.column()
            col.prop(scn, 'lays')
            layout.operator("set.locationinmesh")
            box = layout.box()
            box.label(text='Feature settings')
            col = box.column(align=True)
            col.operator("sel.nonmani")
            col.prop(scn, 'featAngle')
            col.operator("sel.feature")
            col.prop(scn, 'featLevel')
            col.operator('mark.feature',text= "Mark as Level %s"%scn.featLevel)
            col.operator('unmark.feature')
            if obj['featLevels'].items():
                col.label(text='Defined features, click to select')
            row = col.row(align=True)
            for level in obj['featLevels']:
                row.operator('show.feature',text=level, emboss=False).whichLevel = int(level)

#            col.prop(obj.data,'show_edge_sharp',text="Show marked feats.") # This thing can make feature lines shine blue!
            box = layout.box()
            box.label(text="Patch settings")
            box.prop(scn, 'shmpatchName')
            row = box.row(align=True)
            row.prop(scn, 'patchMinLevel')
            row.prop(scn, 'patchMaxLevel')
            row = box.row(align=False)
            if scn.lays:
                row.prop(scn, 'patchLayers')
                row.operator("set.shmpatchname")
            else:
                row.operator("set.shmpatchname")
            if scn.lays:
                box.label(text="Color, min, max, name, layers")
            else:
                box.label(text="Color, min, max, name")
            for m in obj.data.materials:
                try:
                    textstr = '{}, {}, {}'.format(m['minLevel'],m['maxLevel'], m.name)
                    lays = str(m['patchLayers'])
                    if scn.lays:
                        textstr += ', ' + lays
                    split = box.split(percentage=0.2, align=False)
                    col = split.column()
                    col.prop(m, "diffuse_color", text="")
                    col = split.column()
                    col.operator("set.shmgetpatch", text=textstr, emboss=False).whichPatch = m.name
                except:
                    pass
            box = layout.box()
            box.label(text="Refinement settings")
            box.prop(scn, 'refregName')
            row = box.row(align=True)
            row.prop(scn, 'refineLevel')
            row.prop(scn, 'refineDist')
            box.prop(scn,"refineInside")
            col = box.column()
            col.enabled = False
            if scn.refregName in bpy.data.objects:
                col.enabled = True
            col.operator("set.refreg")
            box.row(align=False)
            try:
                for refreg in obj['refreg']:
                    if obj['refreg'][refreg]['inside']:
                        mode = 'inside'
                    else:
                        mode = 'outside'
                    textstr = "Refine {1:g} level {2:g} m {3:} {0:}".format(refreg, obj['refreg'][refreg]['level'], obj['refreg'][refreg]['dist'],mode)
                    box.operator("remove.refine", text=textstr, emboss=False).whichObj = refreg
            except:
                pass

    
class OBJECT_OT_SetRefRegObj(bpy.types.Operator):
    '''Set given object as a refinment region'''
    bl_idname = "set.refreg"
    bl_label = "Set Refinement Region"

    def execute(self, context):
        obj = context.active_object
        scn = context.scene
        name = scn.refregName
        try:
            bpy.data.objects[name]
            try:
                obj['refreg']
            except:
                obj['refreg'] = {}
            if not name in obj['refreg']:
                obj['refreg'][name] = {}
            obj['refreg'][name]['level'] = scn.refineLevel
            obj['refreg'][name]['dist'] = scn.refineDist
            obj['refreg'][name]['inside'] = scn.refineInside
        except:
            print("Object %s not found!"%name)
        
        return {'FINISHED'}
    
class OBJECT_OT_UnsetRefRegObj(bpy.types.Operator):
    '''Remove this refinement'''
    bl_idname = "remove.refine"
    bl_label = "Defined refinement region. Click to remove."
    
    whichObj = StringProperty()

    def execute(self, context):
        obj = context.active_object
        obj['refreg'].pop(self.whichObj)
        return {'FINISHED'}
    
class OBJECT_OT_SetInsidePoint(bpy.types.Operator):
    '''Set the locationInMesh coordinate using the 3D cursor'''
    bl_idname = "set.locationinmesh"
    bl_label = "Set locationInMesh"

    def execute(self, context):
        obj = context.active_object
        obj['locinmesh'] = context.scene.cursor_location
        return {'FINISHED'}
    
class OBJECT_OT_Nonmani(bpy.types.Operator):
    '''Finds and selects non-manifold edges'''
    bl_idname = "sel.nonmani"
    bl_label = "Detect Non-Manifold"

    def execute(self, context):
        obj = context.active_object
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.wm.context_set_value(data_path="tool_settings.mesh_select_mode", value="(False,True,False)")
        for e in obj.data.edges:
            e.select = False
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_non_manifold()
        return {'FINISHED'}
    
class OBJECT_OT_FeatureSel(bpy.types.Operator):
    '''Finds and selects feature edges'''
    bl_idname = "sel.feature"
    bl_label = "Detect Features"

    def execute(self, context):
        obj = context.active_object
        scn = context.scene
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.wm.context_set_value(data_path="tool_settings.mesh_select_mode", value="(False,True,False)")
        for e in obj.data.edges:
            e.select = False
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.edges_select_sharp(sharpness=scn.featAngle)
        return {'FINISHED'}
    
class OBJECT_OT_FeatureMark(bpy.types.Operator):
    '''Marks selected edges as feature lines'''
    bl_idname = "mark.feature"
    bl_label = "Mark selected edges as feature lines"

    def execute(self, context):
        obj = context.active_object
        scn = context.scene
        bpy.ops.object.mode_set(mode='OBJECT')
        for e in obj.data.edges:
            if e.select:
                e.use_edge_sharp = True
                e.bevel_weight = 0.01*scn.featLevel # Store level info in bevel_weight (which is a float in range [0,1])

        obj['featLevels'] = {}  # Reset the info on present feature edge levels
        for e in obj.data.edges:
            if e.use_edge_sharp:
                obj['featLevels'][str(round(100*e.bevel_weight))] = 1
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}
    
class OBJECT_OT_FeatureUnmark(bpy.types.Operator):
    '''Unmarks selected edges as feature lines'''
    bl_idname = "unmark.feature"
    bl_label = "Unmark Selected"

    def execute(self, context):
        obj = context.active_object
        bpy.ops.object.mode_set(mode='OBJECT')
        for e in obj.data.edges:
            if e.select:
                e.use_edge_sharp = False
                e.bevel_weight = 0.0
                
        obj['featLevels'] = {}  # Reset the info on present feature edge levels
        for e in obj.data.edges:
            if e.use_edge_sharp:
                obj['featLevels'][str(round(100*e.bevel_weight))] = 1
                
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}
    
class OBJECT_OT_FeatureShow(bpy.types.Operator):
    '''Show previously set feature edges'''
    bl_idname = "show.feature"
    bl_label = "Show previously set feature edges"

    whichLevel = IntProperty()
    
    def execute(self, context):
        obj = context.active_object
        scn = context.scene
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.wm.context_set_value(data_path="tool_settings.mesh_select_mode", value="(False,True,False)")

        for e in obj.data.edges:
            e.select = False
            if e.use_edge_sharp and round(100*e.bevel_weight) == self.whichLevel:
                e.select = True
        bpy.ops.object.mode_set(mode='EDIT')
        scn.featLevel = self.whichLevel
        return {'FINISHED'}
    
class OBJECT_OT_shmEnable(bpy.types.Operator):
    '''Enables SwiftSnap for the active object'''
    bl_idname = "enable.swiftsnap"
    bl_label = "Enable SwiftSnap"
# initializes an object    
    def execute(self, context):
        
        obj = context.active_object
        scn = context.scene

        obj['swiftsnap'] = True
        obj['featLevels'] = {}
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.material_slot_remove()
        bpy.ops.wm.context_set_value(data_path="tool_settings.mesh_select_mode", value="(False,True,False)")
        for e in obj.data.edges:
            e.use_edge_sharp=False
            e.bevel_weight = 0.
        bpy.ops.wm.context_set_value(data_path="tool_settings.mesh_select_mode", value="(False,False,True)")
        for f in obj.data.faces:
            f.select=True
        try:
            mat = bpy.data.materials['defaultName']
            patchindex = list(obj.data.materials).index(mat)
            obj.active_material_index = patchindex
        except: 
            mat = bpy.data.materials.new('defaultName')
            mat.diffuse_color = (0.5,0.5,0.5)
            bpy.ops.object.material_slot_add() 
            obj.material_slots[-1].material = mat
        mat['minLevel'] = scn.patchMinLevel
        mat['maxLevel'] = scn.patchMaxLevel
        mat['patchLayers'] = scn.patchLayers
        bpy.ops.object.editmode_toggle()  
        bpy.ops.object.material_slot_assign()
        bpy.ops.object.editmode_toggle()  
        for v in obj.data.vertices:
            v.select=False
        bpy.ops.object.editmode_toggle()  
        return{'FINISHED'}

class OBJECT_OT_shmSetPatchName(bpy.types.Operator):
    '''Set the given name to the selected faces'''
    bl_idname = "set.shmpatchname"
    bl_label = "Set Patch"
    
    def execute(self, context):
        scn = context.scene
        obj = context.active_object
        bpy.ops.object.mode_set(mode='OBJECT')
        namestr = scn.shmpatchName
        namestr = namestr.strip()
        namestr = namestr.replace(' ', '_')
        try:
            mat = bpy.data.materials[namestr]
            patchindex = list(obj.data.materials).index(mat)
            obj.active_material_index = patchindex
        except: # add a new patchname (as a blender material, as such face props are conserved during mesh mods)
            mat = bpy.data.materials.new(namestr)
            mat.diffuse_color = shmpatchColor(len(obj.data.materials)-1)
            bpy.ops.object.material_slot_add() 
            obj.material_slots[-1].material = mat
        mat['minLevel'] = scn.patchMinLevel
        scn.patchMaxLevel = max(scn.patchMaxLevel, scn.patchMinLevel)
        mat['maxLevel'] = scn.patchMaxLevel
        mat['patchLayers'] = scn.patchLayers
        bpy.ops.object.editmode_toggle()  
        bpy.ops.object.material_slot_assign()
        return {'FINISHED'}

class OBJECT_OT_shmGetPatch(bpy.types.Operator):
    '''Click to select faces belonging to this patch'''
    bl_idname = "set.shmgetpatch"
    bl_label = "Get Patch"
    
    whichPatch = StringProperty()

    def execute(self, context):
        scn = context.scene
        obj = context.active_object
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.wm.context_set_value(data_path="tool_settings.mesh_select_mode", value="(False,False,True)")
        for f in obj.data.faces:
            f.select = False
        mat = bpy.data.materials[self.whichPatch]
        patchindex = list(obj.data.materials).index(mat)
        obj.active_material_index = patchindex
        bpy.ops.object.editmode_toggle()  
        bpy.ops.object.material_slot_select()
        scn.patchMinLevel = mat['minLevel']
        scn.patchMaxLevel =mat['maxLevel']
        scn.patchLayers = mat['patchLayers']
        scn.shmpatchName = self.whichPatch
        return {'FINISHED'}

class OBJECT_OT_writeSHM(bpy.types.Operator):
    '''Write snappyHexMeshDict and associated files for selected object'''
    bl_idname = "write.shmfile"
    bl_label = "Write"
    
    if "bpy" in locals():
        import imp
        if "utils" in locals():
            imp.reload(utils)
        if "blender_utils" in locals():
            imp.reload(blender_utils)
    

    distributeFiles = BoolProperty(name="Distribute",
                         description="Put triSurface dir in ../constant",
                         default=False)

    filepath = StringProperty(
            name="File Path",
            description="Filepath used for exporting the file",
            maxlen=1024,
            subtype='FILE_PATH',
            )
    check_existing = BoolProperty(
            name="Check Existing",
            description="Check and warn on overwriting existing files",
            default=True,
            options={'HIDDEN'},
            )

    def invoke(self, context, event):
        self.filepath = 'snappyHexMeshDict'
        bpy.context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        from . import utils
        import imp
        imp.reload(utils)
        from . import blender_utils
        import os
        scn = context.scene
        stlfiles = []
        eMeshfiles = []
        refinefiles = []
        edgeMesh = {}
        sc = scn.ctmFloat

        path = os.path.dirname(self.filepath)
        if self.distributeFiles:
            pathtrisurface = os.path.join(path,'..','constant','triSurface')
        else:
            pathtrisurface = os.path.join(path,'triSurface')
        if not os.path.exists(pathtrisurface):
            os.makedirs(pathtrisurface)

        geoobj = context.active_object
        geoname = geoobj.name

        bpy.ops.object.mode_set(mode='OBJECT')
        for ob in bpy.data.objects:
            ob.select = False
            
        context.scene.cursor_location = geoobj.location
        try:
            for refreg in geoobj['refreg']:
                refobj = bpy.data.objects[refreg]
                refobj.select = True
                bpy.ops.object.origin_set(type='ORIGIN_CURSOR')  
                filename = refreg + '.stl' 
                refinefiles.append([filename,geoobj['refreg'][refreg]['level'], geoobj['refreg'][refreg]['dist'], geoobj['refreg'][refreg]['inside']])
                filenameandpath = os.path.join(pathtrisurface, filename)
                bpy.ops.object.duplicate(linked=False, mode='INIT')
                bpy.ops.transform.resize(value=(sc,sc,sc))
                bpy.data.objects[refreg].select = True
                refobj.select = False
                bpy.ops.export_mesh.stl(filepath=filenameandpath, check_existing=False, ascii=True, apply_modifiers=True)
                bpy.ops.object.delete()
                refobj.select = False
        except:
            pass
            
        obj = bpy.data.objects[geoname]
        obj.select = True

        try:
            cent = obj.location
            locinmesh = (mathutils.Vector(geoobj['locinmesh'])-cent)*sc + cent
        except:
            locinmesh = (0,0,0)
        
        bpy.ops.object.duplicate(linked=False, mode='INIT')
        bpy.ops.transform.resize(value=(sc,sc,sc))
        obj = context.active_object
        obj.name = 'shmCopyWriteOut'
        bpy.ops.object.duplicate(linked=False, mode='INIT')
        obj = context.active_object
        obj.name = 'edgemesh'
        levelToEdgeMap = {}

        for e in obj.data.edges:
            if e.use_edge_sharp:
                e.select = False
                level = round(e.bevel_weight*100)
                if not level in levelToEdgeMap:
                    levelToEdgeMap[level] = []
                levelToEdgeMap[level].append(e.index)

        bpy.ops.wm.context_set_value(data_path="tool_settings.mesh_select_mode", value="(False,True,False)")

        for level in levelToEdgeMap:
            obj.select = True
            for e in levelToEdgeMap[level]:
                obj.data.edges[e].select = True
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.duplicate(mode='INIT')
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.mode_set(mode='OBJECT')
            eobj = bpy.data.objects['edgemesh.001']
            verts = list(blender_utils.vertices_from_mesh(eobj))
            edges = list(blender_utils.edges_from_mesh(eobj))
            eMeshfiles.append(writeeMeshFile(pathtrisurface,verts,edges,level))
            obj.select = False
            eobj.select = True
            bpy.ops.object.delete()
            obj = bpy.data.objects['edgemesh']
            for e in levelToEdgeMap[level]:
                obj.data.edges[e].select = False
            

        obj = bpy.data.objects['shmCopyWriteOut']
        obj.select = True
        bpy.context.scene.objects.active = obj
        print('active',context.active_object.name)
        for v in obj.data.vertices:
            v.select=True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.wm.context_set_value(data_path="tool_settings.mesh_select_mode", value="(False,False,True)")
        bpy.ops.mesh.separate(type='MATERIAL')
        bpy.ops.object.mode_set(mode='OBJECT')
        print('objects', bpy.data.objects[:])
        for ob in bpy.data.objects:
            ob.select = False
            
        for ob in bpy.data.objects:
            if 'shmCopyWriteOut' in ob.name and len(ob.data.faces) > 0:
                ob.select = True
                matID = ob.data.faces[0].material_index
                mat = obj.data.materials[matID]
                filename = mat.name + '.stl' 
                stlfiles.append([filename,mat['minLevel'], mat['maxLevel'], mat['patchLayers']])
                filenameandpath = os.path.join(pathtrisurface, filename)
                bpy.ops.export_mesh.stl(filepath=filenameandpath, check_existing=False, ascii=True, apply_modifiers=True)
                ob.select = False
                
        for ob in bpy.data.objects:
            if 'shmCopyWriteOut' in ob.name or 'edgemesh' in ob.name:
                ob.select = True
                bpy.ops.object.delete()

        utils.write(self.filepath, obj, stlfiles, refinefiles, eMeshfiles, scn.cast, scn.snap, scn.lays, locinmesh)
        obj = bpy.data.objects[geoname]
        obj.select = True
        bpy.context.scene.objects.active = obj

        if scn.makeBMD:
            verts = []
            matrix = obj.matrix_world.copy()
            cent = obj.location
            for b in obj.bound_box:
                verts.append((matrix*mathutils.Vector(b)-cent)*1.02*sc+cent)
            res = scn.resFloat
            Nx = max(1,round((verts[4] - verts[5]).length / res))
            Ny = max(1,round((verts[5] - verts[6]).length / res))
            Nz = max(1,round((verts[0] - verts[4]).length / res))
            if self.distributeFiles:
                path = os.path.join(path,'..','constant','polyMesh')
                if not os.path.exists(path):
                    os.makedirs(path)
            utils.makeBMD(path, verts, (Nx,Ny,Nz))
        return{'FINISHED'}

initshmProperties()  # Initialize 

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

