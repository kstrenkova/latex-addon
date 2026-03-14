bl_info = {
    "name": "LaTeX Text Generator",
    "author": "Katarina Strenkova",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "3D Viewport",
    "description": "Generate customizable 3D text from LaTeX notation",
    "warning": "",
    "doc_url": "",
    "category": "Object",
}


if "bpy" in locals():
    import importlib
    importlib.reload(generator)
    importlib.reload(lexical_analyser)
    importlib.reload(syntax_analyser)
    importlib.reload(syntax_analyser_math)
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(panels)
    importlib.reload(characters_db)
    importlib.reload(ll_table)
else:
    from .src import generator
    from .src import lexical_analyser
    from .src import syntax_analyser
    from .src import syntax_analyser_math
    from .src import properties
    from .src import operators
    from .src import panels
    from .src.data import characters_db
    from .src.data import ll_table

import bpy


classes = [
    properties.LATEX_PG_Properties,
    panels.OBJECT_PT_ME,
    panels.TEXT_PT_LaTeXEditor,
    operators.TEXT_OT_EditText,
    operators.TEXT_OT_SaveAndReturn,
    operators.WM_OT_LoadFont,
    operators.WM_OT_ResetParameters,
    operators.WM_OT_AddText,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.custom_prop = bpy.props.PointerProperty(
        type=properties.LATEX_PG_Properties
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.custom_prop


if __name__ == "__main__":
    register()
