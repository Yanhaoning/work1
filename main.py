import sys  # 导入系统模块，用于访问与系统相关的参数和函数
from monitor.monitorapp import MonitorApp  # 从自定义的monitor模块中导入MonitorApp类

if __name__ == '__main__':
    app = MonitorApp(sys.argv)  # 创建MonitorApp实例，传入命令行参数
    sys.exit(app.exec())  # 执行应用程序的事件循环，并在退出时返回状态码
