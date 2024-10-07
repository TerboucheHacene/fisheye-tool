import os
from typing import Tuple

import cv2
import numpy as np

from fisheye.camera import FisheyeCameraFactory
from fisheye.schemas import CameraType, FisheyeFormat


class FisheyeToPerspective:
    """Convert fisheye image to perspective image

    The conversion is done by computing the undistortion map for each pixel in the
    fisheye image. The undistortion map is computed using the mapping between the angle
    theta and the radius r for the fisheye camera model. The undistortion map is then
    used to remap the fisheye image to the perspective image.


    """

    def __init__(
        self,
        image_file: str,
        fov: float,
        perspective_fov: float,
        camera_type: CameraType = CameraType.EQUIDISTANT,
        format: FisheyeFormat = FisheyeFormat.CIRCULAR,
        output_shape: Tuple[int, int] = None,
    ) -> None:
        self._image_file = image_file
        self._fov = fov
        self._rfov = fov / 2
        self._perspective_fov = perspective_fov
        self._format = format
        self.read_image()
        self._camera_type = camera_type
        self._output_shape = output_shape

    def get_perspective_width(self) -> int:
        if self._format == FisheyeFormat.CIRCULAR:
            return min(self._width, self._height)
        elif self._format == FisheyeFormat.DIAGONAL:
            return np.sqrt(self._width**2 + self._height**2)
        else:
            raise ValueError(f"Unknown format {self._format}")

    def read_image(self) -> None:
        if not os.path.exists(self._image_file):
            raise FileNotFoundError(f"Image file {self._image_file} not found")
        self.image = cv2.imread(self._image_file)
        if self.image is None:
            raise ValueError(f"Could not read image file {self._image_file}")
        self._height = self.image.shape[0]
        self._width = self.image.shape[1]
        dim = min(self._width, self._height)
        offset_x = (self._width - dim) // 2
        offset_y = (self._height - dim) // 2
        self.image = self.image[offset_y : offset_y + dim, offset_x : offset_x + dim]

        self._height = self.image.shape[0]
        self._width = self.image.shape[1]
        self._x_center = (self._width - 1) // 2
        self._y_center = (self._height - 1) // 2

    @staticmethod
    def focal_length_from_fov(fov: float, width: int) -> float:
        return width / (2 * np.tan(np.radians(fov) / 2))

    def generate_meshgrid(self) -> Tuple[np.ndarray, np.ndarray]:
        x = np.arange(self._width)
        y = np.arange(self._height)
        x, y = np.meshgrid(x, y)
        x = x - self._x_center
        y = y - self._y_center
        return x, y

    def init_undistort_map(
        self, xy: Tuple[np.ndarray, np.ndarray], pfocal: float, dim: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Compute the undistortion map for perspective projection from fisheye image

        The undistortion map is computed using the following steps:
        1. Compute the distorted radius from the center of the image for each pixel
        2. Compute the angle theta for each pixel
        3. Compute the focal length for the perspective camera
        4. Compute the radius for the perspective camera
        5. Compute the undistortion map (map_x, map_y) for each pixel:
            - map_x = perspective_r / distorted_r * x + x_center
            - map_y = perspective_r / distorted_r * y + y_center

        Args:
            xy (Tuple[np.ndarray, np.ndarray]): x and y coordinates
            pfocal (float): perspective focal length
            dim (int): perspective image width

        Returns:
            Tuple[np.ndarray, np.ndarray]: x and y undistortion map
        """

        x, y = xy
        distorted_r = np.hypot(x, y)
        theta = np.arctan(distorted_r / pfocal)
        focal_fisheye = FisheyeCameraFactory.f_from_theta_and_r(
            self._camera_type, np.deg2rad(self._rfov), dim / 2
        )
        camera = FisheyeCameraFactory.create_camera(self._camera_type, focal_fisheye)
        perspective_r = camera.theta_to_r(theta)
        mask = distorted_r != 0
        map_x = np.zeros_like(x, dtype=np.float32)
        map_y = np.zeros_like(y, dtype=np.float32)
        map_x[mask] = perspective_r[mask] / distorted_r[mask] * x[mask] + self._x_center
        map_y[mask] = perspective_r[mask] / distorted_r[mask] * y[mask] + self._y_center
        return map_x, map_y

    def __call__(self, output_file: str = None) -> np.ndarray:
        dim = self.get_perspective_width()
        perspective_focal_length = self.focal_length_from_fov(self._perspective_fov, dim)
        x, y = self.generate_meshgrid()
        map_x, map_y = self.init_undistort_map((x, y), perspective_focal_length, dim)
        if self._output_shape is not None:
            map_x = cv2.resize(map_x, self._output_shape, interpolation=cv2.INTER_LINEAR)
            map_y = cv2.resize(map_y, self._output_shape, interpolation=cv2.INTER_LINEAR)
        perspective_image = cv2.remap(
            self.image, map_x, map_y, interpolation=cv2.INTER_CUBIC
        )
        if output_file is not None:
            cv2.imwrite(output_file, perspective_image)
        return perspective_image
