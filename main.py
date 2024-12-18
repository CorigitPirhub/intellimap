import sys
import signal
import os
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication
from backend import start_server
import threading

server_thread = threading.Thread(target=start_server)
server_thread.start()

app = QApplication(sys.argv)

signal.signal(signal.SIGINT, signal.SIG_DFL)

current_script_path = os.path.dirname(os.path.abspath(__file__))
relative_html_path = 'gaodemap.html'
full_html_path = os.path.join(current_script_path, relative_html_path)
qurl = QUrl.fromLocalFile(full_html_path)

browser = QWebEngineView()
browser.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
browser.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
browser.setUrl(qurl)
browser.show()

app.exec()