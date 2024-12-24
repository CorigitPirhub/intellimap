import sys
import signal
import os
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from backend import start_server
from multiprocessing import Process

class MyWebEngineView(QWebEngineView):
    def closeEvent(self, event):
        print("Closing the application...")
        if server_process.is_alive():  # 检查子进程是否运行中
            server_process.terminate()  # 终止子进程
            server_process.join()  # 等待子进程结束
            print("Server process terminated.")
        event.accept()  # 接受关闭事件


if __name__ == '__main__':

    # 启动后台子进程
    server_process = Process(target=start_server, daemon=True)
    server_process.start()

    app = QApplication(sys.argv)
    icon_path = './icon/icon.png'  # 确保图标文件存在
    app.setWindowIcon(QIcon(icon_path))

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    current_script_path = os.path.dirname(os.path.abspath(__file__))
    relative_html_path = 'gaodemap.html'
    full_html_path = os.path.join(current_script_path, relative_html_path)
    qurl = QUrl.fromLocalFile(full_html_path)


    profile = QWebEngineProfile.defaultProfile()

    profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
    profile.setHttpCacheMaximumSize(100000000) # 100MB
    app.setAttribute(Qt.ApplicationAttribute.AA_UseOpenGLES,True)
    browser = MyWebEngineView()
    browser.setWindowTitle('智行 IntelliMap')
    browser.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
    browser.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
    browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
    browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False)
    browser.settings().setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
    browser.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)

    browser.setUrl(qurl)
    browser.show()

    app.exec()

    # 确保子进程在应用退出后终止
    if server_process.is_alive():
        server_process.terminate()
        server_process.join()
