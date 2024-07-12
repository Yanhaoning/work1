import base64
import requests
import logging
import traceback
from PyQt5.QtCore import QThread, pyqtSignal

class VehicleDetectionThread(QThread):
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, img_base64, access_token, vehicle_detect_url):
        super(VehicleDetectionThread, self).__init__()
        self.img_base64 = img_base64
        self.access_token = access_token
        self.vehicle_detect_url = vehicle_detect_url

    def run(self):
        try:
            params = {"image": self.img_base64}
            request_url = self.vehicle_detect_url + "?access_token=" + self.access_token
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            response = requests.post(request_url, data=params, headers=headers, timeout=30)
            if response and response.status_code == 200:
                result = response.json()
                logging.info(f"车辆检测成功，返回值: {result}")
                self.result_signal.emit(result)
            else:
                self.error_signal.emit("车辆检测API请求失败")
                logging.error(f"车辆检测API请求失败，返回状态码: {response.status_code}, 返回内容: {response.content}")
        except requests.RequestException as e:
            logging.error(f"车辆检测API请求错误: {e}")
            self.error_signal.emit(f"车辆检测API请求错误: {e}")
            traceback.print_exc()

class VehicleRecognitionThread(QThread):
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, img_base64, access_token, vehicle_recognize_url):
        super(VehicleRecognitionThread, self).__init__()
        self.img_base64 = img_base64
        self.access_token = access_token
        self.vehicle_recognize_url = vehicle_recognize_url

    def run(self):
        try:
            params = {"image": self.img_base64}
            request_url = self.vehicle_recognize_url + "?access_token=" + self.access_token
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            response = requests.post(request_url, data=params, headers=headers, timeout=30)
            if response and response.status_code == 200:
                result = response.json()
                logging.info(f"车型识别成功，返回值: {result}")
                self.result_signal.emit(result)
            else:
                self.error_signal.emit("车型识别API请求失败")
                logging.error(f"车型识别API请求失败，返回状态码: {response.status_code}, 返回内容: {response.content}")
        except requests.RequestException as e:
            logging.error(f"车型识别API请求错误: {e}")
            self.error_signal.emit(f"车型识别API请求错误: {e}")
            traceback.print_exc()

class PeopleCountThread(QThread):
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(self, img_base64, access_token, people_count_url):
        super(PeopleCountThread, self).__init__()
        self.img_base64 = img_base64
        self.access_token = access_token
        self.people_count_url = people_count_url

    def run(self):
        try:
            params = {"image": self.img_base64}
            request_url = self.people_count_url + "?access_token=" + self.access_token
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            response = requests.post(request_url, data=params, headers=headers, timeout=30)
            if response and response.status_code == 200:
                result = response.json()
                logging.info(f"人流量分析成功，返回值: {result}")
                self.result_signal.emit(result)
            else:
                self.error_signal.emit("人流量分析API请求失败")
                logging.error(f"人流量分析API请求失败，返回状态码: {response.status_code}, 返回内容: {response.content}")
        except requests.RequestException as e:
            logging.error(f"人流量分析API请求错误: {e}")
            self.error_signal.emit(f"人流量分析API请求错误: {e}")
            traceback.print_exc()
