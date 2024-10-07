from enum import Enum


class CameraType(Enum):
    EQUIDISTANT = "equidistant"
    EQUISOLID = "equisolid"
    ORTHOGRAPHIC = "orthographic"
    STEREOGRAPHIC = "stereographic"


class FisheyeFormat(Enum):
    CIRCULAR = "circular"
    DIAGONAL = "diagonal"
