import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import time
import json  # 설정 저장/불러오기용

class VoiceCommandManager:
    def __init__(self, parent, log_callback, drone_controller):
        """음성 명령 관리자 초기화"""
        self.parent = parent
        self.log = log_callback
        self.drone_controller = drone_controller
        
        # STT/LLM 관련 변수
        self.audio_recorder = None
        self.stt = None
        self.llm = None
        self.is_recording = False
        
        # 설정 변수 초기화 (기본값)
        self.stt_model_var = tk.StringVar(value="openai/whisper-large-v3-turbo")
        self.llm_model_var = tk.StringVar(value="google/gemma-3-1b-it")
        self.prompt_path_var = tk.StringVar(value="prompt.txt")
        self.cache_dir_var = tk.StringVar(value="../model_cache")
        
        # UI 컴포넌트 참조 저장 변수 초기화
        self.stt_model_entry = None
        self.llm_model_entry = None
        self.prompt_path_entry = None
        self.cache_dir_entry = None
        self.browse_button = None
        self.cache_browse_button = None
        self.load_stt_button = None
        self.load_llm_button = None
        self.stt_status_var = None
        self.llm_status_var = None
        self.voice_status_var = None
        self.voice_record_button = None
        self.recognized_command_var = None
        self.save_settings_button = None
        
    def create_widgets(self, frame):
        """음성 제어 위젯 생성"""
        # 저장된 설정 불러오기
        self.load_settings()
        
        # 캐시 디렉토리 확인 및 생성
        os.makedirs(self.cache_dir_var.get(), exist_ok=True)
        
        # 모델 로딩 프레임
        model_frame = ttk.Frame(frame)
        model_frame.grid(row=0, column=0, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # STT 모델 입력 및 로딩 버튼
        ttk.Label(model_frame, text="음성인식(STT) 모델:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.stt_model_entry = ttk.Entry(model_frame, textvariable=self.stt_model_var, width=30)
        self.stt_model_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        self.stt_status_var = tk.StringVar(value="로딩 안됨")
        ttk.Label(model_frame, textvariable=self.stt_status_var, font=('Arial', 10, 'italic')).grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        self.load_stt_button = ttk.Button(model_frame, text="STT 모델 로딩", command=self.load_stt_model)
        self.load_stt_button.grid(row=0, column=3, padx=5, pady=5)
        
        # LLM 모델 입력 및 로딩 버튼
        ttk.Label(model_frame, text="언어모델(LLM):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.llm_model_entry = ttk.Entry(model_frame, textvariable=self.llm_model_var, width=30)
        self.llm_model_entry.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        self.llm_status_var = tk.StringVar(value="로딩 안됨")
        ttk.Label(model_frame, textvariable=self.llm_status_var, font=('Arial', 10, 'italic')).grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        self.load_llm_button = ttk.Button(model_frame, text="LLM 모델 로딩", command=self.load_llm_model)
        self.load_llm_button.grid(row=1, column=3, padx=5, pady=5)
        
        # 프롬프트 파일 경로 입력 및 브라우징 버튼
        ttk.Label(model_frame, text="프롬프트 파일:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.prompt_path_entry = ttk.Entry(model_frame, textvariable=self.prompt_path_var, width=30)
        self.prompt_path_entry.grid(row=2, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        self.browse_button = ttk.Button(model_frame, text="찾아보기", command=self.browse_prompt_file)
        self.browse_button.grid(row=2, column=2, padx=5, pady=5)
        
        # 캐시 디렉토리 입력 및 브라우징 버튼
        ttk.Label(model_frame, text="캐시 디렉토리:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.cache_dir_entry = ttk.Entry(model_frame, textvariable=self.cache_dir_var, width=30)
        self.cache_dir_entry.grid(row=3, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        self.cache_browse_button = ttk.Button(model_frame, text="찾아보기", command=self.browse_cache_dir)
        self.cache_browse_button.grid(row=3, column=2, padx=5, pady=5)
        
        # 열 늘리기 설정
        model_frame.columnconfigure(1, weight=1)
        
        # 음성 제어 버튼 및 상태
        self.voice_status_var = tk.StringVar(value="음성 인식 준비되지 않음")
        voice_status_label = ttk.Label(frame, textvariable=self.voice_status_var, font=('Arial', 10, 'italic'))
        voice_status_label.grid(row=3, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        self.voice_record_button = ttk.Button(frame, text="음성 명령  시작", command=self.toggle_voice_recording, state=tk.DISABLED)
        self.voice_record_button.grid(row=4, column=0, padx=5, pady=5)
        
        # 음성 인식 결과 표시 레이블
        ttk.Label(frame, text="인식된 명령:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.recognized_command_var = tk.StringVar(value="-")
        recognized_command_label = ttk.Label(frame, textvariable=self.recognized_command_var, font=('Arial', 10, 'bold'))
        recognized_command_label.grid(row=5, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # 설정 저장 버튼
        save_frame = ttk.Frame(frame)
        save_frame.grid(row=6, column=0, columnspan=3, sticky=tk.E, padx=5, pady=10)
        
        self.save_settings_button = ttk.Button(save_frame, text="설정 저장", command=self.save_settings)
        self.save_settings_button.pack(side=tk.RIGHT, padx=5, pady=5)
        
    def load_stt_model(self):
        """STT 모델 로딩 버튼 핸들러"""
        if self.stt is not None:
            messagebox.showinfo("알림", "이미 STT 모델이 로딩되어 있습니다.")
            return
            
        # 모델 ID 가져오기
        model_id = self.stt_model_var.get().strip()
        if not model_id:
            messagebox.showerror("오류", "STT 모델 ID를 입력해주세요.")
            return
            
        # AudioRecorder 초기화 (먼저 한 번만 초기화)
        if self.audio_recorder is None:
            from stt import AudioRecorder
            self.audio_recorder = AudioRecorder()
            
        self.stt_status_var.set("로딩 중...")
        self.load_stt_button.config(state=tk.DISABLED)
        self.log(f"음성 인식(STT) 모델 '{model_id}'을 로딩합니다...")
        
        # STT 모델 초기화 (백그라운드 스레드에서 실행)
        self.stt_init_thread = threading.Thread(target=self._initialize_stt, args=(model_id,), daemon=True)
        self.stt_init_thread.start()
    
    def load_llm_model(self):
        """LLM 모델 로딩 버튼 핸들러"""
        if self.llm is not None:
            messagebox.showinfo("알림", "이미 LLM 모델이 로딩되어 있습니다.")
            return
        
        # 모델명 가져오기
        model_name = self.llm_model_var.get().strip()
        if not model_name:
            messagebox.showerror("오류", "LLM 모델명을 입력해주세요.")
            return
            
        # 프롬프트 파일 경로 가져오기
        prompt_file = self.prompt_path_var.get().strip()
        if not prompt_file:
            messagebox.showerror("오류", "프롬프트 파일 경로를 입력해주세요.")
            return
            
        self.llm_status_var.set("로딩 중...")
        self.load_llm_button.config(state=tk.DISABLED)
        self.log(f"언어 모델(LLM) '{model_name}'을 로딩합니다...")
        self.log(f"프롬프트 파일: {prompt_file}")
        
        # LLM 모델 초기화 (백그라운드 스레드에서 실행)
        self.llm_init_thread = threading.Thread(target=self._initialize_llm, args=(model_name, prompt_file), daemon=True)
        self.llm_init_thread.start()
    
    def browse_prompt_file(self):
        """프롬프트 파일 브라우징"""
        file_path = filedialog.askopenfilename(
            title="프롬프트 파일 선택",
            filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")],
            initialdir=os.getcwd()  # 현재 실행 경로를 시작 위치로 설정
        )
        if file_path:
            self.prompt_path_var.set(file_path)
            self.log(f"프롬프트 파일이 선택되었습니다: {file_path}")
            
    def browse_cache_dir(self):
        """캐시 디렉토리 브라우징"""
        dir_path = filedialog.askdirectory(
            title="모델 캐시 디렉토리 선택",
            initialdir=os.getcwd()  # 현재 실행 경로를 시작 위치로 설정
        )
        if dir_path:
            self.cache_dir_var.set(dir_path)
            # 디렉토리가 존재하는지 확인하고 없으면 생성
            os.makedirs(dir_path, exist_ok=True)
            self.log(f"모델 캐시 디렉토리가 설정되었습니다: {dir_path}")
            
    def save_settings(self):
        """현재 설정을 파일에 저장"""
        try:
            settings = {
                'stt_model': self.stt_model_var.get(),
                'llm_model': self.llm_model_var.get(),
                'prompt_path': self.prompt_path_var.get(),
                'cache_dir': self.cache_dir_var.get()
            }
            
            with open('voice_settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
                
            self.log("설정이 성공적으로 저장되었습니다.")
            messagebox.showinfo("설정 저장", "현재 설정이 성공적으로 저장되었습니다.")
        except Exception as e:
            self.log(f"설정 저장 중 오류 발생: {str(e)}")
            messagebox.showerror("저장 오류", f"설정을 저장하는 중 오류가 발생했습니다: {str(e)}")
    
    def load_settings(self):
        """저장된 설정 파일 불러오기"""
        try:
            if os.path.exists('voice_settings.json'):
                with open('voice_settings.json', 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 설정값 적용
                if 'stt_model' in settings and settings['stt_model']:
                    self.stt_model_var.set(settings['stt_model'])
                    
                if 'llm_model' in settings and settings['llm_model']:
                    self.llm_model_var.set(settings['llm_model'])
                    
                if 'prompt_path' in settings and settings['prompt_path']:
                    self.prompt_path_var.set(settings['prompt_path'])
                    
                if 'cache_dir' in settings and settings['cache_dir']:
                    self.cache_dir_var.set(settings['cache_dir'])
                    # 캐시 디렉토리는 생성 시점을 create_widgets로 이동
                
                self.log("저장된 설정을 불러왔습니다.")
        except Exception as e:
            self.log(f"설정 불러오기 중 오류 발생: {str(e)}")
            # 오류가 발생해도 기본값으로 계속 진행
    
    def _initialize_stt(self, model_id):
        """STT 모델 초기화 (백그라운드 스레드)"""
        try:
            from stt import SpeechToText
            self.stt = SpeechToText(
                model_id=model_id,
                cache_dir=self.cache_dir_var.get(),
                language="korean"
            )
            self.log(f"음성 인식(STT) 시스템이 초기화되었습니다. 모델: {model_id}")
            self.parent.after(0, self._update_stt_status, True)
        except Exception as e:
            self.log(f"STT 초기화 오류: {str(e)}")
            self.parent.after(0, self._update_stt_status, False)
    
    def _initialize_llm(self, model_name, prompt_file):
        """LLM 모델 초기화 (백그라운드 스레드)"""
        try:
            from llm import LLMChat
            self.llm = LLMChat(
                model_name=model_name,
                cache_dir=self.cache_dir_var.get(),
                prompt_file=prompt_file
            )
            self.log(f"언어 모델(LLM) 시스템이 초기화되었습니다. 모델: {model_name}")
            self.parent.after(0, self._update_llm_status, True)
        except Exception as e:
            self.log(f"LLM 초기화 오류: {str(e)}")
            self.parent.after(0, self._update_llm_status, False)
    
    def _update_stt_status(self, success):
        """STT 상태 업데이트"""
        if success:
            self.stt_status_var.set("로딩 완료")
            self.load_stt_button.config(state=tk.DISABLED)
            self.stt_model_entry.config(state=tk.DISABLED)  # 입력 필드 비활성화
            # STT가 로딩 완료되었어도 LLM이 로딩되지 않았으면 캐시 디렉토리는 여전히 수정 가능해야 함
            if self.llm is None:
                self.cache_dir_entry.config(state=tk.NORMAL)
                self.cache_browse_button.config(state=tk.NORMAL)
        else:
            self.stt_status_var.set("로딩 실패")
            self.load_stt_button.config(state=tk.NORMAL)
            self.stt = None
        
        # 음성 제어 버튼 상태 업데이트
        self._update_voice_control_ui()
    
    def _update_llm_status(self, success):
        """LLM 상태 업데이트"""
        if success:
            self.llm_status_var.set("로딩 완료")
            self.load_llm_button.config(state=tk.DISABLED)
            self.llm_model_entry.config(state=tk.DISABLED)  # 입력 필드 비활성화
            self.prompt_path_entry.config(state=tk.DISABLED)  # 입력 필드 비활성화
            self.browse_button.config(state=tk.DISABLED)  # 브라우즈 버튼 비활성화
            self.cache_dir_entry.config(state=tk.DISABLED)  # 캐시 디렉토리 입력 필드 비활성화
            self.cache_browse_button.config(state=tk.DISABLED)  # 캐시 디렉토리 브라우즈 버튼 비활성화
        else:
            self.llm_status_var.set("로딩 실패")
            self.load_llm_button.config(state=tk.NORMAL)
            self.llm = None
        
        # 음성 제어 버튼 상태 업데이트
        self._update_voice_control_ui()
    
    def _update_voice_control_ui(self):
        """음성 제어 UI 업데이트"""
        if self.stt is not None and self.llm is not None and self.drone_controller.is_drone_connected():
            # STT와 LLM 모두 초기화되고 드론이 연결되어 있으면 버튼 활성화
            self.voice_record_button.config(state=tk.NORMAL)
            self.voice_status_var.set("음성 인식 준비 완료")
        else:
            self.voice_record_button.config(state=tk.DISABLED)
            if not self.drone_controller.is_drone_connected():
                self.voice_status_var.set("드론이 연결되지 않음")
            else:
                self.voice_status_var.set("음성 인식 준비되지 않음")
    
    def toggle_voice_recording(self):
        """음성 녹음 시작/중지 토글"""
        if not self.drone_controller.is_drone_connected():
            messagebox.showerror("연결 오류", "드론이 연결되어 있지 않습니다.")
            return
            
        if self.stt is None or self.llm is None:
            messagebox.showerror("초기화 오류", "STT와 LLM 모델이 모두 로딩되어야 합니다. 각 모델 로딩 버튼을 클릭해주세요.")
            return
        
        # 녹음 중이면 중지하고 처리
        if self.is_recording:
            self.stop_recording_and_process()
        # 녹음 중이 아니면 시작
        else:
            self.start_recording()
    
    def start_recording(self):
        """음성 녹음 시작"""
        try:
            self.is_recording = True
            self.voice_status_var.set("녹음 중... (클릭하여 중지)")
            self.voice_record_button.config(text="음성 녹음 중지")
            
            # 녹음 시작
            self.audio_recorder.start_recording()
            self.log("음성 녹음이 시작되었습니다. 명령을 말한 후 버튼을 다시 클릭하세요.")
            
        except Exception as e:
            self.log(f"음성 녹음 시작 오류: {str(e)}")
            self.is_recording = False
            self.voice_status_var.set("녹음 오류 발생")
            self.voice_record_button.config(text="음성 녹음 시작")
    
    def stop_recording_and_process(self):
        """음성 녹음 중지 및 처리"""
        if not self.is_recording:
            return
            
        try:
            self.is_recording = False
            self.voice_status_var.set("녹음 중지, 처리 중...")
            self.voice_record_button.config(text="음성 녹음 시작")
            self.voice_record_button.config(state=tk.DISABLED)  # 처리 중 비활성화
            
            # 녹음 중지 및 파일 가져오기
            audio_file = self.audio_recorder.stop_recording()
            
            if audio_file:
                # 처리 스레드 시작
                process_thread = threading.Thread(
                    target=self.process_audio_file,
                    args=(audio_file,),
                    daemon=True
                )
                process_thread.start()
            else:
                self.log("녹음된 오디오가 없습니다.")
                self.voice_status_var.set("음성 인식 준비 완료")
                self.voice_record_button.config(state=tk.NORMAL)
                
        except Exception as e:
            self.log(f"음성 녹음 중지 오류: {str(e)}")
            self.voice_status_var.set("음성 인식 준비 완료")
            self.voice_record_button.config(state=tk.NORMAL)
    
    def process_audio_file(self, audio_file):
        """오디오 파일 처리 (별도 스레드에서 실행)"""
        try:
            # 음성을 텍스트로 변환
            text = self.stt.transcribe(audio_file)
            self.log(f"인식된 음성: {text}")
            
            # LLM으로 명령어 처리
            response = self.llm.chat(text)
            command = self.parse_llm_response(response)
            
            # UI 업데이트 (메인 스레드에서 실행)
            self.parent.after(0, lambda: self.recognized_command_var.set(command))
            self.log(f"처리된 명령: {command}")
            
            # 명령어에 따라 드론 제어
            self.drone_controller.execute_drone_command(command)
            
            # 임시 파일 삭제
            try:
                os.unlink(audio_file)
            except:
                pass
                
            # UI 업데이트 (메인 스레드에서 실행)
            self.parent.after(0, self.update_ui_after_processing)
            
        except Exception as e:
            self.log(f"음성 처리 오류: {str(e)}")
            # UI 업데이트 (메인 스레드에서 실행)
            self.parent.after(0, self.update_ui_after_processing)
    
    def update_ui_after_processing(self):
        """처리 후 UI 업데이트"""
        self.voice_status_var.set("음성 인식 준비 완료")
        self.voice_record_button.config(state=tk.NORMAL)
    
    def parse_llm_response(self, response):
        """LLM 응답 파싱"""
        try:
            # LLM 출력 구조가 문자열이라면 그대로 반환
            if isinstance(response, str):
                return response.strip()
            
            # LLM 클래스의 parse_output 메서드를 사용
            return self.llm.parse_output(response)
            
        except Exception as e:
            self.log(f"LLM 응답 파싱 오류: {str(e)}")
            return "알 수 없는 명령"
    
    def on_drone_connection_changed(self):
        """드론 연결 상태 변경 시 호출되는 콜백"""
        self._update_voice_control_ui()
        
    def cleanup(self):
        """리소스 정리"""
        # 음성 녹음 중지
        if self.is_recording and hasattr(self, 'audio_recorder') and self.audio_recorder:
            self.audio_recorder.stop_recording()
            self.is_recording = False
            
        # 오디오 레코더 정리
        if hasattr(self, 'audio_recorder') and self.audio_recorder:
            self.audio_recorder.close()