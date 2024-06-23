import sys
import json
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, \
    QPushButton, QMessageBox, QComboBox

SERVER_URL_CONFIG_KEY = 'SERVER_URL'

categories = ["Published Works", "Media Appearances"]


class UrlEntryWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window

        self.url_entry = QLineEdit()
        self.title_entry = QLineEdit()
        self.description_entry = QLineEdit()

        self.category_dropdown = QComboBox()
        self.category_dropdown.addItems(categories)

        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_self)

        layout = QVBoxLayout()
        entry_layout = QVBoxLayout()

        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL:"))
        url_layout.addWidget(self.url_entry)

        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Title:"))
        title_layout.addWidget(self.title_entry)

        description_layout = QHBoxLayout()
        description_layout.addWidget(QLabel("Description:"))
        description_layout.addWidget(self.description_entry)

        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Category:"))
        category_layout.addWidget(self.category_dropdown)

        entry_layout.addLayout(url_layout)
        entry_layout.addLayout(title_layout)
        entry_layout.addLayout(description_layout)
        entry_layout.addLayout(category_layout)

        layout.addLayout(entry_layout)
        layout.addWidget(self.remove_button)

        self.setLayout(layout)

    def remove_self(self):
        self.main_window.remove_url_entry(self)
        self.setParent(None)
        self.deleteLater()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.url_entries = []

        self.setWindowTitle("URL Uploader")
        self.resize(400, 300)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        server_url_layout = QHBoxLayout()
        self.server_url_label = QLabel("Server URL (don't change unless necessary):")
        self.server_url_entry = QLineEdit()
        self.server_url_entry.mouseDoubleClickEvent = self.toggle_editable

        try:
            with open('config.json') as config_file:
                config = json.load(config_file)
                default_server_url = config.get(SERVER_URL_CONFIG_KEY)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            default_server_url = ""

        if default_server_url:
            self.server_url_entry.setReadOnly(True)

        self.server_url_entry.setText(default_server_url)
        server_url_layout.addWidget(self.server_url_label)
        server_url_layout.addWidget(self.server_url_entry)

        self.add_button = QPushButton("Add URL")
        self.add_button.clicked.connect(self.add_url_entry)

        self.urls_layout = QVBoxLayout()

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.upload_urls)

        main_layout.addLayout(server_url_layout)
        main_layout.addWidget(self.add_button)
        main_layout.addLayout(self.urls_layout)
        main_layout.addWidget(self.submit_button)

    def toggle_editable(self, event):
        self.server_url_entry.setReadOnly(False)

    def add_url_entry(self):
        url_entry_widget = UrlEntryWidget(self)
        self.urls_layout.addWidget(url_entry_widget)
        self.url_entries.append(url_entry_widget)

    def remove_url_entry(self, url_entry):
        self.url_entries.remove(url_entry)

    def handle_upload_response(self, response):
        if response.status_code == 200:
            QMessageBox.information(self, "Success", "URLs uploaded successfully")
        else:
            QMessageBox.critical(self, "Error", f"Error uploading URLs: {response.text}")

    def upload_urls(self):
        server_url = self.server_url_entry.text()
        if not server_url:
            QMessageBox.warning(self, "Warning", "Please enter a server URL")
            return

        data_payload = self.get_data_payload()
        if not data_payload:
            return

        try:
            response = requests.post(server_url + '/upload', json=data_payload)
            self.handle_upload_response(response)
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error", f"Error uploading URLs: {str(e)}")

    def get_data_payload(self):
        data = []
        for url_entry in self.url_entries:
            url = url_entry.url_entry.text()
            title = url_entry.title_entry.text()
            description = url_entry.description_entry.text()
            category = url_entry.category_dropdown.currentText().lower().replace(" ", "_")

            if not url or not title or (category == "published_works" and not description):
                QMessageBox.warning(self, "Warning", "Please fill out all fields for each URL")
                return {}

            data.append({
                "url": url,
                "title": title,
                "description": description,
                "category": category
            })
        return data


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
