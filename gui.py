"""
UI components for the flight monitor application
"""
from PyQt5.QtWidgets import QApplication, QMessageBox, QMainWindow, QTextEdit, QVBoxLayout, QPushButton, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QTimer, QThread
import logging
import time

class QTextEditLogger(logging.Handler):
    def __init__(self, parent=None):
        super().__init__()
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.widget = QTextEdit()
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.append(msg)

class LogWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Flight Monitor Logs")
        self.setGeometry(100, 100, 800, 600)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout
        layout = QVBoxLayout(central_widget)

        # Log widget
        self.log_widget = QTextEditLogger(self)
        layout.addWidget(self.log_widget.widget)

        # Countdown label
        self.countdown_label = QLabel("Next check: Not scheduled yet")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #0066cc; padding: 8px;")
        layout.addWidget(self.countdown_label)

        # Stop button
        self.stop_button = QPushButton("Stop Monitor")
        self.stop_button.clicked.connect(self.stop_monitor)
        layout.addWidget(self.stop_button)

        # Timer to update the countdown
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_countdown)
        self.update_timer.start(1000)  # Update every second

        # Initialize next check time to None
        self.next_check_time = None

    def stop_monitor(self):
        logging.info("Stop button clicked, shutting down...")
        app = QApplication.instance()
        if app and hasattr(app, 'cleanup'):
            app.cleanup()
            app.quit()

    def update_countdown(self):
        if self.next_check_time:
            now = time.time()
            remaining = max(self.next_check_time - now, 0)

            # Format the remaining time
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)

            if minutes > 0:
                self.countdown_label.setText(f"Next check in: {minutes} min {seconds} sec")
            else:
                self.countdown_label.setText(f"Next check in: {seconds} sec")

            # Change color when getting close to the next check
            if remaining < 60:  # Less than a minute
                self.countdown_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #cc3300; padding: 8px;")
            else:
                self.countdown_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #0066cc; padding: 8px;")

    def set_next_check_time(self, next_time):
        self.next_check_time = next_time