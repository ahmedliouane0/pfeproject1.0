# ... existing code ...
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

            # First detection with fastText
            fasttext_label, fasttext_conf = detect_token_lang_fasttext(tok.text)
            
            # Special case for words with accents in non-English text
            has_accents = bool(re.search(r'[éèêëàâäôöùûüÿçñ]', tok.text))
            
            # If fastText is confident and the language is supported
            if fasttext_conf >= 0.7 and fasttext_label in allowed_langs:
                # French words containing accents should usually stay French
                if has_accents and fasttext_label == "fr" and target_lang != "fr":
                    needs_translation = True
                    detected_lang = "fr"
                # German words with umlauts should usually stay German
                elif has_accents and fasttext_label == "de" and target_lang != "de":
                    needs_translation = True
                    detected_lang = "de"
                else:
                    # For non-accented words, trust the fastText detection more
                    needs_translation = fasttext_label != target_lang
                    detected_lang = fasttext_label
                    
                fragments.append(Fragment(
                    text=tok.text,
                    start=tok.idx,
                    end=tok.idx + len(tok.text),
                    needs_translation=needs_translation,
                    detected_lang=detected_lang,
                    confidence=float(fasttext_conf)
                ))
            else:
                # Fallback to XLM-R for low confidence cases
                xlm_label, xlm_conf = detect_token_lang_xlm(tok.text)
                
                # If XLM-R is confident and language is supported
                if xlm_conf > 0.7 and xlm_label in allowed_langs:
                    needs_translation = xlm_label != target_lang
                    fragments.append(Fragment(
                        text=tok.text,
                        start=tok.idx,
                        end=tok.idx + len(tok.text),
                        needs_translation=needs_translation,
                        detected_lang=xlm_label,
                        confidence=float(xlm_conf)
                    ))
                else:
                    # If both models aren't confident, use the best guess
                    # but prefer fastText unless XLM-R is much more confident
                    if xlm_conf > fasttext_conf + 0.2 and xlm_label in allowed_langs:
                        label, conf = xlm_label, xlm_conf
                    else:
                        label = fasttext_label if fasttext_label in allowed_langs else target_lang
                        conf = fasttext_conf
                    
                    # For very short words with low confidence, assume target language
                    if len(tok.text) <= 3 and conf < 0.8:
                        label = target_lang
                        conf = 0.7
                        
                    needs_translation = label != target_lang
                    fragments.append(Fragment(
                        text=tok.text,
                        start=tok.idx,
                        end=tok.idx + len(tok.text),
                        needs_translation=needs_translation,
                        detected_lang=label,
                        confidence=float(conf)
                    ))
# ... existing code ... 