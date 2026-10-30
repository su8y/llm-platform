import os
import fasttext

from module.Language.helper import *
from utils.constants import KOREAN, REAL



class FastTextDetector:
    model = None
    model_path = 'module/Language/lang_detect_model.bin' if os.getenv("SERVER_STAGE") != REAL else '/home/ec2-user/llm-platform/api/lang_detect_model.bin'

    @classmethod
    def model_init(cls):
        try:
            cls.model = fasttext.load_model(cls.model_path)
            logging.info("✅ Success To LOAD detect language model")
        except Exception as e:
            logging.error(f"[module.Language.detector.FastTextDetector.model_init] 🔴 Exception: {e}")


    @classmethod
    def _load_model(cls):
        try:
            if cls.model is None:
                cls.model = fasttext.load_model(cls.model_path)
                logging.info("[module.Language.detector.FastTextDetector.model_init] ✅ Success To LOAD detect language model")
            else:
                logging.info("[module.Language.detector.FastTextDetector.model_init] ✅ language model was SET")
        except Exception as e:
            logging.error(f"[module.Language.detector.FastTextDetector._load_model] 🔴 Exception: {e}")
            raise "Fail to LOAD Model. you should check"


    @classmethod
    async def detect(cls, args:LLMArgs|LLMEmailArgs|MCPArgs):
        try:
            cls._load_model()
            predictions = cls.model.predict(args.question.replace('\n', ' '))
            get_elapsed(args, "ElapsedLangAgent")
            args.lang_detected = predictions[0][0].replace('__label__', '')
        except Exception as e:
            logging.error(f"[module.Language.detector.FastTextDetector.detect] 🔴 Exception: {e}")
            args.lang_detected = KOREAN