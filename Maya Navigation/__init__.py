"""
Maya Style Navigation for Blender
Replaces Ctrl+Middle Mouse zoom with Alt+Right Mouse drag (horizontal drag for zoom)
"""

bl_info = {
    "name": "Maya Style Navigation",
    "author": "Your Name",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Header",
    "description": "Maya-style navigation: Alt+Right Mouse horizontal drag for zoom, auto-enables emulate 3-button mouse",
    "category": "Interface",
}

import bpy
from bpy.app.handlers import persistent
from bpy.types import Operator, Panel, AddonPreferences
from bpy.props import BoolProperty, FloatProperty, EnumProperty
import mathutils


# Global handler for modal operators
_modal_operators = {}


def get_region_under_mouse(context, event):
    """Get the window, area and region under mouse cursor"""
    # Get the area where the mouse is
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type in {'VIEW_3D', 'IMAGE_EDITOR', 'NODE_EDITOR', 'SEQUENCE_EDITOR', 'CLIP_EDITOR', 'DOPESHEET_EDITOR', 'GRAPH_EDITOR', 'NLA_EDITOR', 'TEXT_EDITOR', 'CONSOLE', 'INFO', 'OUTLINER', 'PROPERTIES', 'FILE_BROWSER', 'ASSETS'}:
                for region in area.regions:
                    if region.type == 'WINDOW':
                        # Check if mouse is inside this region
                        if (region.x <= event.mouse_x <= region.x + region.width and
                            region.y <= event.mouse_y <= region.y + region.height):
                            return window, area, region
    return None, None, None


def perform_zoom(window, area, region, factor):
    """Perform zoom operation based on area type - direct manipulation approach"""
    try:
        if area.type == 'VIEW_3D':
            # For 3D view, manipulate view3d region data directly
            space = area.spaces.active
            if hasattr(space, 'region_3d'):
                r3d = space.region_3d
                # Zoom by adjusting view distance
                # Factor positive = zoom in (decrease distance), negative = zoom out (increase distance)
                zoom_speed = 1.2  # Zoom speed multiplier
                
                # Calculate zoom amount
                if factor > 0:
                    # Zoom in
                    r3d.view_distance *= (1.0 / (1.0 + abs(factor) * zoom_speed))
                else:
                    # Zoom out
                    r3d.view_distance *= (1.0 + abs(factor) * zoom_speed)
                
                # Update view matrix
                r3d.view_matrix = r3d.view_matrix
        
        elif area.type == 'IMAGE_EDITOR':
            # For image editor (UV/Texture), adjust zoom directly
            space = area.spaces.active
            if hasattr(space, 'zoom'):
                # Adjust zoom level
                zoom_change = factor * 0.5  # Smaller factor for image editor
                new_zoom = space.zoom * (1.0 + zoom_change)
                # Clamp zoom to reasonable range
                space.zoom = max(0.01, min(100.0, new_zoom))
        
        elif area.type == 'NODE_EDITOR':
            # For node editor, adjust view location and zoom
            space = area.spaces.active
            if hasattr(space, 'cursor_location'):
                # Move cursor location to simulate zoom
                zoom_speed = 10.0
                space.cursor_location.x += factor * zoom_speed
                space.cursor_location.y += factor * zoom_speed
            
            if hasattr(space, 'zoom'):
                # Also adjust zoom if available
                zoom_change = factor * 0.3
                new_zoom = space.zoom * (1.0 + zoom_change)
                space.zoom = max(0.1, min(10.0, new_zoom))
        
        elif area.type in {'SEQUENCE_EDITOR', 'CLIP_EDITOR', 'DOPESHEET_EDITOR', 
                          'GRAPH_EDITOR', 'NLA_EDITOR'}:
            # For 2D editors, adjust view offset and zoom
            space = area.spaces.active
            
            # Try to adjust view offset (pan)
            if hasattr(space, 'cursor_position'):
                zoom_speed = 10.0
                space.cursor_position.x += factor * zoom_speed
                space.cursor_position.y += factor * zoom_speed
            
            # Try to adjust zoom if available
            if hasattr(space, 'zoom'):
                zoom_change = factor * 0.3
                new_zoom = space.zoom * (1.0 + zoom_change)
                space.zoom = max(0.1, min(10.0, new_zoom))
            
            # For Graph Editor, adjust view y-axis
            if area.type == 'GRAPH_EDITOR' and hasattr(space, 'view_offset'):
                zoom_speed = 5.0
                space.view_offset.y += factor * zoom_speed
    
    except Exception as e:
        print(f"Zoom error in {area.type}: {e}")


def get_preferences(context):
    """Get addon preferences"""
    return context.preferences.addons[__name__].preferences


class MAYA_NAV_Preferences(AddonPreferences):
    bl_idname = __name__
    
    enabled: BoolProperty(
        name="Enable Maya Navigation",
        description="Enable Maya-style navigation (Alt+Right Mouse for zoom)",
        default=True,
    )
    
    zoom_sensitivity: FloatProperty(
        name="Zoom Sensitivity",
        description="Zoom sensitivity factor",
        default=1.0,
        min=0.1,
        max=5.0,
        step=0.1,
    )
    
    auto_enable_emulate_3button: BoolProperty(
        name="Auto Enable Emulate 3-Button Mouse",
        description="Automatically enable 'Emulate 3-Button Mouse' in preferences when addon is enabled",
        default=True,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "enabled")
        layout.prop(self, "zoom_sensitivity")
        layout.prop(self, "auto_enable_emulate_3button")


class MAYA_NAV_OT_toggle_enabled(Operator):
    """Toggle Maya navigation on/off"""
    bl_idname = "maya_nav.toggle_enabled"
    bl_label = "Toggle Maya Navigation"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        prefs = get_preferences(context)
        prefs.enabled = not prefs.enabled
        
        if prefs.enabled and prefs.auto_enable_emulate_3button:
            # Enable emulate 3-button mouse
            context.preferences.inputs.use_mouse_emulate_3_button = True
        
        self.report({'INFO'}, 
                   f"Maya Navigation {'Enabled' if prefs.enabled else 'Disabled'}")
        return {'FINISHED'}


class MAYA_NAV_PT_panel(Panel):
    """Panel in 3D Viewport header"""
    bl_label = "Maya Navigation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_ui_units_x = 10
    
    def draw(self, context):
        layout = self.layout
        prefs = get_preferences(context)
        
        row = layout.row(align=True)
        
        # Toggle button
        icon = 'CHECKBOX_HLT' if prefs.enabled else 'CHECKBOX_DEHLT'
        row.operator("maya_nav.toggle_enabled", 
                    text="Maya Nav", 
                    icon=icon,
                    depress=prefs.enabled)
        
        # Settings menu
        row.menu("MAYA_NAV_MT_settings", icon='PREFERENCES')


class MAYA_NAV_MT_settings(bpy.types.Menu):
    bl_label = "Maya Navigation Settings"
    bl_idname = "MAYA_NAV_MT_settings"
    
    def draw(self, context):
        layout = self.layout
        prefs = get_preferences(context)
        
        layout.prop(prefs, "enabled", toggle=True)
        layout.separator()
        layout.prop(prefs, "zoom_sensitivity")
        layout.prop(prefs, "auto_enable_emulate_3button")


# Global handler for mouse events
class MAYA_NAV_OT_modal_zoom(Operator):
    """Modal operator for Maya-style zoom with Alt+Right Mouse"""
    bl_idname = "maya_nav.modal_zoom"
    bl_label = "Maya Zoom"
    
    # Store initial values
    start_x: FloatProperty()
    start_y: FloatProperty()
    sensitivity: FloatProperty(default=1.0)
    
    def modal(self, context, event):
        if not get_preferences(context).enabled:
            return {'CANCELLED'}
        
        # Handle mouse movement for zoom
        if event.type == 'MOUSEMOVE':
            # Calculate horizontal movement
            dx = event.mouse_x - self.start_x
            dy = event.mouse_y - self.start_y
            
            # Horizontal movement for zoom (right = zoom in, left = zoom out)
            zoom_factor = dx * 0.002 * self.sensitivity
            
            # Only perform zoom if there's significant movement
            if abs(zoom_factor) > 0.0001:
                # Get area under mouse
                window, area, region = get_region_under_mouse(context, event)
                if area and region:
                    perform_zoom(window, area, region, zoom_factor)
            
            # Update starting position for smooth continuous movement
            self.start_x = event.mouse_x
            self.start_y = event.mouse_y
        
        # Release right mouse button to stop
        elif event.type == 'RIGHTMOUSE' and event.value == 'RELEASE':
            return {'FINISHED'}
        
        # Escape key to cancel
        elif event.type in {'ESC'}:
            return {'CANCELLED'}
        
        # Keep running while right mouse is held
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        if not get_preferences(context).enabled:
            return {'CANCELLED'}
        
        self.start_x = event.mouse_x
        self.start_y = event.mouse_y
        self.sensitivity = get_preferences(context).zoom_sensitivity
        
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


# Handler to capture mouse events
@persistent
def load_handler(dummy):
    """Handler for file load"""
    pass


# Keymap handler
addon_keymaps = []


def register():
    bpy.utils.register_class(MAYA_NAV_Preferences)
    bpy.utils.register_class(MAYA_NAV_OT_toggle_enabled)
    bpy.utils.register_class(MAYA_NAV_PT_panel)
    bpy.utils.register_class(MAYA_NAV_MT_settings)
    bpy.utils.register_class(MAYA_NAV_OT_modal_zoom)
    
    # Add to header for multiple editor types
    bpy.types.VIEW3D_HT_header.append(draw_header_button)
    bpy.types.IMAGE_HT_header.append(draw_header_button)
    bpy.types.NODE_HT_header.append(draw_header_button)
    bpy.types.SEQUENCER_HT_header.append(draw_header_button)
    bpy.types.CLIP_HT_header.append(draw_header_button)
    bpy.types.DOPESHEET_HT_header.append(draw_header_button)
    bpy.types.GRAPH_HT_header.append(draw_header_button)
    bpy.types.NLA_HT_header.append(draw_header_button)
    
    # Set up keymaps for multiple editors
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        # 3D View
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(
            MAYA_NAV_OT_modal_zoom.bl_idname,
            type='RIGHTMOUSE',
            value='PRESS',
            alt=True
        )
        addon_keymaps.append((km, kmi))
        
        # Image Editor (UV/Texture)
        km = kc.keymaps.new(name='Image', space_type='IMAGE_EDITOR')
        kmi = km.keymap_items.new(
            MAYA_NAV_OT_modal_zoom.bl_idname,
            type='RIGHTMOUSE',
            value='PRESS',
            alt=True
        )
        addon_keymaps.append((km, kmi))
        
        # Node Editor
        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        kmi = km.keymap_items.new(
            MAYA_NAV_OT_modal_zoom.bl_idname,
            type='RIGHTMOUSE',
            value='PRESS',
            alt=True
        )
        addon_keymaps.append((km, kmi))
        
        # Sequence Editor
        km = kc.keymaps.new(name='Sequencer', space_type='SEQUENCE_EDITOR')
        kmi = km.keymap_items.new(
            MAYA_NAV_OT_modal_zoom.bl_idname,
            type='RIGHTMOUSE',
            value='PRESS',
            alt=True
        )
        addon_keymaps.append((km, kmi))
        
        # Movie Clip Editor
        km = kc.keymaps.new(name='Clip', space_type='CLIP_EDITOR')
        kmi = km.keymap_items.new(
            MAYA_NAV_OT_modal_zoom.bl_idname,
            type='RIGHTMOUSE',
            value='PRESS',
            alt=True
        )
        addon_keymaps.append((km, kmi))
        
        # Dopesheet Editor
        km = kc.keymaps.new(name='Dopesheet', space_type='DOPESHEET_EDITOR')
        kmi = km.keymap_items.new(
            MAYA_NAV_OT_modal_zoom.bl_idname,
            type='RIGHTMOUSE',
            value='PRESS',
            alt=True
        )
        addon_keymaps.append((km, kmi))
        
        # Graph Editor
        km = kc.keymaps.new(name='Graph Editor', space_type='GRAPH_EDITOR')
        kmi = km.keymap_items.new(
            MAYA_NAV_OT_modal_zoom.bl_idname,
            type='RIGHTMOUSE',
            value='PRESS',
            alt=True
        )
        addon_keymaps.append((km, kmi))
        
        # NLA Editor
        km = kc.keymaps.new(name='NLA Editor', space_type='NLA_EDITOR')
        kmi = km.keymap_items.new(
            MAYA_NAV_OT_modal_zoom.bl_idname,
            type='RIGHTMOUSE',
            value='PRESS',
            alt=True
        )
        addon_keymaps.append((km, kmi))
    
    # Enable emulate 3-button mouse if preference is set
    prefs = bpy.context.preferences.addons[__name__].preferences
    if prefs.enabled and prefs.auto_enable_emulate_3button:
        bpy.context.preferences.inputs.use_mouse_emulate_3_button = True


def unregister():
    # Remove from all headers
    bpy.types.VIEW3D_HT_header.remove(draw_header_button)
    bpy.types.IMAGE_HT_header.remove(draw_header_button)
    bpy.types.NODE_HT_header.remove(draw_header_button)
    bpy.types.SEQUENCER_HT_header.remove(draw_header_button)
    bpy.types.CLIP_HT_header.remove(draw_header_button)
    bpy.types.DOPESHEET_HT_header.remove(draw_header_button)
    bpy.types.GRAPH_HT_header.remove(draw_header_button)
    bpy.types.NLA_HT_header.remove(draw_header_button)
    
    # Remove keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
    bpy.utils.unregister_class(MAYA_NAV_OT_modal_zoom)
    bpy.utils.unregister_class(MAYA_NAV_MT_settings)
    bpy.utils.unregister_class(MAYA_NAV_PT_panel)
    bpy.utils.unregister_class(MAYA_NAV_OT_toggle_enabled)
    bpy.utils.unregister_class(MAYA_NAV_Preferences)


def draw_header_button(self, context):
    """Draw button in 3D view header"""
    layout = self.layout
    prefs = get_preferences(context)
    
    row = layout.row(align=True)
    
    # Toggle button
    icon = 'CHECKBOX_HLT' if prefs.enabled else 'CHECKBOX_DEHLT'
    row.operator("maya_nav.toggle_enabled", 
                text="", 
                icon=icon,
                depress=prefs.enabled)


if __name__ == "__main__":
    register()