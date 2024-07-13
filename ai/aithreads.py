import base64
import requests
import logging
import traceback
from PyQt5.QtCore import QThread, pyqtSignal

class VehicleDetectionThread(QThread):
    # 定义两个信号：result_signal 用于传递检测结果，error_signal 用于传递错误信息
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, img_base64, access_token, vehicle_detect_url):
        super(VehicleDetectionThread, self).__init__()
        self.img_base64 = img_base64  # base64编码的图像数据
        self.access_token = access_token  # API访问令牌
        self.vehicle_detect_url = vehicle_detect_url  # 车辆检测API的URL

    def run(self):
        try:
            # 将图像数据放入请求参数中
            params = {"image": self.img_base64}
            # 构建完整的API请求URL
            request_url = self.vehicle_detect_url + "?access_token=" + self.access_token
            # 设置请求头
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            # 发送POST请求
            response = requests.post(request_url, data=params, headers=headers, timeout=30)
            # 检查响应状态码是否为200（表示成功）
            if response and response.status_code == 200:
                # 将响应内容解析为JSON格式
                result = response.json()
                logging.info(f"车辆检测成功，返回值: {result}")
                # 通过result_signal信号传递检测结果
                self.result_signal.emit(result)
            else:
                # 处理API请求失败的情况，记录日志并通过error_signal信号传递错误信息
                self.error_signal.emit("车辆检测API请求失败")
                logging.error(f"车辆检测API请求失败，返回状态码: {response.status_code}, 返回内容: {response.content}")
        except requests.RequestException as e:
            # 处理请求异常，记录日志并通过error_signal信号传递错误信息
            logging.error(f"车辆检测API请求错误: {e}")
            self.error_signal.emit(f"车辆检测API请求错误: {e}")
            # 打印异常堆栈信息
            traceback.print_exc()

class VehicleRecognitionThread(QThread):
    # 定义两个信号：result_signal 用于传递识别结果，error_signal 用于传递错误信息
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, img_base64, access_token, vehicle_recognize_url):
        super(VehicleRecognitionThread, self).__init__()
        self.img_base64 = img_base64  # base64编码的图像数据
        self.access_token = access_token  # API访问令牌
        self.vehicle_recognize_url = vehicle_recognize_url  # 车型识别API的URL

    def run(self):
        try:
            # 将图像数据放入请求参数中
            params = {"image": self.img_base64}
            # 构建完整的API请求URL
            request_url = self.vehicle_recognize_url + "?access_token=" + self.access_token
            # 设置请求头
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            # 发送POST请求
            response = requests.post(request_url, data=params, headers=headers, timeout=30)
            # 检查响应状态码是否为200（表示成功）
            if response and response.status_code == 200:
                # 将响应内容解析为JSON格式
                result = response.json()
                logging.info(f"车型识别成功，返回值: {result}")
                # 通过result_signal信号传递识别结果
                self.result_signal.emit(result)
            else:
                # 处理API请求失败的情况，记录日志并通过error_signal信号传递错误信息
                self.error_signal.emit("车型识别API请求失败")
                logging.error(f"车型识别API请求失败，返回状态码: {response.status_code}, 返回内容: {response.content}")
        except requests.RequestException as e:
            # 处理请求异常，记录日志并通过error_signal信号传递错误信息
            logging.error(f"车型识别API请求错误: {e}")
            self.error_signal.emit(f"车型识别API请求错误: {e}")
            # 打印异常堆栈信息
            traceback.print_exc()

class PeopleCountThread(QThread):
    # 定义两个信号：result_signal 用于传递分析结果，error_signal 用于传递错误信息
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, img_base64, access_token, people_count_url):
        super(PeopleCountThread, self).__init__()
        self.img_base64 = img_base64  # base64编码的图像数据
        self.access_token = access_token  # API访问令牌
        self.people_count_url = people_count_url  # 人流量分析API的URL

    def run(self):
        try:
            # 将图像数据放入请求参数中
            params = {"image": self.img_base64}
            # 构建完整的API请求URL
            request_url = self.people_count_url + "?access_token=" + self.access_token
            # 设置请求头
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            # 发送POST请求
            response = requests.post(request_url, data=params, headers=headers, timeout=30)
            # 检查响应状态码是否为200（表示成功）
            if response and response.status_code == 200:
                # 将响应内容解析为JSON格式
                result = response.json()
                logging.info(f"人流量分析成功，返回值: {result}")
                # 通过result_signal信号传递分析结果
                self.result_signal.emit(result)
            else:
                # 处理API请求失败的情况，记录日志并通过error_signal信号传递错误信息
                self.error_signal.emit("人流量分析API请求失败")
                logging.error(f"人流量分析API请求失败，返回状态码: {response.status_code}, 返回内容: {response.content}")
        except requests.RequestException as e:
            # 处理请求异常，记录日志并通过error_signal信号传递错误信息
            logging.error(f"人流量分析API请求错误: {e}")
            self.error_signal.emit(f"人流量分析API请求错误: {e}")
            # 打印异常堆栈信息
            traceback.print_exc()
