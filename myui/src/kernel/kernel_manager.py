from PyQt5.QtCore import QObject, pyqtSignal as Signal, QThread
import subprocess
import sys
import os
import tempfile
import io
import threading
import time

class KernelWorker(QObject):
    output_received = Signal(str)
    error_received = Signal(str)
    image_received = Signal(str)
    execution_finished = Signal()
    
    def __init__(self):
        super().__init__()
        self.process = None
        self.running = False
        self.read_thread = None
        self.stop_event = threading.Event()
        
    def start_kernel(self):
        if self.process is None or self.process.poll() is not None:
            self.stop_event.clear()
            self.process = subprocess.Popen(
                [sys.executable, '-i', '-c', '''
import sys
import traceback
import io

def execute(code):
    try:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        
        exec(code, globals())
        
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        return stdout_capture.getvalue(), stderr_capture.getvalue(), None
    except Exception as e:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        return "", traceback.format_exc(), str(e)

while True:
    try:
        line = input("__KERNEL_INPUT__")
        if line == "__KERNEL_EXIT__":
            break
        stdout, stderr, error = execute(line)
        print("__KERNEL_STDOUT__")
        print(stdout)
        print("__KERNEL_STDERR__")
        print(stderr)
        print("__KERNEL_ERROR__")
        print(error if error else "")
        print("__KERNEL_DONE__")
    except EOFError:
        break
'''],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.running = True
            
    def stop_kernel(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write("__KERNEL_EXIT__\n")
                self.process.stdin.flush()
            except Exception:
                pass
            
            try:
                self.process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.communicate()
            
            self.running = False
            
    def execute_code(self, code):
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write(code + "\n")
                self.process.stdin.flush()
                
                stdout_data = ""
                stderr_data = ""
                error_data = ""
                current_section = None
                
                while True:
                    line = self.process.stdout.readline()
                    if not line:
                        break
                        
                    if line.startswith("__KERNEL_STDOUT__"):
                        current_section = "stdout"
                        continue
                    elif line.startswith("__KERNEL_STDERR__"):
                        current_section = "stderr"
                        continue
                    elif line.startswith("__KERNEL_ERROR__"):
                        current_section = "error"
                        continue
                    elif line.startswith("__KERNEL_DONE__"):
                        break
                        
                    if current_section == "stdout":
                        stdout_data += line
                    elif current_section == "stderr":
                        stderr_data += line
                    elif current_section == "error":
                        error_data += line
                
                if stdout_data:
                    self.output_received.emit(stdout_data)
                if stderr_data:
                    self.output_received.emit(stderr_data)
                if error_data:
                    self.error_received.emit(error_data)
                    
                self.execution_finished.emit()
            except Exception as e:
                self.error_received.emit(str(e))

class KernelManager(QObject):
    output_received = Signal(str)
    error_received = Signal(str)
    image_received = Signal(str)
    status_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.status = 'idle'
        self.worker = KernelWorker()
        self.thread = QThread()
        
        self.worker.moveToThread(self.thread)
        self.worker.output_received.connect(self.on_output_received)
        self.worker.error_received.connect(self.on_error_received)
        self.worker.image_received.connect(self.on_image_received)
        self.worker.execution_finished.connect(self.on_execution_finished)
        
        self.thread.start()
        
    def start_kernel(self):
        self.status = 'starting'
        self.status_changed.emit(self.status)
        self.worker.start_kernel()
        self.status = 'idle'
        self.status_changed.emit(self.status)
        
    def stop_kernel(self):
        self.worker.stop_kernel()
        self.status = 'stopped'
        self.status_changed.emit(self.status)
        
    def execute_code(self, code):
        self.status = 'busy'
        self.status_changed.emit(self.status)
        self.worker.execute_code(code)
        
    def on_output_received(self, output):
        self.output_received.emit(output)
        
    def on_error_received(self, error):
        self.error_received.emit(error)
        
    def on_image_received(self, image_path):
        self.image_received.emit(image_path)
        
    def on_execution_finished(self):
        self.status = 'idle'
        self.status_changed.emit(self.status)
        
    def get_status(self):
        return self.status
        
    def cleanup(self):
        self.stop_kernel()
        self.thread.quit()
        self.thread.wait()