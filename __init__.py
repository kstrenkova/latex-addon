bl_info = {
    "name": "Latex Text Generator",
    "author": "Katarina Strenkova",
    "version": (1, 0, 1),
    "blender": (3, 3, 0),
    "location": "3D Viewport",
    "description": "Addon generates editable 3D text from Latex notation.",
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
    importlib.reload(ui)
    importlib.reload(characters_db)
    importlib.reload(ll_table)
else:
    from .src import generator
    from .src import lexical_analyser
    from .src import syntax_analyser
    from .src import syntax_analyser_math
    from .src import ui
    from .data import characters_db
    from .data import ll_table


# register
def register():
    ui.register()


# unregister
def unregister():
    ui.unregister()


if __name__ == "__main__":
    register()



