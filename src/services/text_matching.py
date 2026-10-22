import re
import difflib

def normalize_arabic(text: str) -> str:
    text = re.sub(r'[\u0617-\u061A\u064B-\u0652]', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ة\b', 'ه', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def compare_texts(reference: str, recited: str) -> dict:
    ref_norm = normalize_arabic(reference)
    rec_norm = normalize_arabic(recited)

    ref_words = ref_norm.split()
    rec_words = rec_norm.split()

    matcher = difflib.SequenceMatcher(None, ref_words, rec_words)
    similarity_ratio = round(matcher.ratio() * 100, 2)

    missing_words = []
    replaced_words = []
    extra_words = []
    word_by_word_analysis = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for w in ref_words[i1:i2]:
                word_by_word_analysis.append({"word": w, "status": "correct"})
        elif tag == 'delete':
            for w in ref_words[i1:i2]:
                missing_words.append(w)
                word_by_word_analysis.append({"word": w, "status": "missing"})
        elif tag == 'insert':
            for w in rec_words[j1:j2]:
                extra_words.append(w)
                word_by_word_analysis.append({"word": w, "status": "extra"})
        elif tag == 'replace':
            expected_chunk = " ".join(ref_words[i1:i2])
            spoken_chunk = " ".join(rec_words[j1:j2])
            replaced_words.append({
                "expected": expected_chunk,
                "spoken": spoken_chunk
            })
            word_by_word_analysis.append({
                "expected": expected_chunk,
                "spoken": spoken_chunk,
                "status": "replaced"
            })

    return {
        "similarity_percentage": similarity_ratio,
        "is_passed": similarity_ratio >= 85.0,
        "missing_words": missing_words,
        "replaced_words": replaced_words,
        "extra_words": extra_words,
        "detailed_analysis": word_by_word_analysis
    }