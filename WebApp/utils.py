import nltk
from nltk.metrics import edit_distance
from fuzzywuzzy import fuzz
import ssl
import re
from datetime import datetime
import random
import string


try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context


nltk.download('punkt')


def preprocess_text(text):
    cleaned_text = text.replace(',', '')
    cleaned_text = re.sub(r'\.([a-z])', r'. \1', cleaned_text)
    cleaned_text = re.sub(r"(\w+)['’](\w+)\b", r"\1\2", cleaned_text)
    cleaned_text = re.sub(r'[^\w\s]', ' ', cleaned_text.lower())
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    return cleaned_text.strip()


def calculate_reading_speed(transcript, start_time, end_time):
    duration_seconds = (end_time - start_time).total_seconds()
    words = transcript.split()
    word_count = len(words)
   
    if duration_seconds > 0:
        words_per_second = word_count / duration_seconds
        words_per_minute = words_per_second * 60
        return round(words_per_minute, 2)
    else:
        return 0


def analyze_reading_mistakes(reference_text, transcript, ignored_words=[]):
    processed_reference = preprocess_text(reference_text)
    processed_transcript = preprocess_text(transcript)


    reference_words = nltk.word_tokenize(processed_reference)
    student_words = nltk.word_tokenize(processed_transcript)


    mispronunciation = 0
    omission = 0
    substitution = 0
    insertion = 0


    mispronunciation_threshold = 70


    mispronunciation_words = []
    omission_words = []
    substitution_words = []
    insertion_words = []


    ref_index = 0
    stu_index = 0


    while ref_index < len(reference_words) or stu_index < len(student_words):
        if ref_index < len(reference_words):
            ref_word = reference_words[ref_index]
        else:
            ref_word = None
       
        if stu_index < len(student_words):
            stu_word = student_words[stu_index]
        else:
            stu_word = None
       
        if ref_word == stu_word:
            ref_index += 1
            stu_index += 1
            continue


        if ref_word is None:
            insertion += 1
            insertion_words.append(stu_word)
            stu_index += 1
            continue


        if stu_word is None:
            omission += 1
            omission_words.append(ref_word)
            ref_index += 1
            continue


        if stu_index + 1 < len(student_words) and student_words[stu_index + 1] == ref_word:
            insertion += 1
            insertion_words.append(stu_word)
            stu_index += 1
            continue


        if ref_index + 1 < len(reference_words) and reference_words[ref_index + 1] == stu_word:
            omission += 1
            omission_words.append(ref_word)
            ref_index += 1
            continue


        if stu_word in ignored_words:
            stu_index += 1
            continue
       
        distance = edit_distance(ref_word, stu_word)


        if distance == 0:
            ref_index += 1
            stu_index += 1
            continue


        ratio = fuzz.ratio(ref_word, stu_word)


        if distance == 1 or distance == 2:
            if ratio >= mispronunciation_threshold:
                mispronunciation += 1
                mispronunciation_words.append((ref_word, stu_word))
            else:
                substitution += 1
                substitution_words.append((ref_word, stu_word))
            ref_index += 1
            stu_index += 1
            continue


        if ratio >= mispronunciation_threshold:
            mispronunciation += 1
            mispronunciation_words.append((ref_word, stu_word))
        else:
            substitution += 1
            substitution_words.append((ref_word, stu_word))
       
        ref_index += 1
        stu_index += 1


    total_miscues = mispronunciation + omission + substitution + insertion


    if len(reference_words) > 0:
        oral_reading_score = (len(reference_words) - total_miscues) / len(reference_words) * 100
    else:
        oral_reading_score = 0


    if oral_reading_score <= 89:
        reading_level = "Frustration"
    elif 90 <= oral_reading_score <= 96:
        reading_level = "Instructional"
    else:
        reading_level = "Independent"


    result = {
        "Mispronunciation": mispronunciation,
        "Omission": omission,
        "Substitution": substitution,
        "Insertion": insertion,
        "Total Miscues": total_miscues,
        "Oral Reading Score": oral_reading_score,
        "Reading Level": reading_level
    }


    if mispronunciation_words:
        result["Mispronunciation Words"] = mispronunciation_words
    if omission_words:
        result["Omission Words"] = omission_words
    if substitution_words:
        result["Substitution Words"] = substitution_words
    if insertion_words:
        result["Insertion Words"] = insertion_words


    return result


def wer(reference_text, transcript):
    ref_words = nltk.word_tokenize(preprocess_text(reference_text))
    hyp_words = nltk.word_tokenize(preprocess_text(transcript))


    # Calculate Word Error Rate
    return float(edit_distance(ref_words, hyp_words)) / len(ref_words)


def handle_ignore_click(reference_text, transcript, ignore_word):
    ignored_words = nltk.word_tokenize(preprocess_text(ignore_word))
    return analyze_reading_mistakes(reference_text, transcript, ignored_words)




def generate_otp(length=6):
    """Generate a random OTP of given length."""
    digits = string.digits
    otp = ''.join(random.choice(digits) for i in range(length))
    return otp
