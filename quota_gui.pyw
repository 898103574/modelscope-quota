# quota_gui.pyw
# 双击运行，不显示 DOS 窗口
import subprocess
import sys
import os

gui_path = os.path.join(os.path.dirname(__file__), "quota_gui.py")
pythonw = sys.executable.replace("python.exe", "pythonw.exe")
subprocess.run([pythonw, gui_path])
