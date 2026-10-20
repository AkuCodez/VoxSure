"""Multilingual TEST set (typed text): 47 sentences x {en, hi, pa, de}.

Provenance (disclosed in the report): written by the project author/assistant, NOT verified by native
speakers, never used for training or threshold tuning. English is the control. Re-generate with:
    python ml/scripts/multilingual_testset.py
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "multilingual_test.jsonl"

# intent: [(en, hi, pa, de), ...]
DATA: dict[str, list[tuple[str, str, str, str]]] = {
    "library_hours": [
        ("What time does the library close in the evening?", "शाम को पुस्तकालय कितने बजे बंद होता है?", "ਸ਼ਾਮ ਨੂੰ ਲਾਇਬ੍ਰੇਰੀ ਕਿੰਨੇ ਵਜੇ ਬੰਦ ਹੁੰਦੀ ਹੈ?", "Um wie viel Uhr schließt die Bibliothek abends?"),
        ("Is the library open on Sunday?", "क्या रविवार को पुस्तकालय खुला रहता है?", "ਕੀ ਐਤਵਾਰ ਨੂੰ ਲਾਇਬ੍ਰੇਰੀ ਖੁੱਲ੍ਹੀ ਹੁੰਦੀ ਹੈ?", "Ist die Bibliothek sonntags geöffnet?"),
        ("What are the reading room hours?", "वाचनालय का समय क्या है?", "ਰੀਡਿੰਗ ਰੂਮ ਦਾ ਸਮਾਂ ਕੀ ਹੈ?", "Wie sind die Öffnungszeiten des Lesesaals?"),
    ],
    "library_borrow": [
        ("How many books can I borrow?", "मैं कितनी किताबें उधार ले सकता हूँ?", "ਮੈਂ ਕਿੰਨੀਆਂ ਕਿਤਾਬਾਂ ਉਧਾਰ ਲੈ ਸਕਦਾ ਹਾਂ?", "Wie viele Bücher kann ich ausleihen?"),
        ("How do I renew my book?", "मैं अपनी किताब की अवधि कैसे बढ़ाऊँ?", "ਮੈਂ ਆਪਣੀ ਕਿਤਾਬ ਦੀ ਮਿਆਦ ਕਿਵੇਂ ਵਧਾਵਾਂ?", "Wie verlängere ich mein Buch?"),
        ("What is the fine for late return of books?", "किताब देर से लौटाने पर कितना जुर्माना लगता है?", "ਕਿਤਾਬ ਦੇਰ ਨਾਲ ਮੋੜਨ 'ਤੇ ਕਿੰਨਾ ਜੁਰਮਾਨਾ ਲੱਗਦਾ ਹੈ?", "Wie hoch ist die Mahngebühr bei verspäteter Rückgabe?"),
    ],
    "academic_calendar": [
        ("When does the next semester begin?", "अगला सेमेस्टर कब शुरू होगा?", "ਅਗਲਾ ਸਮੈਸਟਰ ਕਦੋਂ ਸ਼ੁਰੂ ਹੋਵੇਗਾ?", "Wann beginnt das nächste Semester?"),
        ("When are the winter holidays?", "सर्दियों की छुट्टियाँ कब हैं?", "ਸਰਦੀਆਂ ਦੀਆਂ ਛੁੱਟੀਆਂ ਕਦੋਂ ਹਨ?", "Wann sind die Winterferien?"),
        ("Where can I see the academic calendar?", "मैं शैक्षणिक कैलेंडर कहाँ देख सकता हूँ?", "ਮੈਂ ਅਕਾਦਮਿਕ ਕੈਲੰਡਰ ਕਿੱਥੇ ਦੇਖ ਸਕਦਾ ਹਾਂ?", "Wo finde ich den Semesterkalender?"),
    ],
    "exam_info": [
        ("When are the final exams?", "अंतिम परीक्षाएँ कब हैं?", "ਫਾਈਨਲ ਪ੍ਰੀਖਿਆਵਾਂ ਕਦੋਂ ਹਨ?", "Wann sind die Abschlussprüfungen?"),
        ("How do I download my hall ticket?", "मैं अपना प्रवेश पत्र कैसे डाउनलोड करूँ?", "ਮੈਂ ਆਪਣਾ ਹਾਲ ਟਿਕਟ ਕਿਵੇਂ ਡਾਊਨਲੋਡ ਕਰਾਂ?", "Wie lade ich meine Prüfungszulassung herunter?"),
        ("When will the results be declared?", "परिणाम कब घोषित होंगे?", "ਨਤੀਜੇ ਕਦੋਂ ਐਲਾਨੇ ਜਾਣਗੇ?", "Wann werden die Ergebnisse veröffentlicht?"),
    ],
    "fee_payment": [
        ("How can I pay my fees online?", "मैं अपनी फीस ऑनलाइन कैसे जमा करूँ?", "ਮੈਂ ਆਪਣੀ ਫੀਸ ਆਨਲਾਈਨ ਕਿਵੇਂ ਭਰਾਂ?", "Wie kann ich meine Studiengebühren online bezahlen?"),
        ("What is the last date for fee payment?", "फीस जमा करने की आखिरी तारीख क्या है?", "ਫੀਸ ਭਰਨ ਦੀ ਆਖਰੀ ਤਾਰੀਖ ਕੀ ਹੈ?", "Was ist die letzte Frist für die Zahlung der Gebühren?"),
        ("I need a receipt for my fee payment", "मुझे अपनी फीस की रसीद चाहिए", "ਮੈਨੂੰ ਆਪਣੀ ਫੀਸ ਦੀ ਰਸੀਦ ਚਾਹੀਦੀ ਹੈ", "Ich brauche eine Quittung für meine Gebührenzahlung"),
    ],
    "hostel_info": [
        ("How do I apply for a hostel room?", "मैं छात्रावास के कमरे के लिए आवेदन कैसे करूँ?", "ਮੈਂ ਹੋਸਟਲ ਦੇ ਕਮਰੇ ਲਈ ਅਰਜ਼ੀ ਕਿਵੇਂ ਦੇਵਾਂ?", "Wie bewerbe ich mich um ein Zimmer im Wohnheim?"),
        ("What are the hostel curfew timings?", "छात्रावास में वापस आने का समय क्या है?", "ਹੋਸਟਲ ਵਿੱਚ ਵਾਪਸ ਆਉਣ ਦਾ ਸਮਾਂ ਕੀ ਹੈ?", "Bis wann muss man im Wohnheim zurück sein?"),
        ("Can visitors enter the hostel?", "क्या मेहमान छात्रावास में आ सकते हैं?", "ਕੀ ਮਹਿਮਾਨ ਹੋਸਟਲ ਵਿੱਚ ਆ ਸਕਦੇ ਹਨ?", "Dürfen Besucher ins Wohnheim kommen?"),
    ],
    "it_helpdesk": [
        ("I forgot my portal password", "मैं अपने पोर्टल का पासवर्ड भूल गया हूँ", "ਮੈਂ ਆਪਣੇ ਪੋਰਟਲ ਦਾ ਪਾਸਵਰਡ ਭੁੱਲ ਗਿਆ ਹਾਂ", "Ich habe mein Portal-Passwort vergessen"),
        ("The wifi is not working in my room", "मेरे कमरे में वाईफाई काम नहीं कर रहा है", "ਮੇਰੇ ਕਮਰੇ ਵਿੱਚ ਵਾਈਫਾਈ ਕੰਮ ਨਹੀਂ ਕਰ ਰਿਹਾ", "Das WLAN in meinem Zimmer funktioniert nicht"),
        ("Who do I contact for IT support?", "आईटी सहायता के लिए मैं किससे संपर्क करूँ?", "ਆਈਟੀ ਮਦਦ ਲਈ ਮੈਂ ਕਿਸ ਨਾਲ ਸੰਪਰਕ ਕਰਾਂ?", "An wen wende ich mich bei IT-Problemen?"),
    ],
    "placement_process": [
        ("How does the campus placement process work?", "कैंपस प्लेसमेंट की प्रक्रिया कैसे काम करती है?", "ਕੈਂਪਸ ਪਲੇਸਮੈਂਟ ਦੀ ਪ੍ਰਕਿਰਿਆ ਕਿਵੇਂ ਕੰਮ ਕਰਦੀ ਹੈ?", "Wie funktioniert das Campus-Placement?"),
        ("How do I register for placements?", "मैं प्लेसमेंट के लिए पंजीकरण कैसे करूँ?", "ਮੈਂ ਪਲੇਸਮੈਂਟ ਲਈ ਰਜਿਸਟਰ ਕਿਵੇਂ ਕਰਾਂ?", "Wie melde ich mich für das Placement an?"),
        ("Which companies come for recruitment?", "भर्ती के लिए कौन सी कंपनियाँ आती हैं?", "ਭਰਤੀ ਲਈ ਕਿਹੜੀਆਂ ਕੰਪਨੀਆਂ ਆਉਂਦੀਆਂ ਹਨ?", "Welche Firmen kommen zum Recruiting?"),
    ],
    "scholarship_aid": [
        ("What scholarships are available?", "कौन सी छात्रवृत्तियाँ उपलब्ध हैं?", "ਕਿਹੜੇ ਵਜ਼ੀਫ਼ੇ ਉਪਲਬਧ ਹਨ?", "Welche Stipendien gibt es?"),
        ("How do I apply for a scholarship?", "मैं छात्रवृत्ति के लिए आवेदन कैसे करूँ?", "ਮੈਂ ਵਜ਼ੀਫ਼ੇ ਲਈ ਅਰਜ਼ੀ ਕਿਵੇਂ ਦੇਵਾਂ?", "Wie beantrage ich ein Stipendium?"),
        ("What is the deadline for scholarship applications?", "छात्रवृत्ति आवेदन की अंतिम तिथि क्या है?", "ਵਜ਼ੀਫ਼ੇ ਦੀ ਅਰਜ਼ੀ ਦੀ ਆਖਰੀ ਤਾਰੀਖ ਕੀ ਹੈ?", "Bis wann kann ich mich für ein Stipendium bewerben?"),
    ],
    "certificates": [
        ("How do I get a bonafide certificate?", "मुझे बोनाफाइड प्रमाण पत्र कैसे मिलेगा?", "ਮੈਨੂੰ ਬੋਨਾਫਾਈਡ ਸਰਟੀਫਿਕੇਟ ਕਿਵੇਂ ਮਿਲੇਗਾ?", "Wie bekomme ich eine Studienbescheinigung?"),
        ("I need my transcript", "मुझे अपना ट्रांसक्रिप्ट चाहिए", "ਮੈਨੂੰ ਆਪਣਾ ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ ਚਾਹੀਦਾ ਹੈ", "Ich brauche meinen Notenauszug"),
        ("How do I get a duplicate marksheet?", "मुझे डुप्लिकेट अंकपत्र कैसे मिलेगा?", "ਮੈਨੂੰ ਡੁਪਲੀਕੇਟ ਮਾਰਕਸ਼ੀਟ ਕਿਵੇਂ ਮਿਲੇਗੀ?", "Wie bekomme ich eine Zweitschrift meines Zeugnisses?"),
    ],
    "campus_services": [
        ("What time does the canteen open?", "कैंटीन कितने बजे खुलती है?", "ਕੈਂਟੀਨ ਕਿੰਨੇ ਵਜੇ ਖੁੱਲ੍ਹਦੀ ਹੈ?", "Um wie viel Uhr öffnet die Mensa?"),
        ("Where is the medical centre?", "चिकित्सा केंद्र कहाँ है?", "ਮੈਡੀਕਲ ਸੈਂਟਰ ਕਿੱਥੇ ਹੈ?", "Wo ist das Gesundheitszentrum?"),
        ("Is there a bus service on campus?", "क्या कैंपस में बस सेवा है?", "ਕੀ ਕੈਂਪਸ ਵਿੱਚ ਬੱਸ ਸੇਵਾ ਹੈ?", "Gibt es einen Busdienst auf dem Campus?"),
    ],
    "greeting": [
        ("Hello", "नमस्ते", "ਸਤ ਸ੍ਰੀ ਅਕਾਲ", "Hallo"),
        ("Good morning", "सुप्रभात", "ਸ਼ੁਭ ਸਵੇਰ", "Guten Morgen"),
    ],
    "thanks_bye": [
        ("Thank you", "धन्यवाद", "ਧੰਨਵਾਦ", "Danke schön"),
        ("Goodbye", "अलविदा", "ਅਲਵਿਦਾ", "Auf Wiedersehen"),
    ],
    "about_bot": [
        ("What is your name?", "आपका नाम क्या है?", "ਤੁਹਾਡਾ ਨਾਮ ਕੀ ਹੈ?", "Wie heißt du?"),
        ("Are you a robot?", "क्या आप रोबोट हैं?", "ਕੀ ਤੁਸੀਂ ਰੋਬੋਟ ਹੋ?", "Bist du ein Roboter?"),
    ],
    "help_capabilities": [
        ("What can you do?", "आप क्या कर सकते हैं?", "ਤੁਸੀਂ ਕੀ ਕਰ ਸਕਦੇ ਹੋ?", "Was kannst du tun?"),
        ("What can I ask you?", "मैं आपसे क्या पूछ सकता हूँ?", "ਮੈਂ ਤੁਹਾਡੇ ਤੋਂ ਕੀ ਪੁੱਛ ਸਕਦਾ ਹਾਂ?", "Wobei kannst du mir helfen?"),
    ],
    "out_of_scope": [
        ("What is the weather today?", "आज मौसम कैसा है?", "ਅੱਜ ਮੌਸਮ ਕਿਹੋ ਜਿਹਾ ਹੈ?", "Wie ist das Wetter heute?"),
        ("Tell me a joke", "मुझे एक चुटकुला सुनाओ", "ਮੈਨੂੰ ਇੱਕ ਚੁਟਕੁਲਾ ਸੁਣਾਓ", "Erzähl mir einen Witz"),
        ("What is the capital of France?", "फ्रांस की राजधानी क्या है?", "ਫਰਾਂਸ ਦੀ ਰਾਜਧਾਨੀ ਕਿਹੜੀ ਹੈ?", "Was ist die Hauptstadt von Frankreich?"),
        ("Order me a pizza", "मेरे लिए पिज़्ज़ा ऑर्डर करो", "ਮੇਰੇ ਲਈ ਪੀਜ਼ਾ ਆਰਡਰ ਕਰੋ", "Bestelle mir eine Pizza"),
        ("What is the price of bitcoin?", "बिटकॉइन की कीमत क्या है?", "ਬਿਟਕੋਇਨ ਦੀ ਕੀਮਤ ਕੀ ਹੈ?", "Was kostet ein Bitcoin?"),
        ("Who won the cricket match yesterday?", "कल क्रिकेट मैच कौन जीता?", "ਕੱਲ੍ਹ ਕ੍ਰਿਕਟ ਮੈਚ ਕੌਣ ਜਿੱਤਿਆ?", "Wer hat gestern das Fußballspiel gewonnen?"),
    ],
}


def main() -> None:
    langs = ["en", "hi", "pa", "de"]
    rows = []
    for intent, items in DATA.items():
        for tup in items:
            for lang, text in zip(langs, tup):
                rows.append({"lang": lang, "text": text, "intent": intent})
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    per = {l: sum(r["lang"] == l for r in rows) for l in langs}
    print("wrote", OUT, per)


if __name__ == "__main__":
    main()
