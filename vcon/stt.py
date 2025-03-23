"""
filename: stt.py
author: gbox3d
create date: 2025-03-22

이 주석은 수정하지 마세요. 이외의 부분을 자유롭게 수정해도 좋습니다.
please do not modify this comment block. you can modify other than this block.
このコメントは変更しないでください。 それ以外の部分を自由に変更してもかまいません。
"""

import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import pyaudio
import wave
import numpy as np
import time
import os
import tempfile
import threading
import scipy.io.wavfile as wavfile


class AudioRecorder:
    """오디오 녹음을 처리하는 클래스"""
    
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.frames = []
        self.is_recording = False
        self.record_thread = None
        
    def start_recording(self):
        """녹음 시작"""
        self.is_recording = True
        self.frames = []
        self.stream = self.audio.open(
            format=pyaudio.paInt16, 
            channels=1,
            rate=16000,  # Whisper 모델에 최적화된 샘플레이트
            input=True,
            frames_per_buffer=1024
        )
        
        print("녹음 중... (종료하려면 Enter 키를 누르세요)")
        
        # 녹음 스레드 시작
        self.record_thread = threading.Thread(target=self._record)
        self.record_thread.start()
    
    def _record(self):
        """녹음 처리 (별도 스레드에서 실행)"""
        while self.is_recording:
            data = self.stream.read(1024)
            self.frames.append(data)
    
    def stop_recording(self):
        """녹음 중지"""
        if not self.is_recording:
            return None
            
        self.is_recording = False
        
        # 녹음 스레드가 종료될 때까지 대기
        if self.record_thread:
            self.record_thread.join()
        
        # 스트림 정리
        self.stream.stop_stream()
        self.stream.close()
        
        # 녹음된 데이터가 없으면 None 반환
        if not self.frames:
            return None
            
        # 임시 파일로 저장
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        wf = wave.open(temp_file.name, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        
        print("녹음 완료!")
        return temp_file.name
        
    def close(self):
        """리소스 정리"""
        self.audio.terminate()


class SpeechToText:
    """음성 인식(STT) 클래스"""
    
    def __init__(self, model_id="openai/whisper-large-v3-turbo", device=None, language="korean", cache_dir="../model_cache"):
        """
        STT 클래스 초기화
        
        Args:
            model_id (str): 사용할 모델 ID (예: "openai/whisper-large-v3-turbo", "facebook/wav2vec2-large-960h")
            device (str, optional): 사용할 장치 (None이면 자동 감지)
            language (str, optional): 인식할 언어
            cache_dir (str, optional): 모델 캐시 디렉토리 (기본값: "../model_cache")
        """
        self.model_id = model_id
        self.language = language
        self.cache_dir = cache_dir
        
        # 캐시 디렉토리가 존재하지 않으면 생성
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 디바이스 설정
        if device is None:
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        
        print(f"사용 중인 디바이스: {self.device}")
        print(f"선택한 모델: {self.model_id}")
        
        # 모델 및 프로세서 로드
        self._load_model()
        
    def _load_model(self):
        """모델과 프로세서 로드"""
        print(f"모델 로딩 중... (캐시 디렉토리: {self.cache_dir})")
        
        try:
            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                self.model_id,
                torch_dtype=self.torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True,
                cache_dir=self.cache_dir
            )
            self.model.to(self.device)
            
            self.processor = AutoProcessor.from_pretrained(
                self.model_id,
                cache_dir=self.cache_dir
            )
            
            # 파이프라인 생성
            self.pipeline = pipeline(
                "automatic-speech-recognition",
                model=self.model,
                tokenizer=self.processor.tokenizer,
                feature_extractor=self.processor.feature_extractor,
                torch_dtype=self.torch_dtype,
                device=self.device
            )
            
            print("모델 및 프로세서 불러오기 완료")
        except Exception as e:
            print(f"모델 로딩 중 오류 발생: {str(e)}")
            raise
    
    def transcribe(self, audio_file, language=None):
        """
        오디오 파일을 텍스트로 변환
        
        Args:
            audio_file (str): 오디오 파일 경로
            language (str, optional): 인식할 언어 (None이면 초기화 시 설정한 언어 사용)
            
        Returns:
            str: 인식된 텍스트
        """
        if not audio_file:
            return "녹음된 오디오가 없습니다."
        
        # 파일이 존재하는지 확인
        if not os.path.exists(audio_file):
            return f"오디오 파일을 찾을 수 없습니다: {audio_file}"
        
        lang = language if language is not None else self.language
        
        print(f"음성을 텍스트로 변환 중... (언어: {lang})")
        
        try:
            # WAV 파일을 직접 읽어서 numpy 배열로 변환 (ffmpeg 의존성 제거)
            sample_rate, audio_data = wavfile.read(audio_file)
            
            # 16비트 정수를 float32로 변환 (-1.0 ~ 1.0 범위)
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            
            # 스테레오인 경우 모노로 변환
            if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # 오디오 데이터를 Transformers 파이프라인에 직접 전달
            result = self.pipeline(
                {"array": audio_data, "sampling_rate": sample_rate}, 
                generate_kwargs={"language": lang}
            )
            
            return result["text"]
            
        except Exception as e:
            print(f"\n[오류] 변환 중 오류 발생: {str(e)}")
            return f"오류: {str(e)}"


def main():
    """메인 함수: 실시간 음성 인식 예제"""
    
    print("=== 음성 인식(STT) 프로그램 ===")
    print("\n모델 ID 예시:")
    print("- openai/whisper-large-v3-turbo")
    print("- openai/whisper-medium")
    print("- openai/whisper-small")
    print("- facebook/wav2vec2-large-960h")
    
    model_id = input("\n사용할 모델 ID를 입력하세요 (기본값: openai/whisper-large-v3-turbo): ").strip() or "openai/whisper-large-v3-turbo"
    
    # 캐시 디렉토리 설정
    cache_dir = input("\n모델 캐시 디렉토리를 입력하세요 (기본값: ../model_cache): ").strip() or "../model_cache"
    
    try:
        # STT 객체 초기화
        stt = SpeechToText(model_id=model_id, cache_dir=cache_dir)
        
        # 오디오 레코더 초기화
        recorder = AudioRecorder()
        
        print("\n실시간 음성 인식 시작")
        
        while True:
            print("\n녹음을 시작하려면 Enter 키를 누르세요...")
            input()  # 엔터 키를 기다림
            
            # 녹음 시작
            recorder.start_recording()
            
            # 다시 엔터 키를 누를 때까지 대기
            input()
            
            # 녹음 중지
            audio_file = recorder.stop_recording()
            
            if audio_file:
                # 음성을 텍스트로 변환
                text = stt.transcribe(audio_file)
                print("인식된 텍스트:", text)
                
                # 임시 파일 삭제
                os.unlink(audio_file)
            
    except KeyboardInterrupt:
        print("\n프로그램 종료")
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
    finally:
        if 'recorder' in locals():
            recorder.close()


if __name__ == "__main__":
    main()