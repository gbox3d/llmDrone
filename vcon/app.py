"""
filename: app.py
author: gbox3d
create date: 2025-03-22

이 주석은 수정하지 마세요. 이외의 부분을 자유롭게 수정해도 좋습니다.
please do not modify this comment block. you can modify other than this block.
このコメントは変更しないでください。 それ以外の部分を自由に変更してもかまいません。
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import sys
import time

# 리팩토링된 모듈 임포트
from serial_port_manager import SerialPortManager
from voice_command_manager import VoiceCommandManager
from drone_control_manager import DroneControlManager

class DroneControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("드론 제어 애플리케이션")
        self.root.geometry("800x700")  # 높이를 더 크게 조정
        self.root.resizable(True, True)
        
        # 스타일 설정
        self.style = ttk.Style()
        self.style.configure('TButton', font=('Arial', 10))
        self.style.configure('TLabel', font=('Arial', 11))
        self.style.configure('TFrame', background='#f0f0f0')
        
        # 메인 프레임 생성
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 로그 텍스트 창 생성 (로그 관리자 모듈 초기화보다 먼저 해야 함)
        self.create_log_widget()
        
        # 모듈 초기화
        self.init_modules()
        
        # UI 구성
        self.create_ui()
    
    def init_modules(self):
        """각 모듈 초기화"""
        # 시리얼 포트 관리자 초기화
        self.serial_manager = SerialPortManager(self, self.log)
        
        # 드론 제어 관리자 초기화
        self.drone_controller = DroneControlManager(self, self.log, self.serial_manager)
        
        # 음성 명령 관리자 초기화
        self.voice_manager = VoiceCommandManager(self, self.log, self.drone_controller)
    
    def create_ui(self):
        """UI 구성"""
        # 상단 프레임 (포트 설정)
        top_frame = ttk.Frame(self.main_frame)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 포트 관리 프레임
        port_frame = ttk.LabelFrame(top_frame, text="포트 설정")
        port_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 시리얼 포트 관리자 위젯 생성
        self.serial_manager.create_widgets(port_frame)
        
        # 음성 제어 프레임
        voice_frame = ttk.LabelFrame(self.main_frame, text="음성 명령 제어")
        voice_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 음성 명령 관리자 위젯 생성
        self.voice_manager.create_widgets(voice_frame)
        
        # 중앙 프레임 (드론 컨트롤)
        control_frame = ttk.LabelFrame(self.main_frame, text="드론 제어")
        control_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 좌측 기본 명령 버튼 프레임
        cmd_frame = ttk.Frame(control_frame)
        cmd_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 드론 제어 관리자 위젯 생성
        self.drone_controller.create_widgets(cmd_frame)
        
        # 오른쪽 로그 프레임
        log_frame = ttk.Frame(control_frame)
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 로그 레이블
        log_label = ttk.Label(log_frame, text="드론 통신 로그")
        log_label.pack(anchor=tk.W, padx=5, pady=2)
        
        # 로그 텍스트 위젯 생성
        self.log_text = scrolledtext.ScrolledText(log_frame, width=40, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
    
    def create_log_widget(self):
        """로그 위젯 생성"""
        # 로그 텍스트 참조 변수만 생성 (실제 위젯은 create_ui에서 생성)
        self.log_text = None
    
    def log(self, message):
        """로그 창에 메시지 추가"""
        if not self.log_text:
            return
            
        self.log_text.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def after(self, ms, func, *args):
        """Tkinter의 after 메서드를 래핑"""
        return self.root.after(ms, func, *args)
        
    def on_drone_connected(self):
        """드론 연결 시 호출되는 콜백"""
        self.voice_manager.on_drone_connection_changed()
    
    def on_drone_disconnected(self):
        """드론 연결 해제 시 호출되는 콜백"""
        self.voice_manager.on_drone_connection_changed()
        
    def on_closing(self):
        """프로그램 종료 시 실행"""
        # 각 모듈 정리
        self.voice_manager.cleanup()
        self.serial_manager.cleanup()
        
        self.root.destroy()

def main():
    try:
        root = tk.Tk()
        app = DroneControlApp(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("오류", f"프로그램 실행 중 오류가 발생했습니다: {str(e)}")
        
if __name__ == "__main__":
    main()