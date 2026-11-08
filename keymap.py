import bpy


# 插件快捷键分别注册到工具所属模式和关键帧操作适用的模式中。
_KEYMAP_NAME = "3D View"
_FAVORITES_MENU_ID = "SCREEN_MT_user_menu"
_KEYFRAME_OPERATOR_ID = "anim.keyframe_insert_by_name"
_KEYFRAME_MENU_OPERATOR_ID = "anim.keyframe_insert_menu"
_LEGACY_KEYFRAME_OPERATOR_ID = "maya_keymap.insert_transform_keys"
_KEYFRAME_BINDINGS = (
    ("S", False, "LocRotScale"),
    ("W", True, "Location"),
    ("E", True, "Rotation"),
    ("R", True, "Scaling"),
)
_TOOL_KEYMAP_NAMES = (
    "3D View",
    "Object Mode",
    "Mesh",
    "Curve",
    "Curves",
    "Armature",
    "Pose",
    "Lattice",
    "Point Cloud",
    "Metaball",
    "Grease Pencil Edit Mode",
    "Sculpt",
    "Sculpt Curves",
    "Particle",
    "Paint Curve",
    "Mask Editing",
)
_KEYFRAME_KEYMAP_NAMES = ("Object Mode", "Pose")
_TOOLS_BY_KEY = {
    "Q": "builtin.select_box",
    "W": "builtin.move",
    "E": "builtin.rotate",
    "R": "builtin.scale",
}


def _preferences():
    # 使用插件偏好设置保存开关状态，而不是写入场景或 Blender 原生 Keymap。
    addon = bpy.context.preferences.addons.get(__package__)
    if addon:
        return addon.preferences
    return next(
        (
            addon.preferences
            for addon in bpy.context.preferences.addons
            if hasattr(addon.preferences, "maya_keymap_enabled")
        ),
        None,
    )


def _keymap_items(name):
    # 插件 Keymap 会与当前键位方案合并；这里只创建或获取插件自己的映射。
    keyconfig = bpy.context.window_manager.keyconfigs.addon
    if not keyconfig:
        return None

    keymap = keyconfig.keymaps.get(name)
    if not keymap:
        keymap = keyconfig.keymaps.new(
            name=name,
            space_type="VIEW_3D" if name == _KEYMAP_NAME else "EMPTY",
            region_type="WINDOW",
        )
    return keymap


def _is_keyframe_item(item):
    return (
        item.idname == _KEYFRAME_OPERATOR_ID
        and not item.ctrl
        and not item.alt
        and not item.oskey
        and any(
            (item.type, item.shift) == (key, shift)
            and item.properties.type == keying_set
            for key, shift, keying_set in _KEYFRAME_BINDINGS
        )
    )


def _is_legacy_keyframe_menu_item(item):
    return (
        item.idname == _KEYFRAME_MENU_OPERATOR_ID
        and item.properties.always_prompt
        and not item.ctrl
        and not item.alt
        and not item.oskey
        and any(
            (item.type, item.shift) == (key, shift)
            for key, shift, _keying_set in _KEYFRAME_BINDINGS
        )
    )


def _remove_keymaps():
    # 按操作符及按键属性查找旧绑定，避免重复注册时残留插件快捷键。
    keyconfig = bpy.context.window_manager.keyconfigs.addon
    if not keyconfig:
        return

    for keymap in keyconfig.keymaps:
        for item in list(keymap.keymap_items):
            is_tool_item = (
                item.idname == "wm.tool_set_by_id"
                and _TOOLS_BY_KEY.get(item.type) == item.properties.name
            )
            is_favorites_item = (
                item.idname == "wm.call_menu"
                and item.type == "Q"
                and item.shift
                and item.properties.name
                in {_FAVORITES_MENU_ID, "VIEW3D_MT_favorites"}
            )
            is_keyframe_item = (
                item.idname == _LEGACY_KEYFRAME_OPERATOR_ID
                and item.type in {"S", "W", "E", "R"}
            ) or _is_legacy_keyframe_menu_item(item) or _is_keyframe_item(item)
            if is_tool_item or is_favorites_item or is_keyframe_item:
                keymap.keymap_items.remove(item)


def _refresh_keymaps():
    # 偏好设置改变时只切换本插件绑定的 active 状态，不改写 Blender 原生绑定。
    preferences = _preferences()
    if preferences is None:
        return

    addon_keyconfig = bpy.context.window_manager.keyconfigs.addon
    if addon_keyconfig:
        for keymap in addon_keyconfig.keymaps:
            for item in keymap.keymap_items:
                if (
                    item.idname == "wm.tool_set_by_id"
                    and _TOOLS_BY_KEY.get(item.type) == item.properties.name
                ):
                    item.active = preferences.maya_keymap_enabled and preferences.enable_tool_keys
                elif (
                    item.idname == "wm.call_menu"
                    and item.type == "Q"
                    and item.shift
                    and item.properties.name == _FAVORITES_MENU_ID
                ):
                    item.active = preferences.maya_keymap_enabled and preferences.enable_tool_keys
                elif _is_keyframe_item(item):
                    item.active = preferences.maya_keymap_enabled and (
                        preferences.enable_keyframe_all
                        if item.type == "S"
                        else preferences.enable_keyframe_channels
                    )


def _update_keymaps(self, context):
    _refresh_keymaps()


class MAYAKEYMAP_Preferences(bpy.types.AddonPreferences):
    # Blender 按此标识将设置关联到当前插件包。
    bl_idname = __package__

    maya_keymap_enabled: bpy.props.BoolProperty(
        name="Enable Maya Keymap",
        description="Enable Maya-style tool and keyframe shortcuts",
        default=False,
        update=_update_keymaps,
    )
    enable_tool_keys: bpy.props.BoolProperty(
        name="Q/W/E/R Tool Switching",
        default=True,
        update=_update_keymaps,
    )
    enable_keyframe_all: bpy.props.BoolProperty(
        name="S: Key All Transform Channels",
        default=True,
        update=_update_keymaps,
    )
    enable_keyframe_channels: bpy.props.BoolProperty(
        name="Shift+W/E/R: Key Individual Channels",
        default=True,
        update=_update_keymaps,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "maya_keymap_enabled")
        # 总开关关闭时保留子选项状态，但暂时禁用其界面与快捷键。
        column = layout.column()
        column.enabled = self.maya_keymap_enabled
        column.prop(self, "enable_tool_keys")
        column.prop(self, "enable_keyframe_all")
        column.prop(self, "enable_keyframe_channels")


def draw_keymap_button(self, context):
    # 仅在顶部栏左侧绘制一次，避免按钮在右侧区域重复出现。
    if context.region and context.region.alignment == "RIGHT":
        return

    preferences = _preferences()
    if preferences:
        self.layout.row(align=True).prop(
            preferences,
            "maya_keymap_enabled",
            text="Maya Keymap",
            toggle=True,
        )


def register():
    # 先注册偏好设置，再创建依赖它们的 Keymap 项。
    bpy.utils.register_class(MAYAKEYMAP_Preferences)

    # Q/W/E/R 使用 Blender 内置工具；在相关模式映射中添加以覆盖原生同键操作。
    _remove_keymaps()
    for keymap_name in _TOOL_KEYMAP_NAMES:
        keymap = _keymap_items(keymap_name)
        if keymap:
            for key, tool in _TOOLS_BY_KEY.items():
                item = keymap.keymap_items.new(
                    "wm.tool_set_by_id",
                    key,
                    "PRESS",
                )
                item.properties.name = tool

    # 将 Shift+Q 绑定到 Blender 的 Quick Favorites 菜单。
    view_keymap = _keymap_items(_KEYMAP_NAME)
    if view_keymap:
        favorites = view_keymap.keymap_items.new(
            "wm.call_menu",
            "Q",
            "PRESS",
            shift=True,
        )
        favorites.properties.name = _FAVORITES_MENU_ID

    # 使用 Blender 原生按名称插入关键帧操作，直接写入对应通道而不弹出菜单。
    for keymap_name in _KEYFRAME_KEYMAP_NAMES:
        keymap = _keymap_items(keymap_name)
        if keymap:
            for key, shift, keying_set in _KEYFRAME_BINDINGS:
                item = keymap.keymap_items.new(
                    _KEYFRAME_OPERATOR_ID,
                    key,
                    "PRESS",
                    shift=shift,
                )
                item.properties.type = keying_set

    bpy.types.TOPBAR_HT_upper_bar.append(draw_keymap_button)
    _refresh_keymaps()


def unregister():
    # 按注册时的相反顺序清理 UI、插件快捷键和 Blender 类型。
    try:
        bpy.types.TOPBAR_HT_upper_bar.remove(draw_keymap_button)
    except (ValueError, RuntimeError):
        pass

    _remove_keymaps()
    bpy.utils.unregister_class(MAYAKEYMAP_Preferences)
