import sys
from monitor.monitorapp import MonitorApp

if __name__ == '__main__':
    app = MonitorApp(sys.argv)
    sys.exit(app.exec())




