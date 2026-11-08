bl_info = {
    "name": "Maya Navigation Mode",
    "author": "Liya",
    "version": (1, 2, 0),
    "blender": (4, 2, 0),
    "location": "Topbar",
    "description": "一键切换 Maya 风格导航，开关关闭时恢复原生操作",
    "category": "Interface",
}

from . import keymap, navigation


def register():
    navigation.register()
    keymap.register()


def unregister():
    keymap.unregister()
    navigation.unregister()
