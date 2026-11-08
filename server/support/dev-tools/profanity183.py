"""Turkish profanity and nonsense-name checks for backend v183 (pure functions, no state).
fold(): lowercase with Turkish letters folded to ASCII, common digit/symbol swaps (0->o, 1->i, 3->e, 4->a, 5->s, 7->t,
@->a, $->s), accents stripped and repeated letters collapsed ("siiik" -> "sik", "taşşak" -> "tasak").
bad(text): True when a swear/insult word appears as a word (also spelled with dots/spaces between single letters,
"a.m.k"); substrings inside ordinary words ("ışık", "kesik", "amca", "sıkıldım") do not count.
nonsense_name(part): keyboard mash such as "dwadwa", "asdasd", "qwrtz": no vowel, 4+ consonants in a row, too few
vowels, a 2-4 letter chunk repeated, or a keyboard run."""
import re,unicodedata
TR=str.maketrans({'ı':'i','İ':'i','ş':'s','Ş':'s','ğ':'g','Ğ':'g','ü':'u','Ü':'u','ö':'o','Ö':'o','ç':'c','Ç':'c','â':'a','î':'i','û':'u',
 '0':'o','1':'i','3':'e','4':'a','5':'s','7':'t','@':'a','$':'s','!':'i'})
def fold(text):
 t=str(text).translate(TR).lower();t=unicodedata.normalize('NFKD',t);t=''.join(ch for ch in t if not unicodedata.combining(ch))
 return re.sub(r'([a-z])\1+',r'\1',t)
WORDS=(r'sik|sike?yim|sikerim|sikim|siktir\w*|sikis\w*|sikik\w*|sikti\w*|siker\w*|sikiyim|sikecem|sikic\w*|'
 r'amk|amq|aq|am|amina\w*|aminak\w*|amcik\w*|amciy\w*|'
 r'orospu\w*|orsp\w*|oc|ocu|pic|pici\w*|pic\w*kurusu|gotveren|gotlek|got|gotun|gotu|gote|tasak\w*|tasag\w*|yarak\w*|yaram\w*|'
 r'pezevenk\w*|pezo|kahpe\w*|ibne\w*|kaltak\w*|kancik\w*|serefsiz\w*|anani|ananin|anan\w*sik\w*|bacini|avradini|sg|siktirgit|mk|mq')
BAD=re.compile(r'\b(?:'+WORDS+r')\b')
def bad(text):
 t=fold(text)
 if BAD.search(t):return True
 joined=re.sub(r'(?<=\b[a-z])[\s.\-_*,+]+(?=[a-z]\b)','',t)
 return joined!=t and bool(BAD.search(joined))
KEYS=('qwe','wer','ert','asd','sdf','dfg','fgh','ghj','hjk','jkl','zxc','xcv','cvb','vbn','bnm','qaz','wsx')
def nonsense_name(part):
 t=re.sub(r'[^a-z]','',fold(part))
 if len(t)<2:return True
 v=sum(ch in'aeiou'for ch in t)
 if v==0 or v/len(t)<.2:return True
 if re.search(r'[^aeiouy]{4,}',t):return True
 if len(t)>=6 and re.search(r'([a-z]{2,4})\1',t):return True
 if len(t)>=5 and sum(k in t for k in KEYS)>=2:return True
 return False
