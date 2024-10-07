from abc import ABC, abstractmethod

import numpy as np

from fisheye.schemas import CameraType


class FisheyeCamera(ABC):
    """Abstract base class for fisheye camera models.

    The fisheye camera model is defined by the mapping between the angle theta and
    the radius r. The mapping is defined by the specific fisheye camera model.
    """

    def __init__(self) -> None:
        pass

    @abstractmethod
    def theta_to_r(self, theta: np.ndarray) -> np.ndarray:
        """Convert angle theta to radius r."""
        pass

    @abstractmethod
    def r_to_theta(self, r: np.ndarray) -> np.ndarray:
        """Convert radius r to angle theta."""
        pass

    @property
    @abstractmethod
    def focal_length(self) -> float:
        """Focal length of the camera."""
        pass

    @staticmethod
    @abstractmethod
    def f_from_theta_and_r(theta_max: float, r_max: float) -> float:
        """Compute the focal length from the maximum angle theta and radius r."""
        pass


class EquidistantCamera(FisheyeCamera):
    """Equidistant fisheye camera model.

    The equidistant camera model is defined by the mapping between the angle theta and
    the radius r. The mapping is defined as r = f * theta, where f is the focal length.
    """

    def __init__(self, focal_length: float) -> None:
        super().__init__()
        self._focal_length = focal_length

    def theta_to_r(self, theta: np.ndarray) -> np.ndarray:
        return self._focal_length * theta

    def r_to_theta(self, r: np.ndarray) -> np.ndarray:
        return r / self._focal_length

    @property
    def focal_length(self) -> float:
        return self._focal_length

    @staticmethod
    def f_from_theta_and_r(theta_max: float, r_max: float) -> float:
        return r_max / theta_max


class EquisolidCamera(FisheyeCamera):
    """Equisolid fisheye camera model.

    The equisolid camera model is defined by the mapping between the angle theta and
    the radius r. The mapping is defined as r = 2 * f * sin(theta / 2), where f is the
    focal length.
    """

    def __init__(self, focal_length: float) -> None:
        super().__init__()
        self._focal_length = focal_length

    def theta_to_r(self, theta: np.ndarray) -> np.ndarray:
        return 2 * self._focal_length * np.sin(theta / 2)

    def r_to_theta(self, r: np.ndarray) -> np.ndarray:
        return 2 * np.arcsin(r / (2 * self._focal_length))

    @property
    def focal_length(self) -> float:
        return self._focal_length

    @staticmethod
    def f_from_theta_and_r(theta_max: float, r_max: float) -> float:
        return r_max / (2 * np.sin(theta_max / 2))


class OrthographicCamera(FisheyeCamera):
    """Orthographic fisheye camera model.

    The orthographic camera model is defined by the mapping between the angle theta and
    the radius r. The mapping is defined as r = f * sin(theta), where f is the focal
    length.
    """

    def __init__(self, focal_length: float) -> None:
        super().__init__()
        self._focal_length = focal_length

    def theta_to_r(self, theta: np.ndarray) -> np.ndarray:
        return self._focal_length * np.sin(theta)

    def r_to_theta(self, r: np.ndarray) -> np.ndarray:
        return np.arcsin(r / self._focal_length)

    @property
    def focal_length(self) -> float:
        return self._focal_length

    @staticmethod
    def f_from_theta_and_r(theta_max: float, r_max: float) -> float:
        return r_max / np.sin(theta_max)


class StereographicCamera(FisheyeCamera):
    """Stereographic fisheye camera model.

    The stereographic camera model is defined by the mapping between the angle theta and
    the radius r. The mapping is defined as r = 2 * f * tan(theta / 2), where f is the
    focal length.
    """

    def __init__(self, focal_length: float) -> None:
        super().__init__()
        self._focal_length = focal_length

    def theta_to_r(self, theta: np.ndarray) -> np.ndarray:
        return 2 * self._focal_length * np.tan(theta / 2)

    def r_to_theta(self, r: np.ndarray) -> np.ndarray:
        return 2 * np.arctan(r / (2 * self._focal_length))

    @property
    def focal_length(self) -> float:
        return self._focal_length

    @staticmethod
    def f_from_theta_and_r(theta_max: float, r_max: float) -> float:
        return r_max / (2 * np.tan(theta_max / 2))


class FisheyeCameraFactory:
    """Factory class for creating fisheye cameras."""

    @staticmethod
    def create_camera(camera_type: CameraType, focal_length: float) -> FisheyeCamera:
        """Create a fisheye camera of the specified type."""
        if camera_type == CameraType.EQUIDISTANT:
            return EquidistantCamera(focal_length)
        elif camera_type == CameraType.EQUISOLID:
            return EquisolidCamera(focal_length)
        elif camera_type == CameraType.ORTHOGRAPHIC:
            return OrthographicCamera(focal_length)
        elif camera_type == CameraType.STEREOGRAPHIC:
            return StereographicCamera(focal_length)
        else:
            raise ValueError(f"Unknown camera type: {camera_type}")

    @staticmethod
    def f_from_theta_and_r(camera_type: CameraType, theta: float, r: float) -> float:
        """Compute the focal length from the angle theta and radius r."""
        if camera_type == CameraType.EQUIDISTANT:
            return EquidistantCamera.f_from_theta_and_r(theta, r)
        elif camera_type == CameraType.EQUISOLID:
            return EquisolidCamera.f_from_theta_and_r(theta, r)
        elif camera_type == CameraType.ORTHOGRAPHIC:
            return OrthographicCamera.f_from_theta_and_r(theta, r)
        elif camera_type == CameraType.STEREOGRAPHIC:
            return StereographicCamera.f_from_theta_and_r(theta, r)
        else:
            raise ValueError(f"Unknown camera type: {camera_type}")
