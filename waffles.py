# -*- coding: utf-8 -*-
"""
Created on Mon Oct  1 12:28:51 2018

@author: Waffletron
"""

import bpy
import os

from bpy.props import (
        EnumProperty,
        PointerProperty,
)

from bpy.types import (
        PropertyGroup,
        Operator,
        Panel,
)


bl_info = {
    "name": 'Waffles',
    "description": "Useful tools for exporting to FBX",
    "author": "Waffletron (James Theiring)",
    "blender": (2, 7, 9),
    "version": (1, 1, 0),
    "category": "Unity",
    "support": 'TESTING',
    "location": "",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
}

class Props(PropertyGroup):

    waffles_export_path = bpy.props.StringProperty (
        name='Path',
        default='//export\\',
        description='Path to export directory',
        subtype='DIR_PATH'
    )

    waffles_export_file_suffix = bpy.props.StringProperty (
        name='Filename Suffix',
        default='',
        description='Append to filename (prior to extension)',
        subtype='NONE'
    )

    # Cluster options:
    waffles_cluster_groups = bpy.props.BoolProperty (
        name="Cluster Groups",
        default=True,
        description="Export grouped objects",
        subtype='NONE'
    )
    waffles_cluster_parents = bpy.props.BoolProperty (
        name="Cluster Parent/Child",
        default=False,
        description="Export parent/child objects",
        subtype='NONE'
    )
    waffles_cluster_individual = bpy.props.BoolProperty (
        name="Include Individuals",
        default=True,
        description="Export parent/child objects",
        subtype='NONE'
    )

    priority_type = EnumProperty(
            name = "Hierarchy Type",
            items = (
                    ('GROUP',        'Group',                   "", 1),
                    ('PARENT',       'Parent',                  "", 2),
                    ('INDIVIDUAL',   'Individual (OVERRIDE)',   "", 0),
            ),
            default = 'GROUP'
    )

    # Transformations (NOT IMPLEMENTED)
    waffles_transform_origin = bpy.props.BoolProperty (
        name="Global Origin",
        default=False,
        description="Set origin to global coordinate (0,0,0)",
        subtype='NONE'
    )
    waffles_transform_apply_scale = bpy.props.BoolProperty (
        name="Apply Scale Transforms",
        default=False,
        description="Apply Scale Transforms",
        subtype='NONE'
    )
    waffles_transform_apply_rotation = bpy.props.BoolProperty (
        name="Apply Rotation Transforms",
        default=False,
        description="Apply Rotation Transforms",
        subtype='NONE'
    )
    waffles_transform_apply_position = bpy.props.BoolProperty (
        name="Apply Position Transforms",
        default=False,
        description="Apply Position Transforms",
        subtype='NONE'
    )


class WafflesPanel(Panel):

    bl_idname = 'waffles.panel'
    bl_label = 'Waffles'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = 'objectmode'

    def draw(self, context):

        waffles = context.scene.waffles
        layout = self.layout

        # Export
        row = layout.row()
        box = row.box()

        box.label("Directory Options")
        box.prop(waffles, 'waffles_export_path')
        box.prop(waffles, 'waffles_export_file_suffix')

        row = layout.row()
        box = row.box()
        box.label("Export Options")

        # cluster options
        box.prop(waffles, 'waffles_cluster_groups',
                 text="Cluster Groups")
        box.prop(waffles, 'waffles_cluster_parents',
                 text="Cluster Parents")
        box.prop(waffles, 'waffles_cluster_individual',
                 text="Include Individuals")

        box.prop(waffles, 'priority_type', text="Priority")

        # Transforms:

        row = layout.row()
        box = row.box()
        box.label("Apply Transforms")
        box.prop(waffles, 'waffles_transform_origin')
        box.prop(waffles, 'waffles_transform_apply_scale')
        box.prop(waffles, 'waffles_transform_apply_rotation')
        box.prop(waffles, 'waffles_transform_apply_position')

        # Export button
        row = layout.row()
        row.operator('waffles.export', text='Export', icon='EXPORT')


class WafflesExport(Operator):

    bl_idname = 'waffles.export'
    bl_label = 'Execute export operation'

    GROUP_APPEND_FILENAME = "-group-"

    def export_selected_meshes(self, name):
        '''
        export_selected_meshes(self, name)
            - export all selected  meshes

            name: string identifier for file
        '''
        waffles = bpy.context.scene.waffles

        name = bpy.path.clean_name(
                name + waffles.waffles_export_file_suffix)

        directory = os.path.dirname(
                bpy.path.abspath(
                        waffles.waffles_export_path))

        if not os.path.isdir(directory):
            raise Exception("Directory does not exist: {0}".format(directory))

        filename = os.path.join(directory, name)
        print("exporting: " + filename)

        # Export to .FBX
        # TODO: create single {} block assignment for export_args
        export_args = {}
        export_args['filepath'] = filename + ".fbx"
        export_args['use_selection'] = True
        export_args['axis_forward'] = '-Z'
        export_args['axis_up'] = 'Y'
        export_args['apply_unit_scale'] = False
        export_args['apply_scale_options'] = 'FBX_SCALE_UNITS'
        bpy.ops.export_scene.fbx(**export_args)


    def select_children(self, parent, objects):
        '''
        select_children(self, parent, objects)
            Returns: List of objects (parent + children)
        '''

        # Notes:
        #   - Circular parent loops are intrinsically prevented by Blender.
        #   - No additional checks are made to prevent infinite recursion

        obj_list = [parent]
        for obj in objects:
            if obj.parent==parent:
                obj.select = True
                obj_list.append(obj)
                obj_list.extend(self.select_children(obj, objects))

        return obj_list

    # TODO: reduce conditional nesting for following export_* methods
    # TODO: seen_objects is not required, remove obj from objects when seen
    def export_groups(self, objects):
        '''
        export_groups(self, objects)
            objects: List of remaining objects to export from
            - each exported object is removed from the list
        '''
        if bpy.context.scene.waffles.waffles_cluster_groups:
            seen_objects = []  # Note: groups may overlap
            groups = bpy.data.groups
            for gr in groups:
                bpy.ops.object.select_all(action='DESELECT')
                for obj in gr.objects:
                    seen_objects.append(obj)
                    obj.select = True

                self.export_selected_meshes(
                        gr.name
                        + self.GROUP_APPEND_FILENAME
                        )

            for seen_obj in seen_objects:
                if seen_obj in objects:
                    objects.remove(seen_obj)

            return len(groups)

        else:
            return None

    def export_parents(self, objects):
        if bpy.context.scene.waffles.waffles_cluster_parents:
            seen_objects = []  # Note: groups may overlap
            parents = [ob.parent for ob in objects if ob.parent]
            # remove non-root parents:
            parents = [pn for pn in parents if pn.parent not in parents]
            for parent in parents:
                bpy.ops.object.select_all(action='DESELECT')
                parent.select = True
                selected = self.select_children(parent, objects)
                self.export_selected_meshes(parent.name)

                for sel in selected:
                    seen_objects.append(sel)

            for seen_obj in seen_objects:
                if seen_obj in objects:
                    objects.remove(seen_obj)

            return len(parents)
        else:
            return None

    def export_individuals(self, objects):
        # Export individual meshes

        if bpy.context.scene.waffles.waffles_cluster_individual:
            for obj in objects:
                bpy.ops.object.select_all(action='DESELECT')
                obj.select = True
                self.export_selected_meshes(obj.name)

            # TODO: determine need to remove obj from objects upon export

            return len(objects)

        else:
            return None


    def execute(self, context):

        print("***** WafflesExport.execute() *****")

        waffles = bpy.context.scene.waffles

        directory = os.path.dirname(bpy.data.filepath)
        if not directory:
            raise Exception("Blend file is not saved.")
        if not waffles.waffles_export_path:
            raise Exception("Export path not set")

        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_by_type(type='MESH')

        objects = bpy.context.selected_objects
        qty_groups = qty_parents = qty_individuals = 0

        # A note about the following conditionals:
        # - Each method removes applicable objects from List supplied
        # - The sequence of the methods thus determines the hierarchy priority

        if waffles.priority_type == 'GROUP':
            # Prioritize: Group, Parent, Individual
            qty_groups = self.export_groups(objects)
            qty_parents = self.export_parents(objects)
            qty_individuals = self.export_individuals(objects)

        elif waffles.priority_type == 'PARENT':
            # Prioritize: Parent, Group, Individual
            qty_parents = self.export_parents(objects)
            qty_groups = self.export_groups(objects)
            qty_individuals = self.export_individuals(objects)

        elif waffles.priority_type == 'INDIVIDUAL':
            # Export Individual only
            qty_individuals = self.export_individuals(objects)

        print("COUNTS -- individuals: {0}, groups: {1}, parent relations: {2}"\
              .format(qty_individuals, qty_groups, qty_parents))

        return {'FINISHED'}


# Register/Deregister:

waffle_classes = [WafflesPanel, WafflesExport, Props]

def register():
    print("Registering Waffles add-on")
    for waffle_class in waffle_classes:
        bpy.utils.register_class(waffle_class)
    bpy.types.Scene.waffles = PointerProperty(type=Props)


def unregister():
    print("Unregistering Waffles add-on")
    for waffle_class in waffle_classes:
        bpy.utils.unregister_class(waffle_class)

    del bpy.types.Scene.waffles


if __name__ == "__main__":
    register()