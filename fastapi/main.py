from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import fasttext
import spacy
import torch
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast
import logging
import os
import time
import re

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Globals
default_confidence_threshold = 0.5
fasttext_model = None
nlp = None
tokenizer = None
mbart_model = None

# Language mapping
dict_lang_map = {
    "en": "en_XX",
    "fr": "fr_XX",
    "de": "de_DE",
    "ar": "ar_AR",
}
allowed_langs = set(dict_lang_map.keys())

device = "cuda" if torch.cuda.is_available() else "cpu"

# Request schema
class TranslationRequest(BaseModel):
    text: str
    target_lang: str  # two-letter code

# Utility: split text but keep delimiters
def split_keep_delims(text: str):
    parts = re.split(r'(\W+)', text)
    return [p for p in parts if p != '']

# Core mixed translation logic
def translate_mixed(text: str, full_lang: str, confidence_threshold: float = default_confidence_threshold):
    parts = split_keep_delims(text)
    out_parts = []
    last_src = None

    for part in parts:
        # pass through punctuation/spaces
        if re.fullmatch(r'\W+', part):
            out_parts.append(part)
            continue

        # detect language on the chunk
        labels, confs = fasttext_model.predict(part.replace("\n", " "))
        src = labels[0].replace("__label__", "")
        conf = confs[0]
        last_src = src

        # if it's the same as target or too low confidence, leave it unchanged
        if src == full_lang or conf < confidence_threshold:
            out_parts.append(part)
        else:
            src_code = dict_lang_map.get(src, dict_lang_map['en'])
            tgt_code = dict_lang_map.get(full_lang, dict_lang_map['en'])
            translated = translate(part, src_code, tgt_code)
            out_parts.append(translated)

    # reconstruct
    final = ''.join(out_parts).strip()
    if not final:
        # fallback: translate entire text
        # detect overall source
        labels, confs = fasttext_model.predict(text.replace("\n", " "))
        overall_src = labels[0].replace("__label__", "")
        src_code = dict_lang_map.get(overall_src, dict_lang_map['en'])
        tgt_code = dict_lang_map.get(full_lang, dict_lang_map['en'])
        final = translate(text, src_code, tgt_code)

    return final

# Translation helper
class TranslateError(Exception):
    pass

def translate(text: str, source_lang_code: str, target_lang_code: str) -> str:
    if tokenizer is None or mbart_model is None:
        raise TranslateError("Model not loaded")
    try:
        tokenizer.src_lang = source_lang_code
        inputs = tokenizer(text, return_tensors="pt").to(device)
        generated = mbart_model.generate(
            **inputs,
            forced_bos_token_id=tokenizer.lang_code_to_id[target_lang_code]
        )
        return tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return text

# Startup: load models
@app.on_event("startup")
async def startup_event():
    global fasttext_model, nlp, tokenizer, mbart_model
    start = time.time()

    # FastText
    fasttext_model = fasttext.load_model("models/fasttext/lid.176.bin")

    # spaCy
    nlp = spacy.load("xx_ent_wiki_sm")
    if "sentencizer" not in nlp.pipe_names:
        nlp.add_pipe("sentencizer")

    # MBART
    tokenizer = MBart50TokenizerFast.from_pretrained("models/mbart_tokenizer")
    mbart_model = MBartForConditionalGeneration.from_pretrained("models/mbart_model").to(device)

    logger.info(f"Models loaded in {time.time()-start:.2f}s")

# Translation endpoint
@app.post("/translate/")
def translate_text(request: TranslationRequest):
    if fasttext_model is None or nlp is None or tokenizer is None or mbart_model is None:
        raise HTTPException(status_code=500, detail="Models not loaded yet")

    text = request.text
    target = request.target_lang

    if target not in allowed_langs:
        raise HTTPException(status_code=400, detail=f"Unsupported target language: {target}")

    translated = translate_mixed(text, target)
    return {"translated_text": translated}
