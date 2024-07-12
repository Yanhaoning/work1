import logging
import traceback
import base64
import cv2
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QTextEdit, QFileDialog, QRadioButton, QButtonGroup
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QGuiApplication
from ai.aithreads import VehicleDetectionThread, VehicleRecognitionThread, PeopleCountThread

class MonitorApp(QApplication):
    def __init__(self, *args, **kwargs):
        super(MonitorApp, self).__init__(*args, **kwargs)
        self.window = SourceSelectionWindow()
        self.monitor = None

    def exec(self):
        self.window.show()
        return super().exec()

class SourceSelectionWindow(QMainWindow):
    def __init__(self):
        super(SourceSelectionWindow, self).__init__()
        self.setWindowTitle('选择视频源')
        self.setFixedSize(800, 600)
        self.center()

        # 创建背景标签
        self.background_label = QLabel(self)
        self.background_label.setGeometry(0, 0, 800, 600)
        self.set_background_image('data/bg.jpg')

        self.select_video_button = QPushButton('选择视频文件', self)
        self.use_camera_button = QPushButton('使用摄像头', self)

        layout = QVBoxLayout()
        layout.addWidget(self.select_video_button)
        layout.addWidget(self.use_camera_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 确保按钮透明
        self.select_video_button.setStyleSheet("background-color: rgba(255, 255, 255, 150);")
        self.use_camera_button.setStyleSheet("background-color: rgba(255, 255, 255, 150);")

        self.select_video_button.clicked.connect(self.select_video_file)
        self.use_camera_button.clicked.connect(self.use_camera)

        self.video_file = None

    def set_background_image(self, image_path):
        pixmap = QPixmap(image_path)
        self.background_label.setPixmap(pixmap)
        self.background_label.setScaledContents(True)

    def center(self):
        screen = QGuiApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def select_video_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "选择视频文件", "", "Video Files (*.mp4 *.avi);;All Files (*)", options=options)
        if fileName:
            self.video_file = fileName
            self.open_monitor_window()

    def use_camera(self):
        self.video_file = None
        self.open_monitor_window()

    def open_monitor_window(self):
        self.monitor = TrafficMonitor(self.video_file)
        self.monitor.show()
        self.close()

class TrafficMonitor(QMainWindow):
    update_signal = pyqtSignal(str)
    update_image_signal = pyqtSignal(QImage)
    update_detection_signal = pyqtSignal()

    def __init__(self, video_file=None):
        super(TrafficMonitor, self).__init__()
        self.setWindowTitle('交通监控系统')
        self.setFixedSize(800, 600)
        self.center()

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)

        self.start_button = QPushButton('开始', self)
        self.stop_button = QPushButton('停止', self)
        self.stop_button.setEnabled(False)
        self.back_button = QPushButton('返回', self)

        self.vehicle_detection_radio = QRadioButton("车辆识别")
        self.people_count_radio = QRadioButton("人流量分析")
        self.radio_group = QButtonGroup()
        self.radio_group.addButton(self.vehicle_detection_radio)
        self.radio_group.addButton(self.people_count_radio)
        self.vehicle_detection_radio.setChecked(True)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.vehicle_detection_radio)
        layout.addWidget(self.people_count_radio)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.back_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.status_bar = self.statusBar()
        self.status_bar.showMessage('准备就绪')

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        self.start_button.clicked.connect(self.start_monitoring)
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.back_button.clicked.connect(self.back_to_source_selection)

        self.cap = None
        self.video_file = video_file
        self.access_token = '24.b94313c4c4283ea399558ab9fde20005.2592000.1723278741.282335-89936151'
        self.vehicle_detect_url = 'https://aip.baidubce.com/rest/2.0/image-classify/v1/vehicle_detect'
        self.vehicle_recognize_url = 'https://aip.baidubce.com/rest/2.0/image-classify/v1/car'
        self.people_count_url = 'https://aip.baidubce.com/rest/2.0/image-classify/v1/body_num'
        self.frame_count = 0
        self.detections = []

        self.update_signal.connect(self.update_text_edit)
        self.update_image_signal.connect(self.update_image_label)
        self.update_detection_signal.connect(self.update_detection_overlay)

    def center(self):
        screen = QGuiApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def back_to_source_selection(self):
        self.close()
        self.source_selection_window = SourceSelectionWindow()
        self.source_selection_window.show()

    def start_monitoring(self):
        if self.video_file:
            self.cap = cv2.VideoCapture(self.video_file)
        else:
            self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            self.update_text_edit("无法打开视频源")
            self.status_bar.showMessage("无法打开视频源")
            logging.error("无法打开视频源")
            return
        self.timer.start(40)  # 减少更新频率
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_bar.showMessage("监控开始")
        logging.info("监控开始")

    def stop_monitoring(self):
        self.timer.stop()
        if self.cap:
            self.cap.release()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_bar.showMessage("监控停止")
        logging.info("监控停止")

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.update_signal.emit("无法捕获视频帧")
            self.status_bar.showMessage("无法捕获视频帧")
            logging.error("无法捕获视频帧")
            return

        self.frame_count += 1
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame_rgb.shape
        step = channel * width
        qimg = QImage(frame_rgb.data, width, height, step, QImage.Format_RGB888)
        self.update_image_signal.emit(qimg)

        if self.frame_count % 40 == 0:  # 每40帧调用一次API
            _, buffer = cv2.imencode('.jpg', frame)
            img_base64 = base64.b64encode(buffer).decode()

            if self.vehicle_detection_radio.isChecked():
                self.vehicle_detection_thread = VehicleDetectionThread(img_base64, self.access_token, self.vehicle_detect_url)
                self.vehicle_detection_thread.result_signal.connect(self.process_vehicle_detection_result)
                self.vehicle_detection_thread.error_signal.connect(self.update_signal)
                self.vehicle_detection_thread.start()
            elif self.people_count_radio.isChecked():
                self.people_count_thread = PeopleCountThread(img_base64, self.access_token, self.people_count_url)
                self.people_count_thread.result_signal.connect(self.process_people_count_result)
                self.people_count_thread.error_signal.connect(self.update_signal)
                self.people_count_thread.start()

    def process_vehicle_detection_result(self, result):
        vehicle_info = result.get('vehicle_info', [])
        new_detections = []

        result_text = "车辆检测结果:\n"
        for vehicle in vehicle_info:
            vehicle_type = vehicle.get('type', '未知')
            location = vehicle.get('location', {})
            left = location.get('left', 0)
            top = location.get('top', 0)
            width = location.get('width', 0)
            height = location.get('height', 0)
            new_detections.append((vehicle_type, left, top, width, height))
            result_text += f"类型: {vehicle_type}, 位置: 左上({left}, {top}), 宽: {width}, 高: {height}\n"

        if new_detections != self.detections:
            self.detections = new_detections
            self.update_detection_signal.emit()
            logging.info(f"更新检测结果: {new_detections}")
            self.update_text_edit(result_text)

    def process_people_count_result(self, result):
        person_num = result.get('person_num', 0)
        result_text = f"人流量分析结果: \n人数: {person_num}\n"
        self.update_text_edit(result_text)
        logging.info(result_text)

    def update_detection_overlay(self):
        pixmap = self.image_label.pixmap()
        if pixmap is not None:
            painter = QPainter(pixmap)
            painter.setPen(QColor(0, 255, 0))
            for detection in self.detections:
                vehicle_type, left, top, width, height = detection
                painter.drawRect(left, top, width, height)
                painter.setPen(QColor(255, 0, 0))
                painter.drawText(left, top - 10, vehicle_type)
            painter.end()
            self.image_label.setPixmap(pixmap)
            logging.info("更新检测框")

    def update_text_edit(self, text):
        self.text_edit.setText(text)
        self.status_bar.showMessage(text)
        logging.info(text)

    def update_image_label(self, qimg):
        self.image_label.setPixmap(QPixmap.fromImage(qimg))
        self.update_detection_overlay()
