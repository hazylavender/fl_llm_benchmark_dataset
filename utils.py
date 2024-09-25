from datetime import datetime, timedelta
import calendar
import re

def get_start_and_end_dates(year, month):
    num_days = calendar.monthrange(year, month)[1]
    # dates = [datetime(year, month, day).date() for day in range(1, num_days + 1)]
    return datetime(year, month, 1), datetime(year, month, num_days)


def get_dates_in_a_month(year, month):
    num_days = calendar.monthrange(year, month)[1]
    return [datetime(year, month, day).date() for day in range(1, num_days + 1)]

def get_date_range(start_date, end_date):
    # List to store the dates
    date_range = []
    
    # Iterate from start_date to end_date
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date)
        current_date += timedelta(days=1)
    
    return date_range

def starts_with_any(text:str, substrings:list):
    for substring in substrings:
        if text.startswith(substring):
            return True
    return False

def clean_text(text):
    # Remove titles like Mr.Speaker or Madam Speaker from speech
    if starts_with_any(text, ['Mr. Speaker,', 'Madam Speaker,','Mr. President,','Madam President,']):
        return ','.join(text.split(',')[1:]).strip()
    
    # Remove some frequently reoccuring phrases
    phrases = ['I declare the motion carried. ', 'Mr. Speaker, I reserve the balance of my time. ', 'The hon. Member. ']
    for ph in phrases:
        text = text.replace(ph, '')
        
    # Remove ====Note===== Notation
    re_patterns = ['\{time\}  [0-9]+', '=*( NOTE | END NOTE )=*']
    for pattern in re_patterns:
        text = re.sub(pattern, '', text)
    
    text = remove_invalid_sentences(text)
    # text = remove_tables(text)
    return text

def remove_invalid_sentences(text):
    # Remove sentences with more than 30% of the characters are not letters 
    sentences = text.split('. ')
    result = []
    for sentence in sentences:
        total_chars = len(sentence.replace(" ", ""))
        letter_chars = sum(1 for char in sentence if char.isalpha())
        if total_chars > 0 and (letter_chars / total_chars) >= 0.70:
            result.append(sentence)
    return '. '.join(result)

def remove_tables(text):
    # Regular expression to match table-like structures
    table_pattern = r"[-]{3,}.*?(?=[A-Z]|\Z)"
    
    cleaned_text = re.sub(table_pattern, '', text, flags=re.DOTALL)
    return cleaned_text.strip()