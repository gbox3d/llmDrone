"""
filename: hf_model_downloader.py
author: gbox3d
create date: 2025-03-22

이 주석은 수정하지 마세요. 이외의 부분을 자유롭게 수정해도 좋습니다.
please do not modify this comment block. you can modify other than this block.
このコメントは変更しないでください。 それ以外の部分を自由に変更してもかまいません。
"""



from dotenv import load_dotenv
import os
import argparse
from transformers import AutoConfig

# Dictionary mapping model domains to their respective model classes
MODEL_CLASSES = {
    "causal_lm": "AutoModelForCausalLM",  # GPT-like, Gemma, etc.
    "seq2seq_lm": "AutoModelForSeq2SeqLM",  # T5, BART, etc.
    "speech_recognition": "AutoModelForSpeechRecognition",  # Whisper
    "vision_text": "AutoModelForVisionTextDual",  # CLIP, etc.
    "image_classification": "AutoModelForImageClassification",  # ViT, etc.
    "object_detection": "AutoModelForObjectDetection",  # DETR, etc.
    "masked_lm": "AutoModelForMaskedLM",  # BERT, RoBERTa, etc.
}

def get_model_domain(model_id):
    """
    Determine the most appropriate model domain based on model_id.
    This is a heuristic approach and may need refinements.
    """
    model_id_lower = model_id.lower()
    
    if any(name in model_id_lower for name in ["gpt", "llama", "gemma", "mistral", "phi"]):
        return "causal_lm"
    elif any(name in model_id_lower for name in ["t5", "bart", "pegasus"]):
        return "seq2seq_lm"
    elif any(name in model_id_lower for name in ["whisper", "wav2vec", "hubert"]):
        return "speech_recognition"
    elif any(name in model_id_lower for name in ["clip", "blip"]):
        return "vision_text"
    elif any(name in model_id_lower for name in ["vit", "deit"]):
        return "image_classification"
    elif any(name in model_id_lower for name in ["detr", "yolo"]):
        return "object_detection"
    elif any(name in model_id_lower for name in ["bert", "roberta", "albert"]):
        return "masked_lm"
    else:
        # Try to determine from model config
        try:
            config = AutoConfig.from_pretrained(model_id)
            model_type = config.model_type
            
            # Map model_type to domain
            if model_type in ["gpt2", "gpt_neo", "llama", "gemma", "mistral"]:
                return "causal_lm"
            elif model_type in ["t5", "bart"]:
                return "seq2seq_lm"
            elif model_type in ["whisper", "wav2vec2"]:
                return "speech_recognition"
            elif model_type in ["bert", "roberta", "albert"]:
                return "masked_lm"
        except:
            pass
            
        # Default to causal_lm if cannot determine
        print(f"Could not determine model domain for {model_id}, defaulting to causal_lm")
        return "causal_lm"

def download_model(model_id, cache_dir="./model_cache", domain=None, use_token=True, torch_dtype="auto"):
    """
    Download and cache a Hugging Face model and its tokenizer or processor.
    
    Args:
        model_id (str): The model ID on Hugging Face Hub
        cache_dir (str): Directory to store the downloaded model
        domain (str, optional): Model domain (causal_lm, speech_recognition, etc.)
                               If None, will try to auto-detect
        use_token (bool): Whether to use API token for authentication
        torch_dtype (str): Torch data type to use for the model
    
    Returns:
        tuple: (model, tokenizer_or_processor)
    """
    # Load environment variables
    load_dotenv('.env')
    token = os.getenv("HUGGINGFACEHUB_API_TOKEN") if use_token else None
    
    # Create cache directory if it doesn't exist
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        print(f"Created cache directory: {cache_dir}")
    
    # Determine model domain if not provided
    if domain is None:
        domain = get_model_domain(model_id)
    
    print(f"Loading model '{model_id}' as {domain} type")
    
    # Import the appropriate model class
    model_class_name = MODEL_CLASSES.get(domain, "AutoModelForCausalLM")
    try:
        ModelClass = getattr(__import__("transformers", fromlist=[model_class_name]), model_class_name)
    except (ImportError, AttributeError):
        print(f"Could not import {model_class_name}, falling back to AutoModelForCausalLM")
        from transformers import AutoModelForCausalLM
        ModelClass = AutoModelForCausalLM
    
    # Common arguments for model loading
    model_args = {
        "pretrained_model_name_or_path": model_id,
        "cache_dir": cache_dir,
        "torch_dtype": torch_dtype
    }
    
    # Add token if needed
    if token:
        model_args["token"] = token
    
    # Load the model
    model = ModelClass.from_pretrained(**model_args)
    
    # For ASR models like Whisper, use processor instead of tokenizer
    if domain == "speech_recognition":
        from transformers import AutoProcessor
        processor = AutoProcessor.from_pretrained(
            model_id, 
            cache_dir=cache_dir, 
            token=token if use_token else None
        )
        tokenizer_or_processor = processor
        print(f"Loaded processor for ASR model '{model_id}'")
    else:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_id, 
            cache_dir=cache_dir, 
            token=token if use_token else None
        )
        tokenizer_or_processor = tokenizer
        print(f"Loaded tokenizer for model '{model_id}'")
    
    print(f"Model and {'processor' if domain == 'speech_recognition' else 'tokenizer'} for '{model_id}' "
          f"have been downloaded and cached in '{cache_dir}'.")
    
    return model, tokenizer_or_processor

def main():
    parser = argparse.ArgumentParser(description="Download and cache Hugging Face models")
    parser.add_argument("--model_id", type=str, 
                        help="The model ID on Hugging Face Hub (e.g., 'google/gemma-3-1b-it')")
    parser.add_argument("--cache_dir", type=str, default="./model_cache",
                        help="Directory to store the downloaded model")
    parser.add_argument("--domain", type=str, choices=list(MODEL_CLASSES.keys()), default=None,
                        help="Model domain (causal_lm, speech_recognition, etc.)")
    parser.add_argument("--no_token", action="store_true", 
                        help="Don't use API token even if available in .env")
    parser.add_argument("--torch_dtype", type=str, default="auto",
                        help="Torch data type to use for the model")
    
    args = parser.parse_args()
    
    # If running as a script, model_id is required
    if args.model_id is None:
        parser.error("the following arguments are required: --model_id")
    
    model, tokenizer_or_processor = download_model(
        model_id=args.model_id,
        cache_dir=args.cache_dir,
        domain=args.domain,
        use_token=not args.no_token,
        torch_dtype=args.torch_dtype
    )
    
    return model, tokenizer_or_processor

if __name__ == "__main__":
    main()