import logging  # 导入日志模块，用于记录日志信息
import traceback  # 导入异常跟踪模块，用于打印异常堆栈信息
import base64  # 导入base64模块，用于编码和解码图像数据
import cv2  # 导入OpenCV库，用于图像处理
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QTextEdit, QFileDialog, QRadioButton, QButtonGroup
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QGuiApplication
from ai.aithreads import VehicleDetectionThread, VehicleRecognitionThread, PeopleCountThread  # 导入自定义线程类

class MonitorApp(QApplication):
    def __init__(self, *args, **kwargs):
        super(MonitorApp, self).__init__(*args, **kwargs)  # 调用父类初始化方法
        self.window = SourceSelectionWindow()  # 创建视频源选择窗口
        self.monitor = None  # 初始化监控窗口为空

    def exec(self):
        self.window.show()  # 显示视频源选择窗口
        return super().exec()  # 运行应用程序

class SourceSelectionWindow(QMainWindow):
    def __init__(self):
        super(SourceSelectionWindow, self).__init__()  # 调用父类初始化方法
        self.setWindowTitle('选择视频源')  # 设置窗口标题
        self.setFixedSize(800, 600)  # 设置窗口固定大小
        self.center()  # 窗口居中

        self.background_label = QLabel(self)  # 创建背景标签
        self.background_label.setGeometry(0, 0, 800, 600)  # 设置背景标签的位置和大小
        self.set_background_image('data/bg.jpg')  # 设置背景图像

        self.select_video_button = QPushButton('选择视频文件', self)  # 创建选择视频文件按钮
        self.use_camera_button = QPushButton('使用摄像头', self)  # 创建使用摄像头按钮

        layout = QVBoxLayout()  # 创建垂直布局
        layout.addWidget(self.select_video_button)  # 将选择视频文件按钮添加到布局
        layout.addWidget(self.use_camera_button)  # 将使用摄像头按钮添加到布局

        container = QWidget()  # 创建容器部件
        container.setLayout(layout)  # 设置容器的布局
        self.setCentralWidget(container)  # 将容器设置为中央部件

        self.select_video_button.setStyleSheet("background-color: rgba(255, 255, 255, 150);")  # 设置按钮透明度
        self.use_camera_button.setStyleSheet("background-color: rgba(255, 255, 255, 150);")  # 设置按钮透明度

        self.select_video_button.clicked.connect(self.select_video_file)  # 连接选择视频文件按钮的点击信号到槽函数
        self.use_camera_button.clicked.connect(self.use_camera)  # 连接使用摄像头按钮的点击信号到槽函数

        self.video_file = None  # 初始化视频文件路径为空

    def set_background_image(self, image_path):
        pixmap = QPixmap(image_path)  # 加载图像为QPixmap对象
        self.background_label.setPixmap(pixmap)  # 设置背景标签的图像
        self.background_label.setScaledContents(True)  # 设置背景标签的图像自适应大小

    def center(self):
        screen = QGuiApplication.primaryScreen().geometry()  # 获取屏幕几何信息
        size = self.geometry()  # 获取窗口几何信息
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)  # 移动窗口到屏幕中心

    def select_video_file(self):
        options = QFileDialog.Options()  # 创建文件对话框选项
        fileName, _ = QFileDialog.getOpenFileName(self, "选择视频文件", "", "Video Files (*.mp4 *.avi);;All Files (*)", options=options)  # 打开文件选择对话框
        if fileName:
            self.video_file = fileName  # 保存选择的视频文件路径
            self.open_monitor_window()  # 打开监控窗口

    def use_camera(self):
        self.video_file = None  # 将视频文件路径设置为空
        self.open_monitor_window()  # 打开监控窗口

    def open_monitor_window(self):
        self.monitor = TrafficMonitor(self.video_file)  # 创建交通监控窗口
        self.monitor.show()  # 显示交通监控窗口
        self.close()  # 关闭当前窗口

class TrafficMonitor(QMainWindow):
    update_signal = pyqtSignal(str)  # 定义更新文本信号
    update_image_signal = pyqtSignal(QImage)  # 定义更新图像信号
    update_detection_signal = pyqtSignal()  # 定义更新检测覆盖信号

    def __init__(self, video_file=None):
        super(TrafficMonitor, self).__init__()  # 调用父类初始化方法
        self.setWindowTitle('交通监控系统')  # 设置窗口标题
        self.setFixedSize(800, 600)  # 设置窗口固定大小
        self.center()  # 窗口居中

        self.image_label = QLabel(self)  # 创建图像显示标签
        self.image_label.setAlignment(Qt.AlignCenter)  # 设置图像标签居中对齐
        self.text_edit = QTextEdit(self)  # 创建文本编辑框
        self.text_edit.setReadOnly(True)  # 设置文本编辑框为只读

        self.start_button = QPushButton('开始', self)  # 创建开始按钮
        self.stop_button = QPushButton('停止', self)  # 创建停止按钮
        self.stop_button.setEnabled(False)  # 设置停止按钮不可用
        self.back_button = QPushButton('返回', self)  # 创建返回按钮

        self.vehicle_detection_radio = QRadioButton("车辆识别")  # 创建车辆识别单选按钮
        self.people_count_radio = QRadioButton("人流量分析")  # 创建人流量分析单选按钮
        self.radio_group = QButtonGroup()  # 创建按钮组
        self.radio_group.addButton(self.vehicle_detection_radio)  # 将车辆识别按钮添加到按钮组
        self.radio_group.addButton(self.people_count_radio)  # 将人流量分析按钮添加到按钮组
        self.vehicle_detection_radio.setChecked(True)  # 默认选择车辆识别按钮

        layout = QVBoxLayout()  # 创建垂直布局
        layout.addWidget(self.image_label)  # 将图像标签添加到布局
        layout.addWidget(self.text_edit)  # 将文本编辑框添加到布局
        layout.addWidget(self.vehicle_detection_radio)  # 将车辆识别按钮添加到布局
        layout.addWidget(self.people_count_radio)  # 将人流量分析按钮添加到布局
        layout.addWidget(self.start_button)  # 将开始按钮添加到布局
        layout.addWidget(self.stop_button)  # 将停止按钮添加到布局
        layout.addWidget(self.back_button)  # 将返回按钮添加到布局

        container = QWidget()  # 创建容器部件
        container.setLayout(layout)  # 设置容器的布局
        self.setCentralWidget(container)  # 将容器设置为中央部件

        self.status_bar = self.statusBar()  # 获取状态栏
        self.status_bar.showMessage('准备就绪')  # 设置状态栏初始信息

        self.timer = QTimer(self)  # 创建定时器
        self.timer.timeout.connect(self.update_frame)  # 连接定时器的超时信号到更新帧的槽函数

        self.start_button.clicked.connect(self.start_monitoring)  # 连接开始按钮的点击信号到槽函数
        self.stop_button.clicked.connect(self.stop_monitoring)  # 连接停止按钮的点击信号到槽函数
        self.back_button.clicked.connect(self.back_to_source_selection)  # 连接返回按钮的点击信号到槽函数

        self.cap = None  # 初始化视频捕获对象为空
        self.video_file = video_file  # 保存视频文件路径
        self.access_token = '24.b94313c4c4283ea399558ab9fde20005.2592000.1723278741.282335-89936151'  # API访问令牌
        self.vehicle_detect_url = 'https://aip.baidubce.com/rest/2.0/image-classify/v1/vehicle_detect'  # 车辆检测API的URL
        self.vehicle_recognize_url = 'https://aip.baidubce.com/rest/2.0/image-classify/v1/car'  # 车型识别API的URL
        self.people_count_url = 'https://aip.baidubce.com/rest/2.0/image-classify/v1/body_num'  # 人流量分析API的URL
        self.frame_count = 0  # 初始化帧计数器为0
        self.detections = []  # 初始化检测结果列表为空

        self.update_signal.connect(self.update_text_edit)  # 连接更新信号到更新文本编辑框的槽函数
        self.update_image_signal.connect(self.update_image_label)  # 连接更新图像信号到更新图像标签的槽函数
        self.update_detection_signal.connect(self.update_detection_overlay)  # 连接更新检测信号到更新检测覆盖的槽函数

    def center(self):
        screen = QGuiApplication.primaryScreen().geometry()  # 获取屏幕几何信息
        size = self.geometry()  # 获取窗口几何信息
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)  # 移动窗口到屏幕中心

    def back_to_source_selection(self):
        self.close()  # 关闭当前窗口
        self.source_selection_window = SourceSelectionWindow()  # 创建视频源选择窗口
        self.source_selection_window.show()  # 显示视频源选择窗口

    def start_monitoring(self):
        if self.video_file:
            self.cap = cv2.VideoCapture(self.video_file)  # 打开视频文件
        else:
            self.cap = cv2.VideoCapture(0)  # 打开摄像头

        if not self.cap.isOpened():
            self.update_text_edit("无法打开视频源")  # 更新文本编辑框显示信息
            self.status_bar.showMessage("无法打开视频源")  # 更新状态栏显示信息
            logging.error("无法打开视频源")  # 记录错误日志
            return
        self.timer.start(40)  # 启动定时器，每40毫秒更新一次
        self.start_button.setEnabled(False)  # 设置开始按钮不可用
        self.stop_button.setEnabled(True)  # 设置停止按钮可用
        self.status_bar.showMessage("监控开始")  # 更新状态栏显示信息
        logging.info("监控开始")  # 记录日志信息

    def stop_monitoring(self):
        self.timer.stop()  # 停止定时器
        if self.cap:
            self.cap.release()  # 释放视频捕获对象
        self.start_button.setEnabled(True)  # 设置开始按钮可用
        self.stop_button.setEnabled(False)  # 设置停止按钮不可用
        self.status_bar.showMessage("监控停止")  # 更新状态栏显示信息
        logging.info("监控停止")  # 记录日志信息

    def update_frame(self):
        ret, frame = self.cap.read()  # 读取视频帧
        if not ret:
            self.update_signal.emit("无法捕获视频帧")  # 发送无法捕获视频帧的信号
            self.status_bar.showMessage("无法捕获视频帧")  # 更新状态栏显示信息
            logging.error("无法捕获视频帧")  # 记录错误日志
            return

        self.frame_count += 1  # 增加帧计数器
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # 将视频帧从BGR转换为RGB
        height, width, channel = frame_rgb.shape  # 获取帧的高、宽和通道数
        step = channel * width  # 计算步长
        qimg = QImage(frame_rgb.data, width, height, step, QImage.Format_RGB888)  # 创建QImage对象
        self.update_image_signal.emit(qimg)  # 发送更新图像信号

        if self.frame_count % 40 == 0:  # 每40帧调用一次API
            _, buffer = cv2.imencode('.jpg', frame)  # 将帧编码为JPEG格式
            img_base64 = base64.b64encode(buffer).decode()  # 将编码后的帧转换为base64格式

            if self.vehicle_detection_radio.isChecked():  # 如果选择了车辆识别
                self.vehicle_detection_thread = VehicleDetectionThread(img_base64, self.access_token, self.vehicle_detect_url)  # 创建车辆检测线程
                self.vehicle_detection_thread.result_signal.connect(self.process_vehicle_detection_result)  # 连接结果信号到处理函数
                self.vehicle_detection_thread.error_signal.connect(self.update_signal)  # 连接错误信号到更新信号
                self.vehicle_detection_thread.start()  # 启动线程
            elif self.people_count_radio.isChecked():  # 如果选择了人流量分析
                self.people_count_thread = PeopleCountThread(img_base64, self.access_token, self.people_count_url)  # 创建人流量分析线程
                self.people_count_thread.result_signal.connect(self.process_people_count_result)  # 连接结果信号到处理函数
                self.people_count_thread.error_signal.connect(self.update_signal)  # 连接错误信号到更新信号
                self.people_count_thread.start()  # 启动线程

    def process_vehicle_detection_result(self, result):
        vehicle_info = result.get('vehicle_info', [])  # 获取车辆信息
        new_detections = []

        result_text = "车辆检测结果:\n"
        for vehicle in vehicle_info:
            vehicle_type = vehicle.get('type', '未知')  # 获取车辆类型
            location = vehicle.get('location', {})  # 获取车辆位置
            left = location.get('left', 0)  # 获取左边界
            top = location.get('top', 0)  # 获取上边界
            width = location.get('width', 0)  # 获取宽度
            height = location.get('height', 0)  # 获取高度
            new_detections.append((vehicle_type, left, top, width, height))  # 将检测结果添加到新检测结果列表中
            result_text += f"类型: {vehicle_type}, 位置: 左上({left}, {top}), 宽: {width}, 高: {height}\n"

        if new_detections != self.detections:  # 如果检测结果有变化
            self.detections = new_detections  # 更新检测结果
            self.update_detection_signal.emit()  # 发送更新检测信号
            logging.info(f"更新检测结果: {new_detections}")  # 记录日志信息
            self.update_text_edit(result_text)  # 更新文本编辑框

    def process_people_count_result(self, result):
        person_num = result.get('person_num', 0)  # 获取人数
        result_text = f"人流量分析结果: \n人数: {person_num}\n"
        self.update_text_edit(result_text)  # 更新文本编辑框
        logging.info(result_text)  # 记录日志信息

    def update_detection_overlay(self):
        pixmap = self.image_label.pixmap()  # 获取图像标签的pixmap
        if pixmap is not None:
            painter = QPainter(pixmap)  # 创建QPainter对象
            painter.setPen(QColor(0, 255, 0))  # 设置画笔颜色为绿色
            for detection in self.detections:
                vehicle_type, left, top, width, height = detection
                painter.drawRect(left, top, width, height)  # 绘制检测框
                painter.setPen(QColor(255, 0, 0))  # 设置画笔颜色为红色
                painter.drawText(left, top - 10, vehicle_type)  # 绘制车辆类型文字
            painter.end()  # 结束绘制
            self.image_label.setPixmap(pixmap)  # 更新图像标签的pixmap
            logging.info("更新检测框")  # 记录日志信息

    def update_text_edit(self, text):
        self.text_edit.setText(text)  # 更新文本编辑框的内容
        self.status_bar.showMessage(text)  # 更新状态栏的显示信息
        logging.info(text)  # 记录日志信息

    def update_image_label(self, qimg):
        self.image_label.setPixmap(QPixmap.fromImage(qimg))  # 更新图像标签的pixmap
        self.update_detection_overlay()  # 更新检测覆盖层
