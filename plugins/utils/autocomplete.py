import novus as n

from .poo_objects import PoopEnum, Volume, Texture, Shape, Feel, Color, Smell

def get_enum_options(enum: PoopEnum):
    return [
        n.ApplicationCommandChoice(
            name=repr(e),
            value=e.value
        )
        for e in enum # type: ignore
    ]

VOLUME_OPTIONS = get_enum_options(Volume) # type: ignore
TEXTURE_OPTIONS = get_enum_options(Texture) # type: ignore
SHAPE_OPTIONS = get_enum_options(Shape) # type: ignore
FEEL_OPTIONS = get_enum_options(Feel) # type: ignore
COLOR_OPTIONS = get_enum_options(Color) # type: ignore
SMELL_OPTIONS = get_enum_options(Smell) # type: ignore
BOOLEAN_OPTIONS = [
    n.ApplicationCommandChoice(
        name="Yes",
        value=1
    ),
    n.ApplicationCommandChoice(
        name="No",
        value=-1
    )
]