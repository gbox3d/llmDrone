import tkinter as tk
from tkinter import ttk, messagebox
import serial.tools.list_ports
import threading
import time

class SerialPortManager:
    def __init__(self, parent, log_callback):
        """시리얼 포트 관리자 초기화"""
        self.parent = parent
        self.log = log_callback
        self.drone = None
        self.connected = False
        self.check_thread = None
        
        # UI 컴포넌트 참조 저장
        self.port_combo = None
        self.connect_button = None
        self.disconnect_button = None
        self.scan_button = None
        self.status_var = None
        
    def create_widgets(self, frame):
        """포트 관리 위젯 생성"""
        # 시리얼 포트 레이블 및 콤보박스
        ttk.Label(frame, text="시리얼 포트:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.port_combo = ttk.Combobox(frame, width=20, state="readonly")
        self.port_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # 컨트롤 버튼
        self.scan_button = ttk.Button(frame, text="포트 스캔", command=self.scan_ports)
        self.scan_button.grid(row=0, column=2, padx=5, pady=5)
        
        self.connect_button = ttk.Button(frame, text="연결", command=self.connect_drone)
        self.connect_button.grid(row=0, column=3, padx=5, pady=5)
        
        self.disconnect_button = ttk.Button(frame, text="연결 해제", command=self.disconnect_drone, state=tk.DISABLED)
        self.disconnect_button.grid(row=0, column=4, padx=5, pady=5)
        
        # 상태 표시 레이블
        self.status_var = tk.StringVar()
        self.status_var.set("대기 중...")
        status_label = ttk.Label(frame, textvariable=self.status_var, font=('Arial', 10, 'italic'))
        status_label.grid(row=1, column=0, columnspan=5, sticky=tk.W, padx=5, pady=5)
        
        # 초기 포트 스캔
        self.scan_ports()
        
    def scan_ports(self):
        """시리얼 포트를 스캔하여 콤보박스에 표시"""
        ports = serial.tools.list_ports.comports()
        port_list = [f"{port.device}" for port in ports]
        
        if not port_list:
            self.port_combo['values'] = ["사용 가능한 포트 없음"]
            self.port_combo.current(0)
            self.connect_button.config(state=tk.DISABLED)
        else:
            self.port_combo['values'] = port_list
            self.port_combo.current(0)
            self.connect_button.config(state=tk.NORMAL)
            
        self.log("포트 스캔 완료: " + ", ".join(port_list) if port_list else "사용 가능한 포트 없음")
            
    def connect_drone(self):
        """선택한 포트에 드론 연결"""
        from CodingDrone.drone import Drone  # 필요할 때만 임포트
        
        port = self.port_combo.get()
        
        if port == "사용 가능한 포트 없음":
            messagebox.showerror("연결 오류", "사용 가능한 포트가 없습니다.")
            return
            
        self.log(f"포트 {port}에 연결 시도 중...")
        self.status_var.set(f"포트 {port}에 연결 중...")
        
        try:
            self.drone = Drone()
            self.drone.open(port)
            self.connected = True
            
            self.status_var.set(f"포트 {port}에 성공적으로 연결되었습니다.")
            self.log(f"드론이 포트 {port}에 성공적으로 연결되었습니다.")
            
            # 버튼 상태 변경
            self.connect_button.config(state=tk.DISABLED)
            self.disconnect_button.config(state=tk.NORMAL)
            self.port_combo.config(state=tk.DISABLED)
            self.scan_button.config(state=tk.DISABLED)
            
            # 이벤트 발생
            if hasattr(self.parent, "on_drone_connected"):
                self.parent.on_drone_connected()
            
            # 연결 상태 확인 스레드 시작
            self.check_thread = threading.Thread(target=self.check_connection, daemon=True)
            self.check_thread.start()
            
        except Exception as e:
            self.log(f"연결 실패: {str(e)}")
            self.status_var.set(f"연결 실패: {str(e)}")
            messagebox.showerror("연결 오류", f"드론 연결 중 오류가 발생했습니다: {str(e)}")
            
    def disconnect_drone(self):
        """드론 연결 해제"""
        if self.drone:
            try:
                self.drone.close()
                self.log("드론 연결이 해제되었습니다.")
                self.status_var.set("드론 연결이 해제되었습니다.")
            except Exception as e:
                self.log(f"연결 해제 중 오류: {str(e)}")
            finally:
                self.drone = None
                self.connected = False
                
                # 버튼 상태 초기화
                self.connect_button.config(state=tk.NORMAL)
                self.disconnect_button.config(state=tk.DISABLED)
                self.port_combo.config(state="readonly")
                self.scan_button.config(state=tk.NORMAL)
                
                # 이벤트 발생
                if hasattr(self.parent, "on_drone_disconnected"):
                    self.parent.on_drone_disconnected()
                
    def check_connection(self):
        """연결 상태를 주기적으로 확인"""
        while self.connected:
            # 여기에 드론 연결 상태 확인 로직 추가 (필요한 경우)
            time.sleep(1)
    
    def get_drone(self):
        """드론 객체 반환"""
        return self.drone
        
    def is_connected(self):
        """연결 상태 반환"""
        return self.connected
        
    def cleanup(self):
        """리소스 정리"""
        if self.connected:
            self.disconnect_drone()
