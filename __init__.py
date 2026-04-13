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

    # 3D View 键位映射（用于 3D 操作）
    km_3dview = kc.keymaps.get('3D View')
    if km_3dview:
        for kmi in km_3dview.keymap_items:
            # 找到我们注册的 Alt + 右键 缩放操作 (3D)
            if kmi.type == 'RIGHTMOUSE' and kmi.alt and kmi.idname == "view3d.zoom":
                kmi.active = is_enabled
            # 找到我们注册的 Alt + 中键 平移操作 (3D)
            if kmi.type == 'MIDDLEMOUSE' and kmi.alt and not kmi.ctrl and kmi.idname == "view3d.move":
                kmi.active = is_enabled
            # 找到我们注册的 Alt + Ctrl + 中键 切换正交视图操作 (四个方向)
            if kmi.type == 'MIDDLEMOUSE' and kmi.alt and kmi.ctrl and kmi.idname == "view3d.view_axis":
                kmi.active = is_enabled
    
    # View2D 键位映射（用于 2D 平移和缩放）
    km_view2d = kc.keymaps.get('View2D')
    if km_view2d:
        for kmi in km_view2d.keymap_items:
            # 找到我们注册的 Alt + 右键 缩放操作 (2D)
            if kmi.type == 'RIGHTMOUSE' and kmi.alt and kmi.idname == "view2d.zoom":
                kmi.active = is_enabled
            # 找到我们注册的 Alt + 中键 平移操作 (2D)
            if kmi.type == 'MIDDLEMOUSE' and kmi.alt and not kmi.ctrl and kmi.idname == "view2d.pan":
                kmi.active = is_enabled
    
    # Image 键位映射（用于图像平移和缩放）
    km_image = kc.keymaps.get('Image')
    if km_image:
        for kmi in km_image.keymap_items:
            # 找到我们注册的 Alt + 右键 缩放操作 (Image)
            if kmi.type == 'RIGHTMOUSE' and kmi.alt and kmi.idname == "image.view_zoom":
                kmi.active = is_enabled
            # 找到我们注册的 Alt + 中键 平移操作 (Image)
            if kmi.type == 'MIDDLEMOUSE' and kmi.alt and not kmi.ctrl and kmi.idname == "image.view_pan":
                kmi.active = is_enabled
    
    # Frames 键位映射（用于帧操作）
    km_frames = kc.keymaps.get('Frames')
    if km_frames:
        for kmi in km_frames.keymap_items:
            # 找到我们注册的 ALT+Q 和 ALT+E 关键帧跳转操作
            if kmi.type in ['Q', 'E'] and kmi.alt and kmi.idname == "screen.keyframe_jump":
                kmi.active = is_enabled
    
    # Animation 键位映射（用于动画操作）
    km_anim_channels = kc.keymaps.get('Animation')
    if km_anim_channels:
        for kmi in km_anim_channels.keymap_items:
            # 找到我们注册的 SHIFT+空格键 时间线跳转操作
            if kmi.type == 'SPACE' and kmi.shift and kmi.idname == "screen.frame_jump":
                kmi.active = is_enabled
            # 找到我们注册的 ALT+S 饼菜单调用操作
            if kmi.type == 'S' and kmi.alt and kmi.idname == "wm.call_menu_pie":
                kmi.active = is_enabled
    
    # Window 键位映射（用于窗口操作）
    km_window = kc.keymaps.get('Window')
    if km_window:
        for kmi in km_window.keymap_items:
            # 找到我们注册的 D 键变换原点操作
            if kmi.type == 'D' and kmi.idname == "wm.context_toggle" and kmi.properties.data_path == "scene.tool_settings.use_transform_data_origin":
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
        description="开启后使用 Alt+右键 左右滑动缩放，Alt+中键平移视图，Alt+Ctrl+中键切换正交视图",
        default=True,
        update=update_maya_nav
    )
    
    # 2. 注册快捷键 (初始状态为关闭)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:  
        # 获取或创建 3D View 键位映射（用于 3D 操作）
        km_3dview = kc.keymaps.get('3D View')
        if not km_3dview:
            km_3dview = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        # 为 view3d.move 注册 ANY 事件 (Alt+中键)
        kmi_pan_3d = km_3dview.keymap_items.new("view3d.move", 'MIDDLEMOUSE', 'CLICK_DRAG', alt=True)
        kmi_pan_3d.active = True
        # 为 view3d.zoom 注册 ANY 事件 (Alt+右键)
        kmi_zoom_3d = km_3dview.keymap_items.new("view3d.zoom", 'RIGHTMOUSE', 'PRESS', alt=True)
        kmi_zoom_3d.active = True

        # 上视图 (NORTH)
        kmi_view_top = km_3dview.keymap_items.new("view3d.view_axis", 'MIDDLEMOUSE', 'CLICK_DRAG', alt=True, ctrl=True)
        # 注意：direction 是 kmi 对象的成员，控制触发条件
        kmi_view_top.direction = 'NORTH' 
        # 注意：type 是操作符 view3d.view_axis 的内部参数
        kmi_view_top.properties.type = 'TOP'
        kmi_view_top.properties.relative = True  # 勾选“相对”选项
        kmi_view_top.active = True

        # 下视图 (SOUTH)
        kmi_view_bottom = km_3dview.keymap_items.new("view3d.view_axis", 'MIDDLEMOUSE', 'CLICK_DRAG', alt=True, ctrl=True)
        kmi_view_bottom.direction = 'SOUTH'
        kmi_view_bottom.properties.type = 'BOTTOM'
        kmi_view_bottom.properties.relative = True  # 勾选“相对”选项
        kmi_view_bottom.active = True

        # 右视图 (EAST)
        kmi_view_right = km_3dview.keymap_items.new("view3d.view_axis", 'MIDDLEMOUSE', 'CLICK_DRAG', alt=True, ctrl=True)
        kmi_view_right.direction = 'EAST'
        kmi_view_right.properties.type = 'RIGHT'
        kmi_view_right.properties.relative = True  # 勾选“相对”选项
        kmi_view_right.active = True

        # 左视图 (WEST)
        kmi_view_left = km_3dview.keymap_items.new("view3d.view_axis", 'MIDDLEMOUSE', 'CLICK_DRAG', alt=True, ctrl=True)
        kmi_view_left.direction = 'WEST'
        kmi_view_left.properties.type = 'LEFT'
        kmi_view_left.properties.relative = True  # 勾选“相对”选项
        kmi_view_left.active = True
        
        # 获取或创建 View2D 键位映射 (用于 2D 平移和缩放)
        km_view2d = kc.keymaps.get('View2D')
        if not km_view2d:
            km_view2d = kc.keymaps.new(name='View2D', space_type='EMPTY')
        # 为 view2d.pan 注册 ANY 事件 (Alt+中键)
        kmi_pan_2d = km_view2d.keymap_items.new("view2d.pan", 'MIDDLEMOUSE', 'CLICK_DRAG', alt=True)
        kmi_pan_2d.active = True
        # 为 view2d.zoom 注册 ANY 事件 (Alt+右键)
        kmi_zoom_2d = km_view2d.keymap_items.new("view2d.zoom", 'RIGHTMOUSE', 'PRESS', alt=True)
        kmi_zoom_2d.active = True
        
        # 获取或创建 Image 键位映射 (用于图像平移和缩放)
        km_image = kc.keymaps.get('Image')
        if not km_image:
            km_image = kc.keymaps.new(name='Image', space_type='IMAGE_EDITOR')
        # 为 image.view_pan 注册 ANY 事件 (Alt+中键)
        kmi_pan_image = km_image.keymap_items.new("image.view_pan", 'MIDDLEMOUSE', 'CLICK_DRAG', alt=True)
        kmi_pan_image.active = True
        # 为 image.view_zoom 注册 ANY 事件 (Alt+右键)
        kmi_zoom_image = km_image.keymap_items.new("image.view_zoom", 'RIGHTMOUSE', 'PRESS', alt=True)
        kmi_zoom_image.active = True
        
        # 添加 Frames 键位映射 (帧的类别)
        km_frames = kc.keymaps.get('Frames')
        if not km_frames:
            km_frames = kc.keymaps.new(name='Frames', space_type='EMPTY')
        
        # 为 screen.keyframe_jump 注册 ALT+Q (上一个关键帧)
        kmi_keyframe_prev = km_frames.keymap_items.new("screen.keyframe_jump", 'Q', 'PRESS', alt=True)
        kmi_keyframe_prev.properties.next = False  # 上一个关键帧
        kmi_keyframe_prev.active = True
        
        # 为 screen.keyframe_jump 注册 ALT+E (下一个关键帧)
        kmi_keyframe_next = km_frames.keymap_items.new("screen.keyframe_jump", 'E', 'PRESS', alt=True)
        kmi_keyframe_next.properties.next = True   # 下一个关键帧
        kmi_keyframe_next.active = True

        
        # 添加 Animation 键位映射 (动画的类别)
        km_anim_channels = kc.keymaps.get('Animation')
        if not km_anim_channels:
            km_anim_channels = kc.keymaps.new(name='Animation', space_type='EMPTY')
        
        # 为 screen.frame_jump 注册 SHIFT+空格键 (跳转到时间线开始)
        kmi_frame_start = km_anim_channels.keymap_items.new("screen.frame_jump", 'SPACE', 'PRESS', shift=True)
        kmi_frame_start.properties.end = False  # 跳转到开始
        kmi_frame_start.active = True
        
        # 为 wm.call_menu_pie 注册 ALT+S (调用关键帧插入饼菜单)
        kmi_pie_menu = km_anim_channels.keymap_items.new("wm.call_menu_pie", 'S', 'PRESS', alt=True)
        kmi_pie_menu.properties.name = "ANIM_MT_keyframe_insert_pie"  # 饼菜单名称
        kmi_pie_menu.active = True
        
        # 添加 Window 键位映射 (窗口类别)
        km_window = kc.keymaps.get('Window')
        if not km_window:
            km_window = kc.keymaps.new(name='Window', space_type='EMPTY')
        
        # 为 scene.tool_settings.use_transform_data_origin 注册 D 键
        # 第一行：操作符类别 wm.context_toggle
        # 第二行：具体命令 scene.tool_settings.use_transform_data_origin
        kmi_transform_origin = km_window.keymap_items.new("wm.context_toggle", 'D', 'PRESS')
        kmi_transform_origin.properties.data_path = "scene.tool_settings.use_transform_data_origin"
        kmi_transform_origin.active = True
    
    # 3. 添加到顶部栏
    bpy.types.VIEW3D_HT_header.append(draw_nav_button)

def unregister():
    # 清理 UI
    bpy.types.VIEW3D_HT_header.remove(draw_nav_button)
    
    # 清理快捷键 (从 3D View 和 View2D 键位映射中移除我们添加的键位)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        # 清理 3D View 键位映射 (3D 平移、缩放和正交视图切换)
        km_3dview = kc.keymaps.get('3D View')
        if km_3dview:
            kmis_to_remove = []
            for kmi in km_3dview.keymap_items:
                if (kmi.type == 'RIGHTMOUSE' and kmi.alt and kmi.idname == "view3d.zoom") or \
                   (kmi.type == 'MIDDLEMOUSE' and kmi.alt and not kmi.ctrl and kmi.idname == "view3d.move") or \
                   (kmi.type == 'MIDDLEMOUSE' and kmi.alt and kmi.ctrl and kmi.idname == "view3d.view_axis"):
                    kmis_to_remove.append(kmi)
            for kmi in kmis_to_remove:
                km_3dview.keymap_items.remove(kmi)
        
        # 清理 View2D 键位映射 (2D 平移和缩放)
        km_view2d = kc.keymaps.get('View2D')
        if km_view2d:
            kmis_to_remove = []
            for kmi in km_view2d.keymap_items:
                if (kmi.type == 'RIGHTMOUSE' and kmi.alt and kmi.idname == "view2d.zoom") or \
                   (kmi.type == 'MIDDLEMOUSE' and kmi.alt and not kmi.ctrl and kmi.idname == "view2d.pan"):
                    kmis_to_remove.append(kmi)
            for kmi in kmis_to_remove:
                km_view2d.keymap_items.remove(kmi)
        
        # 清理 Image 键位映射 (图像平移和缩放)
        km_image = kc.keymaps.get('Image')
        if km_image:
            kmis_to_remove = []
            for kmi in km_image.keymap_items:
                if (kmi.type == 'RIGHTMOUSE' and kmi.alt and kmi.idname == "image.view_zoom") or \
                   (kmi.type == 'MIDDLEMOUSE' and kmi.alt and not kmi.ctrl and kmi.idname == "image.view_pan"):
                    kmis_to_remove.append(kmi)
            for kmi in kmis_to_remove:
                km_image.keymap_items.remove(kmi)
        
        # 清理 Frames 键位映射 (帧操作)
        km_frames = kc.keymaps.get('Frames')
        if km_frames:
            kmis_to_remove = []
            for kmi in km_frames.keymap_items:
                # 找到我们注册的 ALT+Q 和 ALT+E 关键帧跳转操作
                if kmi.type in ['Q', 'E'] and kmi.alt and kmi.idname == "screen.keyframe_jump":
                    kmis_to_remove.append(kmi)

            for kmi in kmis_to_remove:
                km_frames.keymap_items.remove(kmi)
        
        # 清理 Animation Channels 键位映射 (动画操作)
        km_anim_channels = kc.keymaps.get('Animation')
        if km_anim_channels:
            kmis_to_remove = []
            for kmi in km_anim_channels.keymap_items:
                # 找到我们注册的 SHIFT+空格键 时间线跳转操作
                if kmi.type == 'SPACE' and kmi.shift and kmi.idname == "screen.frame_jump":
                    kmis_to_remove.append(kmi)

                # 找到我们注册的 ALT+S 饼菜单调用操作
                if kmi.type == 'S' and kmi.alt and kmi.idname == "wm.call_menu_pie":
                    kmis_to_remove.append(kmi)
            for kmi in kmis_to_remove:
                km_anim_channels.keymap_items.remove(kmi)
        
        # 清理 Window 键位映射 (窗口操作)
        km_window = kc.keymaps.get('Window')
        if km_window:
            kmis_to_remove = []
            for kmi in km_window.keymap_items:
                # 找到我们注册的 D 键变换原点操作
                if kmi.type == 'D' and kmi.idname == "wm.context_toggle" and kmi.properties.data_path == "scene.tool_settings.use_transform_data_origin":
                    kmis_to_remove.append(kmi)
            for kmi in kmis_to_remove:
                km_window.keymap_items.remove(kmi)
    
    # 删除变量
    del bpy.types.Scene.maya_nav_enabled

if __name__ == "__main__":
    register()