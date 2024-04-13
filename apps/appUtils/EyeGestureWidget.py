import sys
from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QSlider, QLineEdit
from PySide2.QtGui import QPixmap, QPalette, QColor, QPainterPath, QRegion, QMouseEvent
from PySide2.QtCore import Qt, QRectF, QMargins, QPoint
from PySide2.QtGui import QPainter, QFont
from PySide2.QtCore import QByteArray
from PySide2.QtSvg import QSvgRenderer
from screeninfo   import get_monitors

from appUtils.ActivationZone import RoIMan
from appUtils.RoiViewer import RoiViewer

import hashlib
import os

class InputFileNameWidget(QWidget):

    def __init__(self,text_updated_cb) -> None:
        super().__init__()
        random_hash = hashlib.sha256(os.urandom(16)).hexdigest()[:8]
        self.text_updated_cb = text_updated_cb
        self.is_editable = True

        layout = QVBoxLayout()
        self.text_input = QLineEdit(f"collection_{random_hash}")
        self.text_input.setReadOnly(not self.is_editable)  # Set initial read-only state
        self.text_input.textChanged.connect(self.on_text_updated)
        self.unsetReadOnly()
        layout.addWidget(self.text_input)

        self.setLayout(layout)

    def setReadOnly(self):
        self.is_editable = False
        self.text_input.setReadOnly(not self.is_editable)  # Set initial read-only state
        self.text_input.setStyleSheet("""
                                QLineEdit {
                                    background-color: #14171A;
                                    border: 1px solid #14171A;
                                    color: #F5F8FA;
                                    border-radius: 5px; /* Adjust this value to change the roundness */
                                    font-size: 20px;  /* Larger font size */
                                    font-family: Poppins;
                                    padding: 5px;
                                }
                                """)

    def unsetReadOnly(self):
        self.is_editable = True
        self.text_input.setReadOnly(not self.is_editable)  # Set initial read-only state
        self.text_input.setStyleSheet("""
                                QLineEdit {
                                    background-color: #14171A;
                                    border: 1px solid #657786;
                                    color: #F5F8FA;
                                    border-radius: 5px; /* Adjust this value to change the roundness */
                                    font-size: 20px;  /* Larger font size */
                                    font-family: Poppins;
                                    padding: 5px;
                                }
                                """)

    def on_text_updated(self, updated_text):
        # Execute the callback function with the new text
        if self.text_updated_cb:
            self.text_updated_cb(updated_text)

    def getText(self):
        return self.text_input.text()

class EyeGestureWidget(QWidget):
    def __init__(self,
                start_cb = lambda : None,
                stop_cb = lambda : None,
                update_fixation_cb = lambda : None,
                update_radius_cb = lambda : None,
                text_updated_cb = lambda text : None):
        super().__init__()

        self.start_cb = start_cb
        self.stop_cb  = stop_cb
        self.update_fixation_cb = update_fixation_cb
        self.update_radius_cb   = update_radius_cb

        self.close_events = []
        self.roiMan = RoIMan()
        self.roiViewer = RoiViewer()

        self.monitor = list(filter(lambda monitor: monitor.is_primary == True ,get_monitors()))[0]
        postion_x = int(self.monitor.width/2) + self.monitor.x - 110
        postion_y = 45 + self.monitor.y

        # Set dark theme
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(1, 4, 4))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Highlight, QColor(142, 45, 197).lighter())
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)

        self.slider_fixation = QSlider(Qt.Horizontal)
        self.slider_fixation.setMinimum(0)
        self.slider_fixation.setMaximum(10)
        self.slider_fixation.setValue(8)
        self.slider_fixation.valueChanged.connect(self.update_fixation_label)

        self.slider_radius = QSlider(Qt.Horizontal)
        self.slider_radius.setMinimum(1)
        self.slider_radius.setMaximum(500)
        self.slider_radius.setValue(400)
        self.slider_radius.valueChanged.connect(self.update_radius_label)

        self.label_fixation_threshold = QLabel("Fixation: 0.8")
        self.label_radius_threshold   = QLabel("Radius: 500px")

        # Window positioning
        self.setGeometry(100, 100, 1000, 700)  # Adjust size as needed
        self.move_to_center()

        self.setWindowTitle("EyeGestures")
        # Buttons
        self.close_btn = QPushButton('Close')
        self.close_btn.clicked.connect(self.close_event)

        self.add_roi_btn = QPushButton('Add')
        self.add_roi_btn.clicked.connect(self.add_roi)

        self.show_roi_btn = QPushButton('Show')
        self.show_roi_btn.clicked.connect(self.show_roi)

        self.label_name = QLabel("EyeGestures")
        # Set text alignment to center
        self.label_name.setAlignment(Qt.AlignCenter)

        progress_bar_container_layout = QHBoxLayout()
        progress_bar_container_layout.setAlignment(Qt.AlignHCenter)

        self.start_stop_btn = QPushButton("Start")
        self.start_stop_btn.setCheckable(True)  # Make the button a toggle button
        self.start_stop_btn.clicked.connect(self.toggle_start_stop)

        progress_bar_container_layout.addWidget(self.start_stop_btn)

        self.fixation_bar = QProgressBar()
        self.fixation_bar.setValue(0)  # Set initial value
        self.fixation_bar.setFixedHeight(100)
        self.fixation_bar.setOrientation(Qt.Orientation.Vertical)
        self.fixation_bar.setTextVisible(False)
        self.fixation_bar.setStyleSheet("""
                                        QProgressBar {
                                            background-color: #06020f;
                                            border-radius: 10px; /* Adjust this value to change the roundness */
                                        }
                                        QProgressBar::chunk {
                                            background-color: #8b125c;
                                            border-radius: 10px; /* Adjust this value to change the roundness */
                                        }
                                        """)

        self.label_fixation        = QLabel("Fixation")
        self.label_fixation_level  = QLabel("0.0")
        progress_bar_container_layout.addWidget(self.fixation_bar)
        progress_bar_container_layout.addWidget(self.label_fixation)
        progress_bar_container_layout.addWidget(self.label_fixation_level)

        # Set font size
        font = self.label_name.font()
        font.setPointSize(20) # You can adjust the font size as per your requirement
        self.label_name.setFont(font)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addWidget(self.label_name)

        self.text_input = InputFileNameWidget(text_updated_cb)
        main_layout.addWidget(self.text_input)

        # self.image_label.setPixmap(scaled_pixmap)
        fixation_layout = QHBoxLayout()
        fixation_layout.addWidget(self.label_fixation_threshold)
        fixation_layout.addWidget(self.slider_fixation)
        main_layout.addLayout(fixation_layout)

        radius_layout = QHBoxLayout()
        radius_layout.addWidget(self.label_radius_threshold)
        radius_layout.addWidget(self.slider_radius)
        main_layout.addLayout(radius_layout)

        main_layout.addLayout(progress_bar_container_layout)
        main_layout.addWidget(self.roiViewer)

        roi_buttons_layout = QHBoxLayout()
        roi_buttons_layout.setSpacing(0)

        roi_buttons_layout.addWidget(self.show_roi_btn,2)
        roi_buttons_layout.addWidget(self.add_roi_btn,1)
        main_layout.addLayout(roi_buttons_layout)
        main_layout.addWidget(self.close_btn)

        # Set font bold for button2
        self.add_roi_btn.setStyleSheet(
            """
            QPushButton {
                padding: 0px; margin: 0px;
                border: 2px solid #657786;
                height: 40px;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
                color: #E1E8ED;
                border-right: none;
                border-top: none;
                border-bottom: none;
                background-color: #14171A;
                font-size: 14px;  /* Larger font size */
                font-family: Poppins;
            }
            QPushButton:hover {
                background-color: #818992;
            }
            QPushButton:pressed {
                background-color: #212426;
            }
            """)

        self.show_roi_btn.setStyleSheet(
            """
            QPushButton {
                padding: 0px; margin: 0px;
                border: 2px solid #657786;
                height: 40px;
                border-top-left-radius: 5px;
                border-bottom-left-radius: 5px;
                color: #eff0f1;
                border-right: none;
                border-left: none;
                border-top: none;
                border-bottom: none;
                background-color: #14171A;
                font-size: 14px;  /* Larger font size */
                font-family: Poppins;
            }
            QPushButton:hover {
                background-color: #818992;
            }
            QPushButton:pressed {
                background-color: #212426;
            }
            """)

        self.style_buttons(self.close_btn)
        self.style_buttons(self.start_stop_btn)

        # this sets windows frameless
        self.resize(400,self.frameGeometry().height())
        radius = 10.0
        path = QPainterPath()
        # self.resize(440,220)
        path.addRoundedRect(QRectF(self.rect()), radius, radius)
        mask = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(mask)

        self.setLayout(main_layout)
        self.move(postion_x, postion_y)

    def get_text(self):
        return self.text_input.getText()

    def toggle_start_stop(self):
        text = "Stop" if self.start_stop_btn.isChecked() else "Start"
        self.start_stop_btn.setText(text)

        if text == "Start":
            self.text_input.unsetReadOnly()
            self.stop_cb()
        else:
            self.text_input.setReadOnly()
            self.start_cb()

        # Perform actions based on button state here (optional)

    def update_fixation(self,value):
        self.label_fixation_level.setText(f"{value:.2f}")
        self.fixation_bar.setValue(int(value * 100))

    def update_fixation_label(self, value):
        # Convert integer value to float (0.0 to 1.0)
        self.label_fixation_threshold.setText(f"Fixation: {value/10}")
        self.update_fixation_cb(value/10)

    def update_radius_label(self, value):
        # Convert integer value to float (0.0 to 1.0)
        self.label_radius_threshold.setText(f"Radius: {value}px")
        self.update_radius_cb(value)

    def add_close_event(self,clsoe_callback):
        self.close_events.append(clsoe_callback)

    def close_event(self):

        for event in self.close_events:
            event()

        self.roiMan.remove()
        self.close()

    def move_to_center(self):
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) / 2
        y = (screen_geometry.height() - self.height()) / 4  # Adjust to bring the window to the top middle
        self.move(int(x), int(y))

    def style_buttons(self, *buttons):
        for button in buttons:
            button.setStyleSheet("""
                QPushButton {
                    border: none;
                    border-radius: 5px;
                    background-color: #14171A;
                    color: #eff0f1;
                    margin: 5px;
                    padding: 10px;
                    padding: 10px 20px;  /* Increase padding for bigger size */
                    font-size: 14px;  /* Larger font size */
                    font-family: Poppins;
                }
                QPushButton:hover {
                    background-color: #818992;
                }
                QPushButton:pressed {
                    background-color: #212426;
                }
            """)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.oldPos:
            return

        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.oldPos = None

    def rm_roi(self,id):
        print("removing")
        self.roiViewer.rm_rectangle(id)
        self.roiViewer.update()

    def update_roi(self,id,rect_params):
        # TODO: maybe those parameters could be handled better?
        rois = self.roiMan.get_all_rois()
        for key in rois:
            self.roiViewer.add_rectangle(
                key,
                rois[key].get_rectangle(),
                self.monitor.width,
                self.monitor.height
            )
        self.roiViewer.update()

    def add_roi(self):
        self.roiMan.add_roi(self.rm_roi,self.update_roi)
        rois = self.roiMan.get_all_rois()
        for key in rois:
            print(rois[key])
            self.roiViewer.add_rectangle(
                key,
                rois[key].get_rectangle(),
                self.monitor.width,
                self.monitor.height)
        self.roiViewer.update()

    def show_roi(self):
        self.roiMan.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    eyegesture_widget = EyeGestureWidget()
    eyegesture_widget.show()

    sys.exit(app.exec_())
