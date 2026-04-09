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

    km = kc.keymaps.get('Screen')
    if km:
        for kmi in km.keymap_items:
            # 找到我们注册的 Alt + 右键 缩放操作 (3D 和 2D)
            if kmi.type == 'RIGHTMOUSE' and kmi.alt and kmi.idname in {"view3d.zoom", "view2d.zoom"}:
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
    row.prop(scene, "maya_nav_enabled", text="Maya Nav", toggle=True)

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
        # 获取或创建 Screen 键位映射
        km = kc.keymaps.get('Screen')
        if not km:
            km = kc.keymaps.new(name='Screen', space_type='EMPTY')
        # 为 view3d.zoom 注册 ANY 事件
        kmi_3d = km.keymap_items.new("view3d.zoom", 'RIGHTMOUSE', 'PRESS', alt=True)
        kmi_3d.active = True
        # 为 view2d.zoom 注册 ANY 事件
        kmi_2d = km.keymap_items.new("view2d.zoom", 'RIGHTMOUSE', 'ANY', alt=True)
        kmi_2d.active = True # 默认不激活，等待按钮开启
    
    # 3. 添加到顶部栏
    bpy.types.VIEW3D_HT_header.append(draw_nav_button)

def unregister():
    # 清理 UI
    bpy.types.VIEW3D_HT_header.remove(draw_nav_button)
    
    # 清理快捷键 (从 Screen 键位映射中移除我们添加的键位)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.get('Screen')
        if km:
            # 需要复制列表，因为在遍历时删除会改变列表
            kmis_to_remove = []
            for kmi in km.keymap_items:
                if kmi.type == 'RIGHTMOUSE' and kmi.alt and kmi.idname in {"view3d.zoom", "view2d.zoom"}:
                    kmis_to_remove.append(kmi)
            for kmi in kmis_to_remove:
                km.keymap_items.remove(kmi)
    
    # 删除变量
    del bpy.types.Scene.maya_nav_enabled

if __name__ == "__main__":
    register()