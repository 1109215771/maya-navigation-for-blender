bl_info = {
    "name": "Maya Navigation Mode",
    "author": "Your Name",
    "version": (1.2),
    "blender": (3.0, 0),
    "location": "View3D > Header",
    "description": "一键切换 Maya 风格导航，开关关闭时恢复原生操作",
    "category": "Interface",
}

import bpy

# --- 核心逻辑：动态开关快捷键 ---

def toggle_maya_nav_keymaps(is_enabled):
    wm = bpy.context.window_manager
    # 获取插件相关的按键配置
    kc = wm.keyconfigs.addon
    if not kc:
        return

    km = kc.keymaps.get('3D View')
    if km:
        for kmi in km.keymap_items:
            # 找到我们注册的 Alt + 右键 缩放操作
            if kmi.idname == "view3d.zoom" and kmi.type == 'RIGHTMOUSE' and kmi.alt:
                kmi.active = is_enabled

def update_maya_nav(self, context):
    """当顶部按钮被点击时触发"""
    is_enabled = context.scene.maya_nav_enabled
    
    # 1. 切换模拟三键鼠标
    context.preferences.inputs.use_mouse_emulate_3_button = is_enabled
    
    # 2. 切换缩放轴向 (开启时设为水平滑动)
    if is_enabled:
        context.preferences.inputs.view_zoom_axis = 'HORIZONTAL'
    
    # 3. 动态激活/禁用快捷键
    toggle_maya_nav_keymaps(is_enabled)

# --- UI 绘制 ---

def draw_nav_button(self, context):
    layout = self.layout
    scene = context.scene
    
    # 这里的 align=True 保证它能紧凑地排在可见性图标左边
    row = layout.row(align=True)
    # 根据状态切换图标
    icon = 'MOUSE_MOVE' if scene.maya_nav_enabled else 'GHOST_DISABLED'
    row.prop(scene, "maya_nav_enabled", text="Maya Nav", toggle=True, icon=icon)

# --- 注册与注销 ---

def register():
    # 1. 注册场景变量
    bpy.types.Scene.maya_nav_enabled = bpy.props.BoolProperty(
        name="Maya Navigation",
        description="开启后使用 Alt+右键 左右滑动缩放",
        default=False,
        update=update_maya_nav
    )
    
    # 2. 注册快捷键 (初始状态为关闭)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new("view3d.zoom", 'RIGHTMOUSE', 'PRESS', alt=True)
        kmi.active = False # 默认不激活，等待按钮开启
    
    # 3. 添加到顶部栏
    bpy.types.VIEW3D_HT_header.append(draw_nav_button)

def unregister():
    # 清理 UI
    bpy.types.VIEW3D_HT_header.remove(draw_nav_button)
    
    # 清理快捷键
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.get('3D View')
        if km:
            for kmi in km.keymap_items:
                if kmi.idname == "view3d.zoom" and kmi.alt:
                    km.keymap_items.remove(kmi)
    
    # 删除变量
    del bpy.types.Scene.maya_nav_enabled

if __name__ == "__main__":
    register()