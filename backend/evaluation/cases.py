"""
Multilingual evaluation cases for the Namma HR policy assistant.

Facts come from backend/docs/HR_POLICY.pdf. The interface exposes
nine languages. Odia and Urdu are not in that list because Gnani
Prisma and Timbre do not support them.
"""

from __future__ import annotations

SOURCE = "HR_POLICY.pdf"

LANGUAGES = ("en", "hi", "ta", "te", "kn", "ml", "bn", "mr", "gu")

# Each topic is one HR question asked in every interface language.
# passage_terms must appear in the retrieved English PDF text.
# answer_any groups: a correct answer matches at least one term in every group.
TOPICS: list[dict] = [
    {
        "id": "casual_entitlement",
        "title": "Casual leave entitlement",
        "in_policy": True,
        "pages": [1, 2],
        "passage_terms": ["casual leave"],
        "facts": (
            "Casual leave is 7 days in a calendar year. "
            "It can be taken from 0.5 day to 3 days. "
            "Unused casual leave lapses and is not encashable."
        ),
        "answer_any": [["7"]],
        "questions": {
            "en": "How many casual leave days is an employee entitled to in a year?",
            "hi": "एक साल में कर्मचारी को कितने दिन की कैजुअल लीव मिलती है?",
            "ta": "ஒரு வருடத்திற்கு எத்தனை நாள் கேஷுவல் லீவ் கிடைக்கும்?",
            "te": "ఒక సంవత్సరానికి ఎన్ని రోజుల క్యాజువల్ లీవ్ హక్కు ఉంటుంది?",
            "kn": "ಒಂದು ವರ್ಷಕ್ಕೆ ಎಷ್ಟು ದಿನ ಕ್ಯಾಶುವಲ್ ಲೀವ್ ಸಿಗುತ್ತದೆ?",
            "ml": "ഒരു വർഷത്തിൽ എത്ര ദിവസം കാഷ്വൽ ലീവ് ലഭിക്കും?",
            "bn": "এক বছরে কতদিন ক্যাজুয়াল ছুটি পাওয়া যায়?",
            "mr": "एका वर्षात किती दिवस कॅज्युअल रजा मिळते?",
            "gu": "એક વર્ષમાં કેટલા દિવસની કેઝ્યુઅલ રજા મળે છે?",
        },
    },
    {
        "id": "casual_monthly_limit",
        "title": "Casual leave monthly limit",
        "in_policy": True,
        "pages": [1, 2],
        "passage_terms": ["casual leave", "3"],
        "facts": (
            "Casual leave is limited to a maximum of 3 days in a month. "
            "More than 3 days must be taken as earned or privileged leave."
        ),
        "answer_any": [["3"]],
        "questions": {
            "en": "What is the maximum casual leave that can be taken in one month?",
            "hi": "एक महीने में अधिकतम कितने दिन कैजुअल लीव ली जा सकती है?",
            "ta": "ஒரு மாதத்தில் கேஷுவல் லீவ் அதிகபட்சம் எத்தனை நாள் எடுக்கலாம்?",
            "te": "ఒక నెలలో గరిష్టంగా ఎన్ని రోజుల క్యాజువల్ లీవ్ తీసుకోవచ్చు?",
            "kn": "ಒಂದು ತಿಂಗಳಿಗೆ ಗರಿಷ್ಠ ಎಷ್ಟು ದಿನ ಕ್ಯಾಶುವಲ್ ಲೀವ್ ತೆಗೆದುಕೊಳ್ಳಬಹುದು?",
            "ml": "ഒരു മാസത്തിൽ പരമാവധി എത്ര ദിവസം കാഷ്വൽ ലീവ് എടുക്കാം?",
            "bn": "এক মাসে সর্বোচ্চ কতদিন ক্যাজুয়াল ছুটি নেওয়া যায়?",
            "mr": "एका महिन्यात जास्तीत जास्त किती दिवस कॅज्युअल रजा घेता येते?",
            "gu": "એક મહિનામાં વધુમાં વધુ કેટલા દિવસની કેઝ્યુઅલ રજા લઈ શકાય?",
        },
    },
    {
        "id": "sick_entitlement",
        "title": "Sick leave entitlement",
        "in_policy": True,
        "pages": [2],
        "passage_terms": ["sick leave"],
        "facts": (
            "Sick leave is 7 paid days, from a minimum of 0.5 day "
            "to a maximum of 7 days. It does not carry forward and is not encashable."
        ),
        "answer_any": [["7"]],
        "questions": {
            "en": "How many days of sick leave can an employee take?",
            "hi": "कर्मचारी कितने दिन की बीमार छुट्टी ले सकता है?",
            "ta": "நோய் விடுப்பு எத்தனை நாள் எடுக்கலாம்?",
            "te": "అనారోగ్య సెలవు ఎన్ని రోజులు తీసుకోవచ్చు?",
            "kn": "ಅನಾರೋಗ್ಯ ರಜೆ ಎಷ್ಟು ದಿನ ತೆಗೆದುಕೊಳ್ಳಬಹುದು?",
            "ml": "അസുഖാവധി എത്ര ദിവസം എടുക്കാം?",
            "bn": "অসুস্থতার ছুটি কতদিন নেওয়া যায়?",
            "mr": "रुग्ण रजा किती दिवस घेता येते?",
            "gu": "બીમારીની રજા કેટલા દિવસ લઈ શકાય?",
        },
    },
    {
        "id": "earned_carry_forward",
        "title": "Earned leave carry-forward",
        "in_policy": True,
        "pages": [3],
        "passage_terms": ["earned leave", "45"],
        "facts": (
            "Unused earned leave may be carried into the next calendar year, "
            "subject to a maximum of 45 days."
        ),
        "answer_any": [["45"]],
        "questions": {
            "en": "Can unused earned leave be carried forward, and what is the maximum?",
            "hi": "क्या बची हुई अर्जित छुट्टी आगे ले जाई जा सकती है, और अधिकतम कितने दिन?",
            "ta": "பயன்படுத்தாத ஈர்ன்ட் லீவை கேரி ஃபார்வேர்ட் செய்ய முடியுமா, அதிகபட்சம் எத்தனை நாள்?",
            "te": "ఉపయోగించని సంపాదిత సెలవును క్యారీ ఫార్వర్డ్ చేయవచ్చా, గరిష్టం ఎన్ని రోజులు?",
            "kn": "ಬಳಸದ ಗಳಿಸಿದ ರಜೆಯನ್ನು ಕ್ಯಾರಿ ಫಾರ್ವರ್ಡ್ ಮಾಡಬಹುದೇ, ಗರಿಷ್ಠ ಎಷ್ಟು ದಿನ?",
            "ml": "ഉപയോഗിക്കാത്ത സമ്പാദ്യ അവധി ക്യാരി ഫോർവേഡ് ചെയ്യാമോ, പരമാവധി എത്ര ദിവസം?",
            "bn": "অব্যবহৃত অর্জিত ছুটি কি আগে নিয়ে যাওয়া যায়, সর্বোচ্চ কতদিন?",
            "mr": "न वापरलेली अर्जित रजा पुढे नेता येते का, आणि कमाल किती दिवस?",
            "gu": "ન વાપરેલી કમાયેલ રજા આગળ લઈ જઈ શકાય, વધુમાં વધુ કેટલા દિવસ?",
        },
    },
    {
        "id": "maternity_leave",
        "title": "Maternity leave",
        "in_policy": True,
        "pages": [3],
        "passage_terms": ["maternity"],
        "facts": (
            "Paid maternity leave is up to 26 weeks (180 days). "
            "A woman who already has two or more children is entitled to 12 weeks. "
            "She must have worked at least 80 days in the 12 months before the expected delivery."
        ),
        "answer_any": [["26", "180"]],
        "questions": {
            "en": "How many weeks of maternity leave are provided?",
            "hi": "प्रसूति अवकाश कितने हफ्ते का मिलता है?",
            "ta": "மகப்பேறு விடுப்பு எத்தனை வாரங்கள் வழங்கப்படுகிறது?",
            "te": "మాతృత్వ సెలవు ఎన్ని వారాలు ఇస్తారు?",
            "kn": "ಪ್ರಸೂತಿ ರಜೆ ಎಷ್ಟು ವಾರ ನೀಡಲಾಗುತ್ತದೆ?",
            "ml": "മെറ്റേണിറ്റി ലീവ് എത്ര ആഴ്ച ലഭിക്കും?",
            "bn": "প্রসূতি ছুটি কত সপ্তাহ পাওয়া যায়?",
            "mr": "प्रसूति रजा किती आठवडे मिळते?",
            "gu": "પ્રસૂતિ રજા કેટલા અઠવાડિયાની મળે છે?",
        },
    },
    {
        "id": "paternity_leave",
        "title": "Paternity leave",
        "in_policy": True,
        "pages": [4],
        "passage_terms": ["paternity"],
        "facts": (
            "Paternity leave is unpaid. It is given to a male employee when a child is born. "
            "The duration is at the sole discretion of management."
        ),
        "answer_any": [[
            "unpaid",
            "without pay",
            "बिना वेतन",
            "சம்பளமில்லாத",
            "జీతం లేకుండా",
            "ಸಂಬಳವಿಲ್ಲದ",
            "ശമ്പളമില്ലാത്ത",
            "বেতনহীন",
            "बिनपगारी",
            "પગાર વગર",
        ]],
        "questions": {
            "en": "Is paternity leave paid or unpaid?",
            "hi": "क्या पितृत्व अवकाश वेतन सहित है या बिना वेतन?",
            "ta": "பேட்டர்னிட்டி லீவ் சம்பளத்துடன் கூடியதா, இல்லையா?",
            "te": "పితృత్వ సెలవు జీతంతో ఇస్తారా, లేక జీతం లేకుండా?",
            "kn": "ಪಿತೃತ್ವ ರಜೆ ಸಂಬಳದೊಂದಿಗೆಯೇ, ಅಥವಾ ಸಂಬಳವಿಲ್ಲದೆಯೇ?",
            "ml": "പാറ്റേണിറ്റി ലീവ് ശമ്പളത്തോടുകൂടിയാണോ, അല്ലെങ്കിൽ ശമ്പളമില്ലാത്തതാണോ?",
            "bn": "পিতৃত্ব ছুটি কি বেতনসহ, না বেতনহীন?",
            "mr": "पितृत्व रजा पगारी आहे की बिनपगारी?",
            "gu": "પિતૃત્વ રજા પગાર સાથે છે કે પગાર વગર?",
        },
    },
    {
        "id": "work_from_home",
        "title": "Work-from-home policy",
        "in_policy": True,
        "pages": [4],
        "passage_terms": ["work from home"],
        "facts": (
            "Eligible employees may be allowed to work from home case by case, "
            "depending on the nature of the work. Conditions are mutually agreed."
        ),
        "answer_any": [["case", "mutually", "eligible", "घर से काम", "வீட்டிலிருந்து", "ఇంటి నుండి", "ಮನೆಯಿಂದ", "വീട്ടിൽ നിന്ന്", "বাড়ি থেকে", "घरातून", "ઘરેથી"]],
        "questions": {
            "en": "What is the work from home policy?",
            "hi": "घर से काम करने की नीति क्या है?",
            "ta": "வீட்டிலிருந்து வேலை செய்வதற்கான கொள்கை என்ன?",
            "te": "ఇంటి నుండి పని చేయడం గురించిన విధానం ఏమిటి?",
            "kn": "ಮನೆಯಿಂದ ಕೆಲಸ ಮಾಡುವ ನೀತಿ ಏನು?",
            "ml": "വീട്ടിൽ നിന്ന് ജോലി ചെയ്യുന്നതിനുള്ള നയം എന്താണ്?",
            "bn": "বাড়ি থেকে কাজ করার নীতি কী?",
            "mr": "घरातून काम करण्याचे धोरण काय आहे?",
            "gu": "ઘરેથી કામ કરવાની નીતિ શું છે?",
        },
    },
    {
        "id": "medical_certificate",
        "title": "Medical certificate requirements",
        "in_policy": True,
        "pages": [2],
        "passage_terms": ["medical certificate"],
        "facts": (
            "For sick leave absences exceeding 2 or 3 days, "
            "a medical certificate usually needs to be enclosed."
        ),
        "answer_any": [["2", "3"], ["certificate", "சான்றிதழ்", "प्रमाणपत्र", "సర్టిఫికేట్", "ಪ್ರಮಾಣಪತ್ರ", "സർട്ടിഫിക്കറ്റ്", "সার্টিফিকেট", "प्रमाणपत्र", "પ્રમાણપત્ર"]],
        "questions": {
            "en": "When is a medical certificate required for sick leave?",
            "hi": "बीमार छुट्टी के लिए चिकित्सा प्रमाणपत्र कब लगाना होता है?",
            "ta": "நோய் விடுப்புக்கு மருத்துவ சான்றிதழ் எப்போது தேவை?",
            "te": "అనారోగ్య సెలవుకు వైద్య సర్టిఫికేట్ ఎప్పుడు అవసరం?",
            "kn": "ಅನಾರೋಗ್ಯ ರಜೆಗೆ ವೈದ್ಯಕೀಯ ಪ್ರಮಾಣಪತ್ರ ಯಾವಾಗ ಬೇಕು?",
            "ml": "അസുഖാവധിക്ക് മെഡിക്കൽ സർട്ടിഫിക്കറ്റ് എപ്പോൾ വേണം?",
            "bn": "অসুস্থতার ছুটিতে মেডিকেল সার্টিফিকেট কখন লাগে?",
            "mr": "रुग्ण रजेसाठी वैद्यकीय प्रमाणपत्र कधी लागते?",
            "gu": "બીમારીની રજા માટે તબીબી પ્રમાણપત્ર ક્યારે જોઈએ?",
        },
    },
    {
        "id": "leave_approval",
        "title": "Leave approval",
        "in_policy": True,
        "pages": [1],
        "passage_terms": ["approval"],
        "facts": (
            "The employee must apply for leave and take approval, except when "
            "advance approval could not be taken, usually for casual or sick leave. "
            "Approval is at the manager's discretion and can be refused."
        ),
        "answer_any": [["approval", "manager", "मंजूरी", "அனுமதி", "ఆమోదం", "ಅನುಮೋದನೆ", "അനുമതി", "অনুমোদন", "मंजूरी", "મંજૂરી"]],
        "questions": {
            "en": "Does leave need approval before an employee takes it?",
            "hi": "छुट्टी लेने से पहले मंजूरी लेनी पड़ती है क्या?",
            "ta": "விடுப்பு எடுப்பதற்கு முன் அனுமதி பெற வேண்டுமா?",
            "te": "సెలవు తీసుకునే ముందు ఆమోదం తీసుకోవాలా?",
            "kn": "ರಜೆ ತೆಗೆದುಕೊಳ್ಳುವ ಮೊದಲು ಅನುಮೋದನೆ ಪಡೆಯಬೇಕೇ?",
            "ml": "അവധി എടുക്കുന്നതിന് മുൻപ് അനുമതി വേണോ?",
            "bn": "ছুটি নেওয়ার আগে অনুমোদন নিতে হয় কি?",
            "mr": "रजा घेण्यापूर्वी मंजूरी घ्यावी लागते का?",
            "gu": "રજા લેતા પહેલાં મંજૂરી લેવી પડે છે?",
        },
    },
    {
        "id": "not_in_policy",
        "title": "Information not in the policy",
        "in_policy": False,
        "pages": [],
        "passage_terms": [],
        "absent_term": "adoption",
        "facts": (
            "Adoption leave is not stated in HR_POLICY.pdf. "
            "The assistant must say the information was not found and must not invent a day count."
        ),
        "answer_any": [[
            "not found",
            "not available",
            "not mentioned",
            "does not",
            "नहीं मिल",
            "கிடைக்கவில்லை",
            "లభించలేదు",
            "ಸಿಗಲಿಲ್ಲ",
            "ലഭ്യമല്ല",
            "পাওয়া যায়নি",
            "सापडत नाही",
            "મળતી નથી",
        ]],
        "questions": {
            "en": "How many days of adoption leave does the policy provide?",
            "hi": "नीति में गोद लेने की छुट्टी कितने दिन की है?",
            "ta": "கொள்கையில் தத்தெடுப்பு விடுப்பு எத்தனை நாள்?",
            "te": "పాలసీలో దత్తత సెలవు ఎన్ని రోజులు?",
            "kn": "ನೀತಿಯಲ್ಲಿ ದತ್ತು ರಜೆ ಎಷ್ಟು ದಿನ?",
            "ml": "നയത്തിൽ ദത്തെടുക്കൽ അവധി എത്ര ദിവസമാണ്?",
            "bn": "নীতিতে দত্তক ছুটি কতদিন?",
            "mr": "धोरणात दत्तक रजा किती दिवसांची आहे?",
            "gu": "નીતિમાં દત્તક રજા કેટલા દિવસની છે?",
        },
    },
]


def evaluation_cases() -> list[dict]:
    """One row for every language and HR topic."""

    rows: list[dict] = []

    for topic in TOPICS:
        for language in LANGUAGES:
            question = topic["questions"][language]
            rows.append(
                {
                    "language": language,
                    "topic": topic["id"],
                    "title": topic["title"],
                    "question": question,
                    "expected_facts": topic["facts"],
                    "in_policy": topic["in_policy"],
                    "expected_source": SOURCE if topic["in_policy"] else None,
                    "expected_pages": list(topic["pages"]),
                    "passage_terms": list(topic["passage_terms"]),
                    "answer_any": topic["answer_any"],
                    "absent_term": topic.get("absent_term"),
                }
            )

    return rows


# Spoken checks use the same nine languages. They verify the Gnani
# language code, output format, and Timbre voice. They do not call
# the speech APIs unless a live run is requested separately.
VOICE_CASES = [
    {
        "language": language,
        "spoken_question": TOPICS[0]["questions"][language],
        "stt_supported": True,
        "tts_supported": True,
    }
    for language in LANGUAGES
]

UNSUPPORTED_VOICE_LANGUAGES = ("or", "ur")
