"""
filename: llm.py
author: gbox3d
create date: 2025-03-22

이 주석은 수정하지 마세요. 이외의 부분을 자유롭게 수정해도 좋습니다.
please do not modify this comment block. you can modify other than this block.
このコメントは変更しないでください。 それ以外の部分を自由に変更してもかまいません。
"""

import os
import torch
from transformers import pipeline

class LLMChat:
    def __init__(self, model_name="google/gemma-3-1b-it", cache_dir="../model_cache", prompt_file="prompt.txt"):
        """
        LLM 채팅 모델을 초기화합니다.
        
        Args:
            model_name (str): 사용할 모델 이름
            cache_dir (str): 모델 캐시 디렉토리 경로
            prompt_file (str): 프롬프트 파일 경로
        """
        # 캐시 디렉토리 생성
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        # GPU 사용 여부 확인 및 출력
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Prepare to use {device}")
            
        # 모델 로드
        self.pipe = pipeline(
            "text-generation",
            model=model_name,
            device=device,
            torch_dtype=torch.bfloat16,
            model_kwargs={"cache_dir": cache_dir}
        )
        
        # 프롬프트 파일 로드
        self.system_prompt = self._load_prompt(prompt_file)
        
        print(f"모델 '{model_name}'이(가) 로드되었습니다. 캐시 디렉토리: {cache_dir}")
        
    def _load_prompt(self, prompt_file):
        """
        프롬프트 파일을 로드합니다.
        
        Args:
            prompt_file (str): 프롬프트 파일 경로
            
        Returns:
            str: 로드된 프롬프트 텍스트
        """
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"경고: 프롬프트 파일 '{prompt_file}'을 찾을 수 없습니다. 빈 프롬프트를 사용합니다.")
            return ""
    
    def chat(self, user_message):
        """
        사용자 메시지에 대한 응답을 생성합니다. 대화 누적 없이 단일 메시지만 처리합니다.
        
        Args:
            user_message (str): 사용자 메시지
            
        Returns:
            str: 모델의 응답
        """
        # 매번 새로운 메시지 구성 (대화 기록 유지 없음)
        messages = [
            [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": self.system_prompt}]
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": user_message}]
                }
            ]
        ]
        
        # 응답 생성
        output = self.pipe(messages, max_new_tokens=512)
        
        # 응답 텍스트 추출 (출력 형식에 맞게 수정)
        response_text = output[0]
        
        return response_text
    def parse_output(self, output):
        """
        모델 출력에서 assistant의 content만 추출합니다.
        
        Args:
            output (list): 모델 출력
        
        Returns:
            str: assistant의 content
        """
        try:
            # 이미 파싱된 출력을 사용
            generated_text = output[0]['generated_text']
            
            # assistant 역할의 메시지 찾기
            for message in generated_text:
                if message['role'] == 'assistant':
                    return message['content']
            
            # assistant 역할을 찾지 못한 경우
            return "Assistant 메시지를 찾을 수 없습니다."
        except Exception as e:
            return f"응답 처리 중 오류 발생: {e}"

# 사용 예시
if __name__ == "__main__":
    # LLMChat 인스턴스 생성
    chat_bot = LLMChat(
        model_name="google/gemma-3-1b-it",
        cache_dir="../model_cache",
        prompt_file="prompt.txt"
    )
    
    # 단일 대화 예시
    response = chat_bot.chat("드론을 이륙 시켜주세요")
    # print("모델 응답:", response)
    print(chat_bot.parse_output(response))
    
    
        