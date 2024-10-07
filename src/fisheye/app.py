from typing import Tuple

import cv2
import numpy as np
import pyqtgraph as pg
from pyqtgraph import ImageItem, PlotWidget
from pyqtgraph.Qt import QtCore, QtGui
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGraphicsView,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from fisheye.projection import FisheyeToPerspective
from fisheye.schemas import CameraType, FisheyeFormat


class ImageWidget(PlotWidget):
    """Custom PlotWidget to display images."""

    on_mouse_moved = QtCore.Signal(object)

    def __init__(self, display_text: bool = True):
        super().__init__()
        self.getPlotItem().invertY()
        self.setAspectLocked()
        self.image_item = ImageItem()

        # Add image item to the PlotWidget
        self.addItem(self.image_item)

        # Customize the axes
        self.hideAxis("left")
        self.hideAxis("bottom")

        # Set cross cursor
        self.setCursor(QtCore.Qt.CrossCursor)
        self.setAntialiasing(False)

        # Optional text item to display coordinates and pixel values
        if display_text:
            self.text_item = pg.TextItem(
                anchor=(0, 1), color=(255, 255, 0), fill=(0, 0, 0, 100)
            )
            self.addItem(self.text_item)
            self.text_item.setPos(0, 0)
            self.text_item.hide()  # Initially hide the text item
            self.on_mouse_moved.connect(self.updateMousePosition)

        # Variable to store image data for pixel lookup
        self.image_data = None

    def set_image(self, image: np.ndarray) -> None:
        """Set and display the image."""
        if image.ndim == 3:
            image = np.flip(image, axis=2).swapaxes(0, 1)
        self.image_item.setImage(image)
        self.image_item.show()

        # Store the image for later pixel lookup
        self.image_data = image

        # Automatically adjust view to fit the image
        self.autoRange()

    def reset_view(self):
        """Reset the view (used to reset zoom or pan)."""
        self.autoRange()

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        # Get mouse position relative to the image view
        lpos = ev.position() if hasattr(ev, "position") else ev.localPos()
        pos = self.plotItem.vb.mapToScene(lpos)
        pos3 = self.plotItem.vb.mapSceneToView(pos)
        x = int(pos3.x())
        y = int(pos3.y())

        # Check if the mouse is within the bounds of the image
        if self.image_data is not None:
            if 0 <= x < self.image_data.shape[1] and 0 <= y < self.image_data.shape[0]:
                pixel_value = self.image_data[y, x]
                self.on_mouse_moved.emit((x, y, pixel_value))
        QGraphicsView.mouseMoveEvent(self, ev)

    def updateMousePosition(self, pos: Tuple[int, int, int]) -> None:
        x, y, pixel_value = pos
        self.text_item.setText(f"({x}, {y}) - V: {pixel_value}")
        self.text_item.setPos(x, y)
        self.text_item.show()

    def leaveEvent(self, ev: QtGui.QMouseEvent) -> None:
        self.text_item.hide()
        QGraphicsView.leaveEvent(self, ev)


class Viewer(QWidget):
    """Widget to display fisheye and perspective images side by side."""

    def __init__(self) -> None:
        super().__init__()

        # Initialize the fisheye and perspective views
        self.fisheye_view = ImageWidget()
        self.perspective_view = ImageWidget()

        # Create a layout for both images (horizontal layout)
        layout = QHBoxLayout()
        layout.addWidget(self.fisheye_view)
        layout.addWidget(self.perspective_view)
        self.setLayout(layout)

    def set_fisheye_image(self, image: np.ndarray) -> None:
        self.fisheye_view.set_image(image)

    def set_perspective_image(self, image: np.ndarray) -> None:
        self.perspective_view.set_image(image)


class FisheyeSettingsDialog(QDialog):
    """Dialog to set the fisheye projection parameters."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Fisheye Settings")
        self.setMinimumWidth(300)

        # Main layout
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Fisheye FOV
        self.fov_edit = QLineEdit()
        self.fov_edit.setText("180")
        self.fov_edit.setValidator(QtGui.QIntValidator(0, 180))
        form_layout.addRow("Fisheye FOV:", self.fov_edit)

        # Perspective FOV
        self.perspective_fov_edit = QLineEdit()
        self.perspective_fov_edit.setText("90")
        form_layout.addRow("Perspective FOV:", self.perspective_fov_edit)

        # Camera Type
        self.camera_type_combo = QComboBox()
        self.camera_type_combo.addItems([camera_type.name for camera_type in CameraType])
        form_layout.addRow("Camera Type:", self.camera_type_combo)

        # Format
        self.format_combo = QComboBox()
        self.format_combo.addItems([format.name for format in FisheyeFormat])
        form_layout.addRow("Format:", self.format_combo)

        # Output Shape
        self.output_shape_edit = QLineEdit()
        self.output_shape_edit.setText("-1,-1")
        form_layout.addRow("Output Shape:", self.output_shape_edit)

        layout.addLayout(form_layout)

        # add submit button
        self.submit_button = QPushButton("Submit")
        layout.addWidget(self.submit_button)
        self.submit_button.clicked.connect(self.submit)

        self.setLayout(layout)

        self.form_data = {
            "fov": 180,
            "perspective_fov": 90,
            "camera_type": CameraType.EQUIDISTANT,
            "format": FisheyeFormat.CIRCULAR,
            "output_shape": None,
        }

    def submit(self) -> None:
        fov = int(self.fov_edit.text())
        perspective_fov = int(self.perspective_fov_edit.text())
        camera_type = CameraType[self.camera_type_combo.currentText()]
        format = FisheyeFormat[self.format_combo.currentText()]
        output_shape = tuple(map(int, self.output_shape_edit.text().split(",")))
        form = {
            "fov": fov,
            "perspective_fov": perspective_fov,
            "camera_type": camera_type,
            "format": format,
            "output_shape": None if output_shape == (-1, -1) else output_shape,
        }
        self.form_data = form
        self.accept()


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Fisheye To Perspective")
        self.setMinimumSize(800, 600)

        # toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        # Load Image button
        load_button = QPushButton("Load Image")
        load_button.clicked.connect(self.open_image_dialog)

        # Settings button
        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self.show_settings_dialog)
        self.settings_dialog = FisheyeSettingsDialog()

        # Compute button
        compute_button = QPushButton("Compute")
        compute_button.clicked.connect(self.compute)

        # Add buttons to the toolbar
        toolbar.addWidget(load_button)
        toolbar.addWidget(settings_button)
        toolbar.addWidget(compute_button)

        # Viewer
        self.viewer = Viewer()
        self.setCentralWidget(self.viewer)

    def show_settings_dialog(self) -> None:
        self.settings_dialog.show()

    def open_image_dialog(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.file_path = file_path
            self.fisheye_image = cv2.imread(file_path)
            self.viewer.set_fisheye_image(self.fisheye_image)

    def compute(self) -> None:
        self.projection = FisheyeToPerspective(
            self.file_path, **self.settings_dialog.form_data
        )
        perspective_image = self.projection()
        self.viewer.set_perspective_image(perspective_image)


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
