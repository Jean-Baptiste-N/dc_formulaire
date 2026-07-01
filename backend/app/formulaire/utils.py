import re

def clean_text(text):
    """
    Nettoie le texte en supprimant les caractères indésirables.
    Utile pour nettoyer les données collées depuis Word ou d'autres sources.
    """
    if not isinstance(text, str):
        return text

    # Supprimer caractères non-alphanumériques au début et fin
    text = re.sub(r'^\W+', '', text)
    text = re.sub(r'\W+$', '', text)

    return text.strip()
