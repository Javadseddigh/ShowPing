import re
import sys
import platform
import subprocess
import os
import json
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QSystemTrayIcon, 
                            QMenu, QMessageBox, QGraphicsDropShadowEffect,
                            QVBoxLayout, QSlider, QDialog, QPushButton,
                            QLineEdit)
from PyQt6.QtGui import (QIcon, QFont, QAction, QGuiApplication, QPainter, 
                        QColor, QBrush, QPalette, QLinearGradient, QPixmap)
from PyQt6.QtCore import Qt, QTimer, QSharedMemory, QSettings, QPoint, QSize


APP_NAME = "PingMonitor"  
APP_SETTINGS_GROUP = "Settings"

class PingMonitor(QWidget):
    def __init__(self):
        super().__init__()
        
        self.settings = QSettings(APP_NAME, APP_SETTINGS_GROUP)
        
        self.ping_interval = self.settings.value("ping_interval", 2000, type=int)
        self.target_host = self.settings.value("target_host", "8.8.8.8", type=str)
        self.font_size = self.settings.value("font_size", 11, type=int)
        self.language = self.settings.value("language", "en", type=str)
        
        self.prevent_multiple_instances()
        
        self.setup_window()
        
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.show_error_message("Error", "System tray is not available on this system!")
            sys.exit(1)
            
        self.setup_ui()
        self.setup_tray_icon()
        self.setup_ping_timer()

    def setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(100, 40)
        
        pos = self.settings.value("window_position")
        if pos and isinstance(pos, QPoint):
            self.move(pos)
        else:
            screen_geometry = QGuiApplication.primaryScreen().geometry()
            self.move(0, 0)

    def setup_ui(self):
        self.ping_label = QLabel("Ping: - ms", self)
        self.ping_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ping_label.setGeometry(0, 0, 100, 40)
        
        font = QFont("Segoe UI", self.font_size, QFont.Weight.Bold)
        self.ping_label.setFont(font)
        
        palette = self.ping_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255, 230))
        self.ping_label.setPalette(palette)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(2, 2)
        self.ping_label.setGraphicsEffect(shadow)

    def create_tray_icon(self):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        gradient = QLinearGradient(0, 0, 32, 32)
        gradient.setColorAt(0, QColor(100, 200, 255))
        gradient.setColorAt(1, QColor(200, 100, 255))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 4, 24, 24)
        
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        first_letter = APP_NAME[0] if APP_NAME else "P"
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, first_letter)
        
        painter.end()
        return QIcon(pixmap)

    def find_icon_path(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        possible_paths = [
            "favicon.ico",
            os.path.join(current_dir, "favicon.ico"),
            os.path.join(current_dir, "icons", "favicon.ico"),
            os.path.join(os.path.expanduser("~"), f".{APP_NAME.lower()}", "favicon.ico"),
            os.path.join(sys._MEIPASS, "favicon.ico") if hasattr(sys, '_MEIPASS') else None,
            f"/usr/share/icons/{APP_NAME.lower()}/favicon.ico"
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                return path
        return None

    def setup_tray_icon(self):
        self.default_icon = self.create_tray_icon()
        
        icon_path = self.find_icon_path()
        
        self.tray_icon = QSystemTrayIcon(self)
        if icon_path and os.path.isfile(icon_path):
            try:
                self.tray_icon.setIcon(QIcon(icon_path))
            except Exception:
                self.tray_icon.setIcon(self.default_icon)
        else:
            self.tray_icon.setIcon(self.default_icon)
            
        self.setup_tray_menu()

    def setup_tray_menu(self):
        tray_menu = QMenu()
        
        actions = [
            ("Show", self.show_normal, "Ctrl+S"),
            ("Hide", self.hide, "Ctrl+H"),
            ("Settings", self.show_settings, "Ctrl+P"),
            None,
            ("Exit", self.safe_exit, "Ctrl+Q")
        ]
        
        for action in actions:
            if action is None:
                tray_menu.addSeparator()
            else:
                text, callback, shortcut = action
                act = QAction(text, self)
                act.triggered.connect(callback)
                act.setShortcut(shortcut)
                tray_menu.addAction(act)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.toggle_visibility)
        self.tray_icon.show()

    def show_settings(self):
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("Settings")
        settings_dialog.setFixedSize(300, 240)
        
        layout = QVBoxLayout()
        
        ping_label = QLabel("Ping interval (ms):")
        layout.addWidget(ping_label)
        
        ping_slider = QSlider(Qt.Orientation.Horizontal)
        ping_slider.setMinimum(500)
        ping_slider.setMaximum(10000)
        ping_slider.setValue(self.ping_interval)
        ping_slider.setTickInterval(500)
        ping_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        layout.addWidget(ping_slider)
        
        value_label = QLabel(str(self.ping_interval))
        ping_slider.valueChanged.connect(lambda v: value_label.setText(str(v)))
        layout.addWidget(value_label)
        
        host_label = QLabel("Target host:")
        layout.addWidget(host_label)
        
        host_input = QLineEdit(self.target_host)
        layout.addWidget(host_input)
        
        button_layout = QVBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        
        save_button.clicked.connect(lambda: self.save_settings(ping_slider.value(), host_input.text()))
        cancel_button.clicked.connect(settings_dialog.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        settings_dialog.setLayout(layout)
        settings_dialog.exec()

    def save_settings(self, ping_interval, target_host):
        self.ping_interval = ping_interval
        self.target_host = target_host
        
        self.settings.setValue("ping_interval", ping_interval)
        self.settings.setValue("target_host", target_host)
        
        self.ping_timer.stop()
        self.ping_timer.start(self.ping_interval)
        self.update_ping()

    def setup_ping_timer(self):
        self.ping_timer = QTimer(self)
        self.ping_timer.timeout.connect(self.update_ping)
        self.ping_timer.start(self.ping_interval)
        self.update_ping()

    def prevent_multiple_instances(self):
        try:
            key_name = f"{APP_NAME}_Instance_Lock"
            self.shared_mem = QSharedMemory(key_name)
            
            if self.shared_mem.attach():
                self.shared_mem.detach()
                
                test_mem = QSharedMemory(key_name)
                if test_mem.attach():
                    test_mem.detach()
                    self.show_error_message("Warning", f"{APP_NAME} is already running!")
                    sys.exit(1)
            
            if not self.shared_mem.create(1):
                if self.shared_mem.error() == QSharedMemory.SharedMemoryError.AlreadyExists:
                    cleanup_mem = QSharedMemory(key_name)
                    if cleanup_mem.attach():
                        cleanup_mem.detach()
                    
                    if not self.shared_mem.create(1):
                        self.show_error_message("Error", f"Error creating shared memory: {self.shared_mem.errorString()}")
                        sys.exit(1)
        except Exception as e:
            self.show_error_message("Error", f"Error in single instance system: {str(e)}")
            sys.exit(1)

    def show_error_message(self, title, message):
        try:
            QMessageBox.critical(None, title, message)
        except Exception:
            print(f"Error: {message}")

    def get_ping(self):
        try:
            host = self.target_host
            timeout = 2
            
            if platform.system().lower() == "windows":
                command = ["ping", "-n", "1", "-w", str(timeout*1000), host]
                startup = subprocess.STARTUPINFO()
                startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                output = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    startupinfo=startup,
                    timeout=timeout+1
                )
                
                patterns = [r"time=(\d+\.?\d*)ms", r"time[=<](\d+\.?\d*)ms"]
                
                for pattern in patterns:
                    match = re.search(pattern, output.stdout, re.IGNORECASE)
                    if match:
                        return int(float(match.group(1)))
                        
                if "destination host unreachable" in output.stdout.lower():
                    return -2
                
                return -1
                
            else:
                output = subprocess.run(
                    ["ping", "-c", "1", "-W", str(timeout), host],
                    capture_output=True,
                    text=True,
                    timeout=timeout+1
                )
                match = re.search(r"time=(\d+\.?\d*) ms", output.stdout)
                
                if match:
                    return int(float(match.group(1)))
                
                if "100% packet loss" in output.stdout or "network is unreachable" in output.stdout:
                    return -2
                    
                return -1
                
        except subprocess.TimeoutExpired:
            return -2
        except Exception as e:
            print(f"Ping error: {str(e)}")
            return -1

    def update_ping(self):
        try:
            ping = self.get_ping()
            
            if ping >= 0:
                status = f"Ping: {ping} ms"
            elif ping == -2:
                status = "Offline"
            else:
                status = "Error"
            
            self.ping_label.setText(status)
            self.update_ping_color(ping)
            self.tray_icon.setToolTip(status)
        except Exception as e:
            print(f"Error updating ping: {str(e)}")
            self.ping_label.setText("Error")

    def update_ping_color(self, ping):
        if ping == -2:
            color = QColor(255, 80, 80, 230)
        elif ping == -1:
            color = QColor(255, 150, 150, 230)
        elif ping < 50:
            color = QColor(150, 255, 150, 230)
        elif ping < 100:
            color = QColor(200, 255, 150, 230)
        elif ping < 200:
            color = QColor(255, 255, 150, 230)
        else:
            color = QColor(255, 150, 150, 230)
        
        palette = self.ping_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, color)
        self.ping_label.setPalette(palette)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        brush = QBrush(QColor(40, 40, 40, 200))
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        
        rect = self.rect().adjusted(2, 2, -2, -2)
        painter.drawRoundedRect(rect, 10, 10)
        
        painter.setPen(QColor(100, 100, 100, 100))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, 10, 10)

    def toggle_visibility(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_normal() if self.isHidden() else self.hide()

    def show_normal(self):
        self.show()
        self.activateWindow()
        self.raise_()

    def safe_exit(self):
        try:
            self.save_window_position()
            
            if hasattr(self, 'ping_timer'):
                self.ping_timer.stop()
            
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()
            
            if hasattr(self, 'shared_mem') and self.shared_mem.isAttached():
                self.shared_mem.detach()
                
            QGuiApplication.processEvents()
            
            QApplication.quit()
        except Exception as e:
            print(f"Error exiting: {str(e)}")
        finally:
            sys.exit(0)

    def save_window_position(self):
        if not self.isHidden():
            self.settings.setValue("window_position", self.pos())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'old_pos') and self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if hasattr(self, 'old_pos'):
            self.old_pos = None
            self.save_window_position()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

if __name__ == "__main__":
    try:
        QApplication.setApplicationName(APP_NAME)
        QApplication.setOrganizationName(APP_NAME)
        
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        app.setStyle('Fusion')
        
        monitor = PingMonitor()
        monitor.show()
        
        sys.exit(app.exec())
    except Exception as e:
        try:
            QMessageBox.critical(None, f"{APP_NAME} Error", f"Unexpected error: {str(e)}")
        except:
            print(f"Critical error: {str(e)}")
        sys.exit(1)