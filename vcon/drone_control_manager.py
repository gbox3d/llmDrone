import tkinter as tk
from tkinter import ttk, messagebox

class DroneControlManager:
    def __init__(self, parent, log_callback, serial_manager):
        """드론 제어 관리자 초기화"""
        self.parent = parent
        self.log = log_callback
        self.serial_manager = serial_manager
        
    def create_widgets(self, frame):
        """드론 제어 위젯 생성"""
        # 기본 명령 버튼들
        cmd_buttons = [
            ("이륙", self.takeoff),
            ("착륙", self.landing),
            ("위로", self.move_up),
            ("아래로", self.move_down),
            ("왼쪽", self.move_left),
            ("오른쪽", self.move_right),
            ("앞으로", self.move_forward),
            ("뒤로", self.move_backward),
            ("호버링", self.hover),
            ("긴급 정지", self.emergency_stop)
        ]
        
        for i, (text, command) in enumerate(cmd_buttons):
            row = i // 2
            col = i % 2
            btn = ttk.Button(frame, text=text, command=command, width=15)
            btn.grid(row=row, column=col, padx=10, pady=10, sticky=tk.NSEW)
            
        # 그리드 설정
        for i in range(5):
            frame.rowconfigure(i, weight=1)
        for i in range(2):
            frame.columnconfigure(i, weight=1)
            
    def is_drone_connected(self):
        """드론 연결 상태 확인"""
        return self.serial_manager.is_connected()
    
    def get_drone(self):
        """드론 객체 반환"""
        return self.serial_manager.get_drone()
    
    def check_drone_connected(self):
        """드론 연결 상태 확인 및 메시지 표시"""
        if not self.is_drone_connected():
            messagebox.showerror("연결 오류", "드론이 연결되어 있지 않습니다.")
            return False
        return True
    
    def execute_drone_command(self, command):
        """드론 명령 실행"""
        if not self.check_drone_connected():
            return
            
        try:
            drone = self.get_drone()
            if not drone:
                return
                
            command = command.strip().lower()
            
            if command == "takeoff":
                self.log("명령 실행: 이륙")
                drone.sendTakeOff()
                
            elif command == "landing":
                self.log("명령 실행: 착륙")
                drone.sendLanding()
                
            elif command == "move up":
                self.log("명령 실행: 상승")
                drone.sendControlPosition(0, 0, 0.5, 1, 0, 0)
                
            elif command == "move down":
                self.log("명령 실행: 하강")
                drone.sendControlPosition(0, 0, -0.5, 1, 0, 0)
                
            elif command == "move left":
                self.log("명령 실행: 왼쪽으로 이동")
                drone.sendControlPosition(0, -1.0, 0, 0.5, 0, 0)
                
            elif command == "move right":
                self.log("명령 실행: 오른쪽으로 이동")
                drone.sendControlPosition(0, 1.0, 0, 0.5, 0, 0)
                
            elif command == "move forward":
                self.log("명령 실행: 앞으로 이동")
                drone.sendControlPosition(1.0, 0, 0, 0.5, 0, 0)
                
            elif command == "move backward":
                self.log("명령 실행: 뒤로 이동")
                drone.sendControlPosition(-1.0, 0, 0, 0.5, 0, 0)
                
            elif command == "hovering":
                self.log("명령 실행: 호버링")
                drone.sendControlWhile(0, 0, 0, 0, 1000)
                
            elif command == "stop":
                self.log("명령 실행: 긴급 정지")
                drone.sendStop()
                
            elif command.startswith("control"):
                parts = command.split()
                if len(parts) == 5:  # control <roll> <pitch> <yaw> <throttle>
                    _, roll, pitch, yaw, throttle = parts
                    self.log(f"명령 실행: 제어 (롤={roll}, 피치={pitch}, 요={yaw}, 스로틀={throttle})")
                    drone.sendControl(int(roll), int(pitch), int(yaw), int(throttle), 1000)
                else:
                    self.log(f"잘못된 제어 명령 형식: {command}")
                    drone.sendControlWhile(0, 0, 0, 0, 1000)  # 안전을 위해 호버링
                
            elif command.startswith("position"):
                parts = command.split()
                if len(parts) == 6:  # position <x> <y> <z> <yaw> <pitch>
                    _, x, y, z, yaw, pitch = parts
                    self.log(f"명령 실행: 위치 (x={x}, y={y}, z={z}, 요={yaw}, 피치={pitch})")
                    drone.sendControlPosition(float(x), float(y), float(z), float(yaw), float(pitch), 0)
                else:
                    self.log(f"잘못된 위치 명령 형식: {command}")
                    drone.sendControlWhile(0, 0, 0, 0, 1000)  # 안전을 위해 호버링
                
            elif command.startswith("heading"):
                parts = command.split()
                if len(parts) == 3:  # heading <yaw> <pitch>
                    _, yaw, pitch = parts
                    self.log(f"명령 실행: 방향 (요={yaw}, 피치={pitch})")
                    drone.sendControlPosition(0, 0, 0, float(yaw), float(pitch), 0)
                else:
                    self.log(f"잘못된 방향 명령 형식: {command}")
                    drone.sendControlWhile(0, 0, 0, 0, 1000)  # 안전을 위해 호버링
                
            else:
                self.log(f"인식되지 않은 명령: {command}, 호버링으로 대체")
                drone.sendControlWhile(0, 0, 0, 0, 1000)  # 안전을 위해 호버링
                
        except Exception as e:
            self.log(f"명령 실행 중 오류: {str(e)}")
            try:
                # 오류 발생 시 안전을 위해 호버링
                drone = self.get_drone()
                if drone:
                    drone.sendControlWhile(0, 0, 0, 0, 1000)
            except:
                pass
    
    # 드론 제어 명령 함수들
    def takeoff(self):
        """드론 이륙"""
        if not self.check_drone_connected():
            return
        try:
            self.log("명령 실행: 이륙")
            self.get_drone().sendTakeOff()
        except Exception as e:
            self.log(f"이륙 명령 실행 중 오류: {str(e)}")
            
    def landing(self):
        """드론 착륙"""
        if not self.check_drone_connected():
            return
        try:
            self.log("명령 실행: 착륙")
            self.get_drone().sendLanding()
        except Exception as e:
            self.log(f"착륙 명령 실행 중 오류: {str(e)}")
            
    def move_up(self):
        """드론 상승"""
        if not self.check_drone_connected():
            return
        try:
            self.log("명령 실행: 상승")
            self.get_drone().sendControlPosition(0, 0, 0.5, 1, 0, 0)
        except Exception as e:
            self.log(f"상승 명령 실행 중 오류: {str(e)}")
            
    def move_down(self):
        """드론 하강"""
        if not self.check_drone_connected():
            return
        try:
            self.log("명령 실행: 하강")
            self.get_drone().sendControlPosition(0, 0, -0.5, 1, 0, 0)
        except Exception as e:
            self.log(f"하강 명령 실행 중 오류: {str(e)}")
            
    def move_left(self):
        """드론 왼쪽 이동"""
        if not self.check_drone_connected():
            return
        try:
            self.log("명령 실행: 왼쪽으로 이동")
            self.get_drone().sendControlPosition(0, -1.0, 0, 0.5, 0, 0)
        except Exception as e:
            self.log(f"왼쪽 이동 명령 실행 중 오류: {str(e)}")
            
    def move_right(self):
        """드론 오른쪽 이동"""
        if not self.check_drone_connected():
            return
        try:
            self.log("명령 실행: 오른쪽으로 이동")
            self.get_drone().sendControlPosition(0, 1.0, 0, 0.5, 0, 0)
        except Exception as e:
            self.log(f"오른쪽 이동 명령 실행 중 오류: {str(e)}")
            
    def move_forward(self):
        """드론 앞으로 이동"""
        if not self.check_drone_connected():
            return
        try:
            self.log("명령 실행: 앞으로 이동")
            self.get_drone().sendControlPosition(1.0, 0, 0, 0.5, 0, 0)
        except Exception as e:
            self.log(f"앞으로 이동 명령 실행 중 오류: {str(e)}")
            
    def move_backward(self):
        """드론 뒤로 이동"""
        if not self.check_drone_connected():
            return
        try:
            self.log("명령 실행: 뒤로 이동")
            self.get_drone().sendControlPosition(-1.0, 0, 0, 0.5, 0, 0)
        except Exception as e:
            self.log(f"뒤로 이동 명령 실행 중 오류: {str(e)}")
            
    def hover(self):
        """드론 호버링"""
        if not self.check_drone_connected():
            return
        try:
            self.log("명령 실행: 호버링")
            self.get_drone().sendControlWhile(0, 0, 0, 0, 1000)
        except Exception as e:
            self.log(f"호버링 명령 실행 중 오류: {str(e)}")
            
    def emergency_stop(self):
        """드론 긴급 정지"""
        if not self.check_drone_connected():
            return
        try:
            self.log("명령 실행: 긴급 정지")
            self.get_drone().sendStop()
        except Exception as e:
            self.log(f"긴급 정지 명령 실행 중 오류: {str(e)}")
