from textblob import TextBlob
from collections import Counter

# --- NEW: Local Summary Generation Function ---
def generate_option_summary(option_name, reasons_list):
    """
    Generates a simple, non-AI summary for a specific poll option based on local analysis.
    """
    if not reasons_list:
        return f"Voters selected '{option_name}' but did not provide specific reasons."

    # Analyze sentiment of all reasons for this option
    sentiments = [analyze_sentiment(r) for r in reasons_list]
    sentiment_counts = Counter(sentiments)
    dominant_sentiment = sentiment_counts.most_common(1)[0][0]

    # Extract keywords from all reasons for this option
    all_reasons_text = ". ".join(reasons_list)
    keywords = extract_keywords(all_reasons_text, num_keywords=3)

    summary = f"The overall sentiment for '{option_name}' is predominantly **{dominant_sentiment.lower()}**. "
    if keywords:
        keyword_str = ", ".join(f"'{kw}'" for kw in keywords)
        summary += f"Common topics mentioned in the reasons include: **{keyword_str}**."
    
    return summary

def analyze_sentiment(reason_text):
    """Analyzes the sentiment of a given text."""
    if not reason_text: return "Neutral"
    analysis = TextBlob(reason_text)
    if analysis.sentiment.polarity > 0.1: return "Positive"
    elif analysis.sentiment.polarity < -0.1: return "Negative"
    else: return "Neutral"

def extract_keywords(reason_text, num_keywords=5):
    """Extracts common nouns as keywords."""
    if not reason_text: return []
    blob = TextBlob(reason_text.lower())
    common_words = [word for word, pos in blob.tags if pos.startswith('NN')]
    seen = set()
    unique_words = [x for x in common_words if not (x in seen or seen.add(x))]
    return unique_words[:num_keywords]
