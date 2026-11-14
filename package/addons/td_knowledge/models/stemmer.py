"""Light stemmer for Ukrainian (and the common Russian endings) for the search of the knowledge base.

PostgreSQL 16 has no Ukrainian text search configuration (pg_ts_config: russian, english, … — no ukrainian), so the
stems are computed here: a word loses its ending, the rest is the stem. A search word matches when its stem is the
beginning of a stem of the article ('монтажу' → 'монтаж' matches 'монтаж', 'монтажем', 'монтажник').
Written for this module; no dictionary, no external package.
"""
import re

MIN_STEM = 3
_WORD_RE = re.compile(r"[\w'’ʼ`-]+", re.UNICODE)
_REFLEXIVE = ('ися', 'ись', 'ся', 'сь')
_ENDINGS = sorted({
    # nouns
    'ями', 'ами', 'ові', 'еві', 'єві', 'ією', 'іям', 'іях', 'іями',
    'ах', 'ях', 'ам', 'ям', 'ою', 'ею', 'єю', 'ом', 'ем', 'єм', 'ів', 'їв', 'ей', 'ія', 'ії', 'ію',
    # adjectives, participles
    'ого', 'ому', 'ими', 'іми', 'ий', 'ій', 'их', 'іх', 'им', 'ім', 'ої', 'ая', 'яя', 'ее', 'ую', 'юю',
    # verbs, present tense (the infinitive -ати/-ити is not cut: it collides with nouns, оплати → опл)
    'ують', 'ють', 'уть', 'ує', 'ює',
    # Russian
    'ы', 'ов', 'ые', 'ой',
    # single letters
    'а', 'я', 'о', 'е', 'є', 'у', 'ю', 'і', 'и', 'ї', 'ь', 'й',
}, key=len, reverse=True)
_DOUBLE_END = re.compile(r'([бвгґджзклмнпрстфхцчшщ])\1$')


def normalize(word):
    word = word.lower().replace('’', "'").replace('ʼ', "'").replace('`', "'").replace('ё', 'е').replace('ґ', 'г')
    return word.strip("'-")


def stem(word):
    word = normalize(word)
    if len(word) <= MIN_STEM or not word.isalpha() and "'" not in word:
        return word
    for suffix in _REFLEXIVE:
        if word.endswith(suffix) and len(word) - len(suffix) >= MIN_STEM:
            word = word[:-len(suffix)]
            break
    for suffix in _ENDINGS:
        if word.endswith(suffix) and len(word) - len(suffix) >= MIN_STEM:
            word = word[:-len(suffix)]
            break
    if word.endswith(('ь', 'й')) and len(word) > MIN_STEM:
        word = word[:-1]
    # замовлення / замовлень: the doubled consonant before the ending is one stem
    return _DOUBLE_END.sub(r'\1', word)


def words(text):
    return [w for w in (normalize(m) for m in _WORD_RE.findall(text or '')) if w]


def stems(text):
    return {stem(w) for w in words(text) if len(w) > 1}
