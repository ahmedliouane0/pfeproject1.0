@app.post("/detect/", response_model=List[Fragment])
async def detect_fragments(request: DetectRequest):
    """Detect language fragments in text with improved handling of named entities"""
    try:
        if request.target_lang not in allowed_langs:
            raise HTTPException(400, f"Unsupported target language: {request.target_lang}")

        text = request.text.replace("\n", " ")
        target_lang = request.target_lang
        doc = nlp_models[target_lang](text)  # Use target language model for initial processing
        fragments: List[Fragment] = []

        # For very short inputs (single words), use both models for more accurate detection
        if len(text.split()) <= 1:
            # First try XLM-RoBERTa (better for word-level detection)
            xlm_label, xlm_conf = detect_token_lang_xlm(text)
            
            # Then try fastText
            ft_label, ft_conf = detect_token_lang_fasttext(text)
            
            # For single words, prefer XLM-RoBERTa as it's better at word-level detection
            if xlm_label in allowed_langs and xlm_conf > 0.6:
                label, conf = xlm_label, float(xlm_conf)
            elif ft_label in allowed_langs and ft_conf > 0.6:
                label, conf = ft_label, float(ft_conf)
            else:
                # If neither model is confident, use the more confident one
                label, conf = (xlm_label, xlm_conf) if xlm_conf > ft_conf else (ft_label, ft_conf)
            
            # Check if it's a place name
            if is_likely_place_name(text):
                fragments.append(Fragment(
                    text=text,
                    start=0,
                    end=len(text),
                    needs_translation=False,
                    detected_lang=label,
                    confidence=1.0
                ))
            else:
                needs_translation = label != target_lang
                fragments.append(Fragment(
                    text=text,
                    start=0,
                    end=len(text),
                    needs_translation=needs_translation,
                    detected_lang=label,
                    confidence=conf
                ))
            return fragments

        # Process text sentence by sentence
        for sent in doc.sents:
            sent_text = sent.text
            
            # Skip empty sentences
            if not sent_text.strip():
                continue
            
            # Detect sentence language with fastText
            sent_label, sent_conf = detect_token_lang_fasttext(sent_text)
            
            # Get named entities using the appropriate language model
            detected_lang = sent_label if sent_label in allowed_langs else target_lang
            entity_texts = get_named_entities(sent_text, detected_lang)
            
            # If we're not confident in sentence detection, try with target language model
            if sent_conf < 0.8:
                target_entities = get_named_entities(sent_text, target_lang)
                entity_texts.update(target_entities)
            
            # Process tokens individually
            for tok in sent:
                if tok.is_punct or not tok.text.strip():
                    continue
                    
                # Skip named entities and place names
                if tok.text in entity_texts or is_likely_place_name(tok.text):
                    fragments.append(Fragment(
                        text=tok.text,
                        start=tok.idx,
                        end=tok.idx + len(tok.text),
                        needs_translation=False,
                        detected_lang=detected_lang,
                        confidence=1.0
                    ))
                    continue

                # First try XLM-RoBERTa (better for word-level detection)
                xlm_label, xlm_conf = detect_token_lang_xlm(tok.text)
                
                # Then try fastText
                fasttext_label, fasttext_conf = detect_token_lang_fasttext(tok.text)
                
                # Special case for words with accents
                has_french_accents = bool(re.search(r'[éèêëàâäôöùûüÿçñ]', tok.text))
                has_german_accents = bool(re.search(r'[äöüß]', tok.text))
                
                # Determine the final language and confidence
                if has_french_accents and target_lang != "fr":
                    label, conf = "fr", 0.95
                elif has_german_accents and target_lang != "de":
                    label, conf = "de", 0.95
                else:
                    # For word-level detection, prefer XLM-RoBERTa if confident
                    if xlm_label in allowed_langs and xlm_conf > 0.6:
                        label, conf = xlm_label, xlm_conf
                    elif fasttext_label in allowed_langs and fasttext_conf > 0.6:
                        label, conf = fasttext_label, fasttext_conf
                    else:
                        # If neither model is confident, use the more confident one
                        label, conf = (xlm_label, xlm_conf) if xlm_conf > fasttext_conf else (fasttext_label, fasttext_conf)
                
                # For very short words with low confidence, assume target language
                if len(tok.text) <= 3 and conf < 0.8:
                    label = target_lang
                    conf = 0.7
                
                # Determine if translation is needed
                needs_translation = label != target_lang
                
                fragments.append(Fragment(
                    text=tok.text,
                    start=tok.idx,
                    end=tok.idx + len(tok.text),
                    needs_translation=needs_translation,
                    detected_lang=label,
                    confidence=float(conf)
                ))

        return fragments
    except Exception as e:
        logger.error(f"Detection error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Return a minimal fragment to avoid breaking the client
        return [Fragment(
            text=request.text,
            start=0,
            end=len(request.text),
            needs_translation=True,
            detected_lang="unknown",
            confidence=0.5
        )] 