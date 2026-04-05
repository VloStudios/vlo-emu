import sys
import os
import subprocess
import requests
import zipfile

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal


QEMU_URL = "https://qemu.weilnetz.de/w64/2023/qemu-w64-setup-20230822.zip"
QEMU_DIR = "qemu"

ISO_URL = "https://osdn.net/projects/android-x86/downloads/74818/android-x86_64-9.0-r2.iso/"
ISO_PATH = "android.iso"
DISK_PATH = "android.qcow2"


class InstallerThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)

    def run(self):
        try:
            # 📦 1. Download QEMU
            self.status.emit("Downloading QEMU...")
            self.download_file(QEMU_URL, "qemu.zip", 0, 20)

            # 📂 2. Extract QEMU
            self.status.emit("Extracting QEMU...")
            with zipfile.ZipFile("qemu.zip", 'r') as zip_ref:
                zip_ref.extractall(QEMU_DIR)
            self.progress.emit(25)

            # 🌐 3. Download Android
            self.status.emit("Downloading Android...")
            self.download_file(ISO_URL, ISO_PATH, 25, 65)

            # 💾 4. Create disk
            self.status.emit("Creating virtual disk...")
            self.create_disk()
            self.progress.emit(75)

            # 🚀 5. Run VM
            self.status.emit("Launching Android...")
            self.run_vm()
            self.progress.emit(100)

            self.status.emit("Done 🚀")

        except Exception as e:
            self.status.emit(f"Error: {e}")

    def download_file(self, url, path, start, end):
        if os.path.exists(path):
            return

        r = requests.get(url, stream=True)
        total = int(r.headers.get('content-length', 0))
        downloaded = 0

        with open(path, "wb") as f:
            for chunk in r.iter_content(1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent = int(downloaded / total * (end - start))
                    self.progress.emit(start + percent)

    def find_qemu(self):
        for root, dirs, files in os.walk(QEMU_DIR):
            if "qemu-system-x86_64.exe" in files:
                return os.path.join(root, "qemu-system-x86_64.exe")
        return None

    def create_disk(self):
        if os.path.exists(DISK_PATH):
            return

        qemu_img = None
        for root, dirs, files in os.walk(QEMU_DIR):
            if "qemu-img.exe" in files:
                qemu_img = os.path.join(root, "qemu-img.exe")
                break

        subprocess.run([
            qemu_img, "create", "-f", "qcow2", DISK_PATH, "16G"
        ])

    def run_vm(self):
        qemu = self.find_qemu()

        subprocess.Popen([
            qemu,
            "-m", "2048",
            "-smp", "2",
            "-hda", DISK_PATH,
            "-cdrom", ISO_PATH,
            "-boot", "d"
        ])


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VloEmu Installer 😏")
        self.setGeometry(500, 300, 400, 200)

        layout = QVBoxLayout()

        self.label = QLabel(
            "Install Android Emulator\n\n"
            "Requirements:\n"
            "- 4 GB RAM\n"
            "- 15 GB Storage\n"
        )

        self.btn = QPushButton("Install")
        self.btn.clicked.connect(self.start)

        self.progress = QProgressBar()
        self.status = QLabel("Waiting...")

        layout.addWidget(self.label)
        layout.addWidget(self.btn)
        layout.addWidget(self.progress)
        layout.addWidget(self.status)

        self.setLayout(layout)

    def start(self):
        self.thread = InstallerThread()
        self.thread.progress.connect(self.progress.setValue)
        self.thread.status.connect(self.status.setText)
        self.thread.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
