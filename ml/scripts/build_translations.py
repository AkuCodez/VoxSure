"""Write backend/app/data/translations.json: curated Hindi, Punjabi and German versions of every fixed reply.

Provenance (disclosed in the report): written by the project author/assistant, NOT reviewed by native speakers.
They replace machine translation for these three languages because MT changed a fact in testing
(it rendered '09:00' Saturday opening as 'night nine' in Hindi). Other languages use NLLB with a numeric guard.
Run:  python ml/scripts/build_translations.py
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "backend" / "app" / "data" / "translations.json"
KEYS = ["library_hours", "library_borrow", "academic_calendar", "exam_info", "fee_payment", "hostel_info", "it_helpdesk",
        "placement_process", "scholarship_aid", "certificates", "campus_services", "greeting", "thanks_bye", "about_bot", "help_capabilities"]
SHORT_KEYS = KEYS[:11]

HI = {
    "short": ["पुस्तकालय के खुलने का समय", "पुस्तकालय की किताबें उधार लेना, अवधि बढ़ाना या जुर्माना", "शैक्षणिक कैलेंडर और महत्वपूर्ण तिथियाँ",
              "परीक्षा, प्रवेश पत्र या परिणाम", "फीस जमा करना या फीस की रसीद", "छात्रावास के कमरे, नियम या शुल्क",
              "वाई-फाई, पासवर्ड या पोर्टल लॉगिन की समस्या", "प्लेसमेंट और इंटर्नशिप", "छात्रवृत्ति और वित्तीय सहायता",
              "ट्रांसक्रिप्ट, बोनाफाइड या अन्य प्रमाण पत्र", "कैंपस सेवाएँ जैसे कैंटीन, चिकित्सा केंद्र या परिवहन"],
    "answer": [
        "केंद्रीय पुस्तकालय सोमवार से शुक्रवार 08:00 से 22:00 तक और शनिवार-रविवार 09:00 से 18:00 तक खुला रहता है। अंतिम परीक्षाओं के दो सप्ताह के दौरान वाचनालय 24:00 बजे तक खुला रहता है। सार्वजनिक अवकाश पर यह बंद रहता है।",
        "विद्यार्थी अपने छात्र पहचान पत्र से 14 दिनों के लिए अधिकतम 4 किताबें उधार ले सकते हैं। किताबों की अवधि पुस्तकालय खाते के माध्यम से ऑनलाइन दो बार बढ़ाई जा सकती है, बशर्ते किसी अन्य सदस्य ने उन्हें आरक्षित न किया हो। देर से लौटाने पर प्रति दिन 5 का जुर्माना लगता है, और खोई हुई किताब की सूचना सर्कुलेशन डेस्क को देनी होगी।",
        "शैक्षणिक कैलेंडर छात्र पोर्टल पर 'Academics' के अंतर्गत प्रकाशित होता है। इसमें सेमेस्टर की शुरुआत और समाप्ति की तिथियाँ, छुट्टियाँ, अवकाश, कोर्स जोड़ने/हटाने की अंतिम तिथियाँ और दीक्षांत समारोह की तिथि दी जाती है। नवीनतम स्वीकृत तिथियों के लिए वहीं देखें।",
        "परीक्षा समय-सारणी और प्रवेश पत्र परीक्षा से लगभग दो सप्ताह पहले छात्र पोर्टल पर जारी किए जाते हैं। अपना प्रवेश पत्र और छात्र पहचान पत्र साथ रखें। परिणाम पोर्टल पर प्रकाशित होते हैं, और परिणाम के बाद कुछ दिनों तक परीक्षा कार्यालय के माध्यम से पुनर्मूल्यांकन के अनुरोध स्वीकार किए जाते हैं।",
        "फीस छात्र पोर्टल के माध्यम से ऑनलाइन (कार्ड, नेट बैंकिंग या UPI) या कार्य समय के दौरान लेखा काउंटर पर जमा की जा सकती है। भुगतान के बाद रसीद अपने आप बन जाती है। यदि पैसे कट गए हैं लेकिन भुगतान विफल रहा, तो लेन-देन संदर्भ संख्या के साथ लेखा कार्यालय से संपर्क करें।",
        "छात्रावास के आवेदन प्रवेश की पुष्टि के बाद खुलते हैं, और कमरे छात्रावास कार्यालय द्वारा आवंटित किए जाते हैं। 22:00 बजे तक वापस आना अनिवार्य है, और मेहमान केवल आगंतुक कक्ष में ही मिल सकते हैं। रखरखाव की समस्याएँ छात्रावास वार्डन कार्यालय या हेल्पडेस्क को बताएँ।",
        "पासवर्ड रीसेट के लिए पोर्टल लॉगिन पृष्ठ पर 'Forgot password' लिंक का उपयोग करें। वाई-फाई या पोर्टल एक्सेस की समस्या के लिए मुख्य प्रशासनिक भवन में स्थित आईटी हेल्पडेस्क पर टिकट दर्ज करें। अपना छात्र आईडी और समस्या का संक्षिप्त विवरण बताएँ।",
        "विद्यार्थी प्लेसमेंट पोर्टल पर पंजीकरण करते हैं और अपना रिज़्यूमे अपलोड करते हैं। पात्र विद्यार्थियों को कंपनी ड्राइव के लिए चुना जाता है, जिनमें परीक्षा, साक्षात्कार और प्री-प्लेसमेंट वार्ता शामिल हैं। प्रशिक्षण एवं प्लेसमेंट कार्यालय मॉक इंटरव्यू भी आयोजित करता है। पात्रता मानदंड हर कंपनी के अनुसार घोषित किए जाते हैं।",
        "मेरिट आधारित और ज़रूरत आधारित छात्रवृत्तियाँ उपलब्ध हैं। आवेदन छात्र पोर्टल के माध्यम से आय प्रमाण और अंकपत्रों के साथ अधिसूचित अंतिम तिथि से पहले जमा किए जाते हैं। आप उसी पृष्ठ पर अपने आवेदन की स्थिति देख सकते हैं। पात्रता संबंधी प्रश्नों के लिए वित्तीय सहायता कार्यालय से संपर्क करें।",
        "बोनाफाइड, चरित्र और स्थानांतरण प्रमाण पत्र तथा ट्रांसक्रिप्ट के लिए छात्र पोर्टल के 'Certificates' अनुभाग में अनुरोध किया जाता है। प्रक्रिया में सामान्यतः तीन से सात कार्य दिवस लगते हैं। डुप्लिकेट दस्तावेज़ों के लिए रजिस्ट्रार कार्यालय में लिखित अनुरोध और शुल्क देना होता है।",
        "कैंटीन और फ़ूड कोर्ट 08:00 से 20:00 तक खुले रहते हैं। चिकित्सा केंद्र खेल परिसर के बगल में है और कार्य दिवसों में खुला रहता है। एक शटल छात्रावासों को शैक्षणिक भवन से जोड़ती है, और क्लबों का पंजीकरण हर सेमेस्टर की शुरुआत में खुलता है।",
        "नमस्ते! मैं VoxSure हूँ, छात्र सहायता सहायक। मुझसे पुस्तकालय, परीक्षा, फीस, छात्रावास, प्लेसमेंट, छात्रवृत्ति, प्रमाण पत्र या आईटी सहायता के बारे में पूछें।",
        "आपका स्वागत है! जब भी मदद चाहिए, फिर आइएगा।",
        "मैं VoxSure हूँ, आवाज़ से चलने वाला छात्र सहायता सहायक। मैं आपका प्रश्न सुनता हूँ, जो मैंने सुना वह दिखाता हूँ ताकि आप उसे सुधार सकें, समझता हूँ कि आपको क्या चाहिए, और एक जाँची हुई ज्ञान-सामग्री से उत्तर देता हूँ। जब मुझे यक़ीन नहीं होता, तो अंदाज़ा लगाने के बजाय आपसे पूछता हूँ। मैं एक एआई हूँ, इंसान नहीं।",
        "मैं इनमें मदद कर सकता हूँ: पुस्तकालय का समय और किताबें उधार लेना, शैक्षणिक कैलेंडर, परीक्षा और परिणाम, फीस जमा करना, छात्रावास, आईटी हेल्पडेस्क की समस्याएँ, प्लेसमेंट, छात्रवृत्ति, प्रमाण पत्र, और कैंटीन व चिकित्सा केंद्र जैसी कैंपस सेवाएँ। बस अपने शब्दों में पूछें, बोलकर या लिखकर। इन विषयों से बाहर कुछ पूछेंगे तो मैं साफ़ बता दूँगा ताकि आप दोबारा पूछ सकें या सही कार्यालय से संपर्क कर सकें।",
    ],
    "fallback_out_of_scope": "यह मेरी सहायता के दायरे से बाहर है, इसलिए मैं अंदाज़ा नहीं लगाऊँगा। मैं पुस्तकालय, कैलेंडर, परीक्षा, फीस, छात्रावास, आईटी सहायता, प्लेसमेंट, छात्रवृत्ति, प्रमाण पत्र और कैंपस सेवाओं के बारे में उत्तर दे सकता हूँ। दोबारा पूछ कर देखें, या पूछें \"आप क्या कर सकते हैं?\"",
    "fallback_repeated": "मुझे अब भी यक़ीन नहीं है कि मैं समझा या नहीं। आप अपना प्रश्न लिखकर पूछ सकते हैं, दूसरे शब्दों में कह सकते हैं, या फिर से शुरू करने के लिए Reset दबा सकते हैं।",
    "repair_prompt": "मुझे यक़ीन नहीं है कि मैंने सही सुना। कृपया लिखे हुए पाठ को जाँचकर सुधारें, या दोबारा बोलें।",
    "clarify_prompt_template": "सुनिश्चित करने के लिए, क्या आपका मतलब {options} से है?", "clarify_or": "या",
}

PA = {
    "short": ["ਲਾਇਬ੍ਰੇਰੀ ਦੇ ਖੁੱਲ੍ਹਣ ਦਾ ਸਮਾਂ", "ਲਾਇਬ੍ਰੇਰੀ ਦੀਆਂ ਕਿਤਾਬਾਂ ਉਧਾਰ ਲੈਣਾ, ਮਿਆਦ ਵਧਾਉਣਾ ਜਾਂ ਜੁਰਮਾਨਾ", "ਅਕਾਦਮਿਕ ਕੈਲੰਡਰ ਅਤੇ ਮਹੱਤਵਪੂਰਨ ਤਾਰੀਖਾਂ",
              "ਪ੍ਰੀਖਿਆ, ਹਾਲ ਟਿਕਟ ਜਾਂ ਨਤੀਜੇ", "ਫੀਸ ਭਰਨਾ ਜਾਂ ਫੀਸ ਦੀ ਰਸੀਦ", "ਹੋਸਟਲ ਦੇ ਕਮਰੇ, ਨਿਯਮ ਜਾਂ ਫੀਸ",
              "ਵਾਈ-ਫਾਈ, ਪਾਸਵਰਡ ਜਾਂ ਪੋਰਟਲ ਲੌਗਇਨ ਦੀ ਸਮੱਸਿਆ", "ਪਲੇਸਮੈਂਟ ਅਤੇ ਇੰਟਰਨਸ਼ਿਪ", "ਵਜ਼ੀਫ਼ੇ ਅਤੇ ਵਿੱਤੀ ਸਹਾਇਤਾ",
              "ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ, ਬੋਨਾਫਾਈਡ ਜਾਂ ਹੋਰ ਸਰਟੀਫਿਕੇਟ", "ਕੈਂਪਸ ਸੇਵਾਵਾਂ ਜਿਵੇਂ ਕੈਂਟੀਨ, ਮੈਡੀਕਲ ਸੈਂਟਰ ਜਾਂ ਆਵਾਜਾਈ"],
    "answer": [
        "ਕੇਂਦਰੀ ਲਾਇਬ੍ਰੇਰੀ ਸੋਮਵਾਰ ਤੋਂ ਸ਼ੁੱਕਰਵਾਰ 08:00 ਤੋਂ 22:00 ਤੱਕ ਅਤੇ ਸ਼ਨੀਵਾਰ-ਐਤਵਾਰ 09:00 ਤੋਂ 18:00 ਤੱਕ ਖੁੱਲ੍ਹੀ ਰਹਿੰਦੀ ਹੈ। ਫਾਈਨਲ ਪ੍ਰੀਖਿਆਵਾਂ ਦੇ ਦੋ ਹਫ਼ਤਿਆਂ ਦੌਰਾਨ ਰੀਡਿੰਗ ਹਾਲ 24:00 ਵਜੇ ਤੱਕ ਖੁੱਲ੍ਹਾ ਰਹਿੰਦਾ ਹੈ। ਸਰਕਾਰੀ ਛੁੱਟੀਆਂ ਵਾਲੇ ਦਿਨ ਇਹ ਬੰਦ ਰਹਿੰਦੀ ਹੈ।",
        "ਵਿਦਿਆਰਥੀ ਆਪਣੇ ਵਿਦਿਆਰਥੀ ਪਛਾਣ ਪੱਤਰ ਨਾਲ 14 ਦਿਨਾਂ ਲਈ ਵੱਧ ਤੋਂ ਵੱਧ 4 ਕਿਤਾਬਾਂ ਉਧਾਰ ਲੈ ਸਕਦੇ ਹਨ। ਕਿਤਾਬਾਂ ਦੀ ਮਿਆਦ ਲਾਇਬ੍ਰੇਰੀ ਖਾਤੇ ਰਾਹੀਂ ਆਨਲਾਈਨ ਦੋ ਵਾਰ ਵਧਾਈ ਜਾ ਸਕਦੀ ਹੈ, ਬਸ਼ਰਤੇ ਕਿਸੇ ਹੋਰ ਮੈਂਬਰ ਨੇ ਉਹਨਾਂ ਨੂੰ ਰਾਖਵਾਂ ਨਾ ਕੀਤਾ ਹੋਵੇ। ਦੇਰ ਨਾਲ ਮੋੜਨ 'ਤੇ ਪ੍ਰਤੀ ਦਿਨ 5 ਦਾ ਜੁਰਮਾਨਾ ਲੱਗਦਾ ਹੈ, ਅਤੇ ਗੁਆਚੀ ਕਿਤਾਬ ਦੀ ਸੂਚਨਾ ਸਰਕੂਲੇਸ਼ਨ ਡੈਸਕ ਨੂੰ ਦੇਣੀ ਪਵੇਗੀ।",
        "ਅਕਾਦਮਿਕ ਕੈਲੰਡਰ ਵਿਦਿਆਰਥੀ ਪੋਰਟਲ 'ਤੇ 'Academics' ਹੇਠ ਪ੍ਰਕਾਸ਼ਿਤ ਹੁੰਦਾ ਹੈ। ਇਸ ਵਿੱਚ ਸਮੈਸਟਰ ਦੀ ਸ਼ੁਰੂਆਤ ਤੇ ਸਮਾਪਤੀ ਦੀਆਂ ਤਾਰੀਖਾਂ, ਛੁੱਟੀਆਂ, ਕੋਰਸ ਜੋੜਨ/ਹਟਾਉਣ ਦੀਆਂ ਆਖਰੀ ਤਾਰੀਖਾਂ ਅਤੇ ਕਨਵੋਕੇਸ਼ਨ ਦੀ ਤਾਰੀਖ ਦਿੱਤੀ ਹੁੰਦੀ ਹੈ। ਤਾਜ਼ਾ ਮਨਜ਼ੂਰਸ਼ੁਦਾ ਤਾਰੀਖਾਂ ਲਈ ਉੱਥੇ ਹੀ ਦੇਖੋ।",
        "ਪ੍ਰੀਖਿਆ ਦੀ ਸਮਾਂ-ਸਾਰਣੀ ਅਤੇ ਹਾਲ ਟਿਕਟ ਪ੍ਰੀਖਿਆ ਤੋਂ ਲਗਭਗ ਦੋ ਹਫ਼ਤੇ ਪਹਿਲਾਂ ਵਿਦਿਆਰਥੀ ਪੋਰਟਲ 'ਤੇ ਜਾਰੀ ਕੀਤੇ ਜਾਂਦੇ ਹਨ। ਆਪਣਾ ਹਾਲ ਟਿਕਟ ਅਤੇ ਵਿਦਿਆਰਥੀ ਪਛਾਣ ਪੱਤਰ ਨਾਲ ਰੱਖੋ। ਨਤੀਜੇ ਪੋਰਟਲ 'ਤੇ ਪ੍ਰਕਾਸ਼ਿਤ ਹੁੰਦੇ ਹਨ, ਅਤੇ ਨਤੀਜੇ ਤੋਂ ਬਾਅਦ ਕੁਝ ਦਿਨਾਂ ਤੱਕ ਪ੍ਰੀਖਿਆ ਦਫ਼ਤਰ ਰਾਹੀਂ ਮੁੜ-ਮੁਲਾਂਕਣ ਦੀਆਂ ਬੇਨਤੀਆਂ ਸਵੀਕਾਰ ਕੀਤੀਆਂ ਜਾਂਦੀਆਂ ਹਨ।",
        "ਫੀਸ ਵਿਦਿਆਰਥੀ ਪੋਰਟਲ ਰਾਹੀਂ ਆਨਲਾਈਨ (ਕਾਰਡ, ਨੈੱਟ ਬੈਂਕਿੰਗ ਜਾਂ UPI) ਜਾਂ ਕੰਮ ਦੇ ਸਮੇਂ ਦੌਰਾਨ ਲੇਖਾ ਕਾਊਂਟਰ 'ਤੇ ਭਰੀ ਜਾ ਸਕਦੀ ਹੈ। ਭੁਗਤਾਨ ਤੋਂ ਬਾਅਦ ਰਸੀਦ ਆਪਣੇ-ਆਪ ਬਣ ਜਾਂਦੀ ਹੈ। ਜੇ ਪੈਸੇ ਕੱਟੇ ਗਏ ਪਰ ਭੁਗਤਾਨ ਅਸਫਲ ਰਿਹਾ, ਤਾਂ ਲੈਣ-ਦੇਣ ਦੇ ਹਵਾਲਾ ਨੰਬਰ ਨਾਲ ਲੇਖਾ ਦਫ਼ਤਰ ਨਾਲ ਸੰਪਰਕ ਕਰੋ।",
        "ਹੋਸਟਲ ਦੀਆਂ ਅਰਜ਼ੀਆਂ ਦਾਖ਼ਲੇ ਦੀ ਪੁਸ਼ਟੀ ਤੋਂ ਬਾਅਦ ਖੁੱਲ੍ਹਦੀਆਂ ਹਨ, ਅਤੇ ਕਮਰੇ ਹੋਸਟਲ ਦਫ਼ਤਰ ਵੱਲੋਂ ਅਲਾਟ ਕੀਤੇ ਜਾਂਦੇ ਹਨ। 22:00 ਵਜੇ ਤੱਕ ਵਾਪਸ ਆਉਣਾ ਲਾਜ਼ਮੀ ਹੈ, ਅਤੇ ਮਹਿਮਾਨ ਸਿਰਫ਼ ਮੁਲਾਕਾਤੀ ਲਾਊਂਜ ਵਿੱਚ ਹੀ ਮਿਲ ਸਕਦੇ ਹਨ। ਮੁਰੰਮਤ ਦੀਆਂ ਸਮੱਸਿਆਵਾਂ ਹੋਸਟਲ ਵਾਰਡਨ ਦਫ਼ਤਰ ਜਾਂ ਹੈਲਪਡੈਸਕ ਨੂੰ ਦੱਸੋ।",
        "ਪਾਸਵਰਡ ਰੀਸੈੱਟ ਲਈ ਪੋਰਟਲ ਲੌਗਇਨ ਪੰਨੇ 'ਤੇ 'Forgot password' ਲਿੰਕ ਵਰਤੋ। ਵਾਈ-ਫਾਈ ਜਾਂ ਪੋਰਟਲ ਪਹੁੰਚ ਦੀ ਸਮੱਸਿਆ ਲਈ ਮੁੱਖ ਪ੍ਰਬੰਧਕੀ ਇਮਾਰਤ ਵਿੱਚ ਸਥਿਤ ਆਈਟੀ ਹੈਲਪਡੈਸਕ 'ਤੇ ਟਿਕਟ ਦਰਜ ਕਰੋ। ਆਪਣਾ ਵਿਦਿਆਰਥੀ ਆਈਡੀ ਅਤੇ ਸਮੱਸਿਆ ਦਾ ਸੰਖੇਪ ਵੇਰਵਾ ਦੱਸੋ।",
        "ਵਿਦਿਆਰਥੀ ਪਲੇਸਮੈਂਟ ਪੋਰਟਲ 'ਤੇ ਰਜਿਸਟਰ ਕਰਦੇ ਹਨ ਅਤੇ ਆਪਣਾ ਰਿਜ਼ਿਊਮੇ ਅੱਪਲੋਡ ਕਰਦੇ ਹਨ। ਯੋਗ ਵਿਦਿਆਰਥੀਆਂ ਨੂੰ ਕੰਪਨੀ ਡਰਾਈਵਾਂ ਲਈ ਚੁਣਿਆ ਜਾਂਦਾ ਹੈ, ਜਿਨ੍ਹਾਂ ਵਿੱਚ ਟੈਸਟ, ਇੰਟਰਵਿਊ ਅਤੇ ਪ੍ਰੀ-ਪਲੇਸਮੈਂਟ ਗੱਲਬਾਤ ਸ਼ਾਮਲ ਹਨ। ਸਿਖਲਾਈ ਅਤੇ ਪਲੇਸਮੈਂਟ ਦਫ਼ਤਰ ਮੌਕ ਇੰਟਰਵਿਊ ਵੀ ਕਰਵਾਉਂਦਾ ਹੈ। ਯੋਗਤਾ ਦੇ ਮਾਪਦੰਡ ਹਰ ਕੰਪਨੀ ਅਨੁਸਾਰ ਐਲਾਨੇ ਜਾਂਦੇ ਹਨ।",
        "ਮੈਰਿਟ ਅਤੇ ਲੋੜ ਆਧਾਰਿਤ ਵਜ਼ੀਫ਼ੇ ਉਪਲਬਧ ਹਨ। ਅਰਜ਼ੀਆਂ ਵਿਦਿਆਰਥੀ ਪੋਰਟਲ ਰਾਹੀਂ ਆਮਦਨ ਦੇ ਸਬੂਤ ਅਤੇ ਅੰਕ-ਪੱਤਰਾਂ ਸਮੇਤ ਐਲਾਨੀ ਗਈ ਆਖਰੀ ਤਾਰੀਖ ਤੋਂ ਪਹਿਲਾਂ ਜਮ੍ਹਾਂ ਕੀਤੀਆਂ ਜਾਂਦੀਆਂ ਹਨ। ਤੁਸੀਂ ਉਸੇ ਪੰਨੇ 'ਤੇ ਆਪਣੀ ਅਰਜ਼ੀ ਦੀ ਸਥਿਤੀ ਦੇਖ ਸਕਦੇ ਹੋ। ਯੋਗਤਾ ਸੰਬੰਧੀ ਸਵਾਲਾਂ ਲਈ ਵਿੱਤੀ ਸਹਾਇਤਾ ਦਫ਼ਤਰ ਨਾਲ ਸੰਪਰਕ ਕਰੋ।",
        "ਬੋਨਾਫਾਈਡ, ਚਰਿੱਤਰ ਅਤੇ ਤਬਾਦਲਾ ਸਰਟੀਫਿਕੇਟ ਅਤੇ ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ ਲਈ ਵਿਦਿਆਰਥੀ ਪੋਰਟਲ ਦੇ 'Certificates' ਭਾਗ ਵਿੱਚ ਬੇਨਤੀ ਕੀਤੀ ਜਾਂਦੀ ਹੈ। ਪ੍ਰਕਿਰਿਆ ਵਿੱਚ ਆਮ ਤੌਰ 'ਤੇ ਤਿੰਨ ਤੋਂ ਸੱਤ ਕੰਮ ਦੇ ਦਿਨ ਲੱਗਦੇ ਹਨ। ਡੁਪਲੀਕੇਟ ਦਸਤਾਵੇਜ਼ਾਂ ਲਈ ਰਜਿਸਟਰਾਰ ਦਫ਼ਤਰ ਵਿੱਚ ਲਿਖਤੀ ਬੇਨਤੀ ਅਤੇ ਫੀਸ ਦੇਣੀ ਪੈਂਦੀ ਹੈ।",
        "ਕੈਂਟੀਨ ਅਤੇ ਫੂਡ ਕੋਰਟ 08:00 ਤੋਂ 20:00 ਤੱਕ ਖੁੱਲ੍ਹੇ ਰਹਿੰਦੇ ਹਨ। ਮੈਡੀਕਲ ਸੈਂਟਰ ਖੇਡ ਕੰਪਲੈਕਸ ਦੇ ਕੋਲ ਹੈ ਅਤੇ ਕੰਮ ਵਾਲੇ ਦਿਨਾਂ ਵਿੱਚ ਖੁੱਲ੍ਹਾ ਰਹਿੰਦਾ ਹੈ। ਇੱਕ ਸ਼ਟਲ ਹੋਸਟਲਾਂ ਨੂੰ ਅਕਾਦਮਿਕ ਇਮਾਰਤ ਨਾਲ ਜੋੜਦੀ ਹੈ, ਅਤੇ ਕਲੱਬਾਂ ਦੀ ਰਜਿਸਟ੍ਰੇਸ਼ਨ ਹਰ ਸਮੈਸਟਰ ਦੀ ਸ਼ੁਰੂਆਤ ਵਿੱਚ ਖੁੱਲ੍ਹਦੀ ਹੈ।",
        "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ VoxSure ਹਾਂ, ਵਿਦਿਆਰਥੀ ਸਹਾਇਤਾ ਸਹਾਇਕ। ਮੈਨੂੰ ਲਾਇਬ੍ਰੇਰੀ, ਪ੍ਰੀਖਿਆ, ਫੀਸ, ਹੋਸਟਲ, ਪਲੇਸਮੈਂਟ, ਵਜ਼ੀਫ਼ੇ, ਸਰਟੀਫਿਕੇਟ ਜਾਂ ਆਈਟੀ ਮਦਦ ਬਾਰੇ ਪੁੱਛੋ।",
        "ਜੀ ਆਇਆਂ ਨੂੰ! ਜਦੋਂ ਵੀ ਮਦਦ ਦੀ ਲੋੜ ਹੋਵੇ, ਦੁਬਾਰਾ ਆਇਓ।",
        "ਮੈਂ VoxSure ਹਾਂ, ਆਵਾਜ਼ ਨਾਲ ਚੱਲਣ ਵਾਲਾ ਵਿਦਿਆਰਥੀ ਸਹਾਇਤਾ ਸਹਾਇਕ। ਮੈਂ ਤੁਹਾਡਾ ਸਵਾਲ ਸੁਣਦਾ ਹਾਂ, ਜੋ ਮੈਂ ਸੁਣਿਆ ਉਹ ਦਿਖਾਉਂਦਾ ਹਾਂ ਤਾਂ ਜੋ ਤੁਸੀਂ ਉਸਨੂੰ ਠੀਕ ਕਰ ਸਕੋ, ਸਮਝਦਾ ਹਾਂ ਕਿ ਤੁਹਾਨੂੰ ਕੀ ਚਾਹੀਦਾ ਹੈ, ਅਤੇ ਜਾਂਚੀ ਹੋਈ ਜਾਣਕਾਰੀ ਵਿੱਚੋਂ ਜਵਾਬ ਦਿੰਦਾ ਹਾਂ। ਜਦੋਂ ਮੈਨੂੰ ਯਕੀਨ ਨਹੀਂ ਹੁੰਦਾ, ਤਾਂ ਅੰਦਾਜ਼ਾ ਲਗਾਉਣ ਦੀ ਬਜਾਏ ਤੁਹਾਡੇ ਤੋਂ ਪੁੱਛਦਾ ਹਾਂ। ਮੈਂ ਇੱਕ ਏਆਈ ਹਾਂ, ਇਨਸਾਨ ਨਹੀਂ।",
        "ਮੈਂ ਇਨ੍ਹਾਂ ਵਿੱਚ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ: ਲਾਇਬ੍ਰੇਰੀ ਦਾ ਸਮਾਂ ਅਤੇ ਕਿਤਾਬਾਂ ਉਧਾਰ ਲੈਣਾ, ਅਕਾਦਮਿਕ ਕੈਲੰਡਰ, ਪ੍ਰੀਖਿਆ ਅਤੇ ਨਤੀਜੇ, ਫੀਸ ਭਰਨਾ, ਹੋਸਟਲ, ਆਈਟੀ ਹੈਲਪਡੈਸਕ ਦੀਆਂ ਸਮੱਸਿਆਵਾਂ, ਪਲੇਸਮੈਂਟ, ਵਜ਼ੀਫ਼ੇ, ਸਰਟੀਫਿਕੇਟ, ਅਤੇ ਕੈਂਟੀਨ ਤੇ ਮੈਡੀਕਲ ਸੈਂਟਰ ਵਰਗੀਆਂ ਕੈਂਪਸ ਸੇਵਾਵਾਂ। ਬੱਸ ਆਪਣੇ ਸ਼ਬਦਾਂ ਵਿੱਚ ਪੁੱਛੋ, ਬੋਲ ਕੇ ਜਾਂ ਲਿਖ ਕੇ। ਇਨ੍ਹਾਂ ਵਿਸ਼ਿਆਂ ਤੋਂ ਬਾਹਰ ਕੁਝ ਪੁੱਛੋਗੇ ਤਾਂ ਮੈਂ ਸਾਫ਼ ਦੱਸ ਦਿਆਂਗਾ ਤਾਂ ਜੋ ਤੁਸੀਂ ਦੁਬਾਰਾ ਪੁੱਛ ਸਕੋ ਜਾਂ ਸਹੀ ਦਫ਼ਤਰ ਨਾਲ ਸੰਪਰਕ ਕਰ ਸਕੋ।",
    ],
    "fallback_out_of_scope": "ਇਹ ਮੇਰੀ ਮਦਦ ਦੇ ਦਾਇਰੇ ਤੋਂ ਬਾਹਰ ਹੈ, ਇਸ ਲਈ ਮੈਂ ਅੰਦਾਜ਼ਾ ਨਹੀਂ ਲਗਾਵਾਂਗਾ। ਮੈਂ ਲਾਇਬ੍ਰੇਰੀ, ਕੈਲੰਡਰ, ਪ੍ਰੀਖਿਆ, ਫੀਸ, ਹੋਸਟਲ, ਆਈਟੀ ਮਦਦ, ਪਲੇਸਮੈਂਟ, ਵਜ਼ੀਫ਼ੇ, ਸਰਟੀਫਿਕੇਟ ਅਤੇ ਕੈਂਪਸ ਸੇਵਾਵਾਂ ਬਾਰੇ ਜਵਾਬ ਦੇ ਸਕਦਾ ਹਾਂ। ਦੁਬਾਰਾ ਪੁੱਛ ਕੇ ਦੇਖੋ, ਜਾਂ ਪੁੱਛੋ \"ਤੁਸੀਂ ਕੀ ਕਰ ਸਕਦੇ ਹੋ?\"",
    "fallback_repeated": "ਮੈਨੂੰ ਹਾਲੇ ਵੀ ਯਕੀਨ ਨਹੀਂ ਕਿ ਮੈਂ ਸਮਝਿਆ ਜਾਂ ਨਹੀਂ। ਤੁਸੀਂ ਆਪਣਾ ਸਵਾਲ ਲਿਖ ਕੇ ਪੁੱਛ ਸਕਦੇ ਹੋ, ਦੂਜੇ ਸ਼ਬਦਾਂ ਵਿੱਚ ਕਹਿ ਸਕਦੇ ਹੋ, ਜਾਂ ਦੁਬਾਰਾ ਸ਼ੁਰੂ ਕਰਨ ਲਈ Reset ਦਬਾ ਸਕਦੇ ਹੋ।",
    "repair_prompt": "ਮੈਨੂੰ ਯਕੀਨ ਨਹੀਂ ਕਿ ਮੈਂ ਸਹੀ ਸੁਣਿਆ। ਕਿਰਪਾ ਕਰਕੇ ਲਿਖੇ ਹੋਏ ਪਾਠ ਨੂੰ ਜਾਂਚ ਕੇ ਠੀਕ ਕਰੋ, ਜਾਂ ਦੁਬਾਰਾ ਬੋਲੋ।",
    "clarify_prompt_template": "ਪੱਕਾ ਕਰਨ ਲਈ, ਕੀ ਤੁਹਾਡਾ ਮਤਲਬ {options} ਤੋਂ ਹੈ?", "clarify_or": "ਜਾਂ",
}

DE = {
    "short": ["die Öffnungszeiten der Bibliothek", "Ausleihe, Verlängerung oder Mahngebühren der Bibliothek", "den Semesterkalender und wichtige Termine",
              "Prüfungen, Zulassung oder Ergebnisse", "Gebührenzahlung oder Quittungen", "Wohnheimzimmer, Regeln oder Kosten",
              "WLAN-, Passwort- oder Portal-Probleme", "Placement und Praktika", "Stipendien und finanzielle Unterstützung",
              "Notenauszüge, Studienbescheinigungen oder andere Zeugnisse", "Campus-Angebote wie Mensa, Gesundheitszentrum oder Verkehr"],
    "answer": [
        "Die Zentralbibliothek ist Montag bis Freitag von 08:00 bis 22:00 Uhr und Samstag und Sonntag von 09:00 bis 18:00 Uhr geöffnet. In den zwei Wochen der Abschlussprüfungen bleibt der Lesesaal bis 24:00 Uhr geöffnet. An gesetzlichen Feiertagen ist sie geschlossen.",
        "Studierende können mit ihrem Studierendenausweis bis zu 4 Bücher für 14 Tage ausleihen. Bücher können über das Bibliothekskonto zweimal online verlängert werden, sofern sie nicht von einem anderen Mitglied vorgemerkt sind. Bei verspäteter Rückgabe fallen 5 pro Tag an, und verlorene Bücher müssen bei der Ausleihtheke gemeldet werden.",
        "Der Semesterkalender wird im Studierendenportal unter „Academics“ veröffentlicht. Er enthält Semesterbeginn und -ende, Feiertage, Ferien, Fristen zum Hinzufügen und Abwählen von Kursen sowie den Termin der Abschlussfeier. Die aktuell gültigen Termine finden Sie dort.",
        "Prüfungsplan und Prüfungszulassung werden etwa zwei Wochen vor den Prüfungen im Studierendenportal veröffentlicht. Bringen Sie Ihre Zulassung und Ihren Studierendenausweis mit. Die Ergebnisse werden im Portal veröffentlicht, und Anträge auf Neubewertung werden nach Bekanntgabe einige Tage lang über das Prüfungsamt angenommen.",
        "Gebühren können online über das Studierendenportal (Karte, Online-Banking oder UPI) oder während der Geschäftszeiten am Kassenschalter bezahlt werden. Nach der Zahlung wird automatisch eine Quittung erstellt. Wurde Geld abgebucht, die Zahlung aber nicht abgeschlossen, wenden Sie sich mit der Transaktionsnummer an die Finanzabteilung.",
        "Die Bewerbung um einen Wohnheimplatz öffnet nach der Zulassungsbestätigung, und die Zimmer werden vom Wohnheimbüro vergeben. Die Ausgangssperre beginnt um 22:00 Uhr, und Besucher sind nur im Besucherraum erlaubt. Reparaturprobleme melden Sie dem Büro der Wohnheimleitung oder dem Helpdesk.",
        "Zum Zurücksetzen des Passworts nutzen Sie den Link „Forgot password“ auf der Anmeldeseite des Portals. Bei WLAN- oder Portalproblemen erstellen Sie ein Ticket beim IT-Helpdesk im Hauptverwaltungsgebäude. Nennen Sie Ihre Matrikelnummer und eine kurze Beschreibung des Problems.",
        "Studierende registrieren sich im Placement-Portal und laden ihren Lebenslauf hoch. Geeignete Studierende werden für Unternehmenstage ausgewählt, die Tests, Interviews und Vorträge vor dem Placement umfassen. Das Karrierebüro bietet außerdem Probeinterviews an. Die Zulassungskriterien werden pro Unternehmen bekannt gegeben.",
        "Es gibt leistungs- und bedarfsabhängige Stipendien. Anträge werden über das Studierendenportal mit Einkommensnachweis und Notenübersichten vor Ablauf der bekannt gegebenen Frist eingereicht. Den Bearbeitungsstatus können Sie auf derselben Seite verfolgen. Bei Fragen zur Berechtigung wenden Sie sich an das Büro für finanzielle Unterstützung.",
        "Studienbescheinigungen, Führungsbescheinigungen, Abgangsbescheinigungen und Notenauszüge werden im Bereich „Certificates“ des Studierendenportals beantragt. Die Bearbeitung dauert normalerweise drei bis sieben Werktage. Für Zweitschriften sind ein schriftlicher Antrag und eine Gebühr beim Studierendensekretariat nötig.",
        "Mensa und Food Court sind von 08:00 bis 20:00 Uhr geöffnet. Das Gesundheitszentrum liegt neben der Sportanlage und ist werktags geöffnet. Ein Shuttle verbindet die Wohnheime mit dem Hochschulgebäude, und die Anmeldung für Clubs öffnet zu Beginn jedes Semesters.",
        "Hallo! Ich bin VoxSure, ein Assistent für Studierende. Fragen Sie mich zu Bibliothek, Prüfungen, Gebühren, Wohnheimen, Placement, Stipendien, Bescheinigungen oder IT-Hilfe.",
        "Gern geschehen! Kommen Sie jederzeit wieder, wenn Sie Hilfe brauchen.",
        "Ich bin VoxSure, ein sprachgesteuerter Assistent für Studierende. Ich höre Ihre Frage, zeige Ihnen, was ich verstanden habe, damit Sie es korrigieren können, finde heraus, was Sie brauchen, und antworte aus einer geprüften Wissensbasis. Wenn ich unsicher bin, frage ich nach, statt zu raten. Ich bin eine KI, kein Mensch.",
        "Ich kann helfen bei: Öffnungszeiten und Ausleihe der Bibliothek, Semesterkalender, Prüfungen und Ergebnissen, Gebührenzahlung, Wohnheimen, IT-Helpdesk-Problemen, Placement, Stipendien, Bescheinigungen sowie Campus-Angeboten wie Mensa und Gesundheitszentrum. Fragen Sie einfach mit eigenen Worten, per Sprache oder Text. Fragen außerhalb dieser Themen beantworte ich nicht, sondern sage es Ihnen klar, damit Sie umformulieren oder das richtige Büro kontaktieren können.",
    ],
    "fallback_out_of_scope": "Das liegt außerhalb dessen, wobei ich helfen kann, daher rate ich nicht. Ich kann Fragen zu Bibliothek, Kalender, Prüfungen, Gebühren, Wohnheimen, IT-Hilfe, Placement, Stipendien, Bescheinigungen und Campus-Angeboten beantworten. Formulieren Sie es um oder fragen Sie: „Was kannst du tun?“",
    "fallback_repeated": "Ich bin immer noch nicht sicher, ob ich Sie richtig verstanden habe. Sie können Ihre Frage eintippen, anders formulieren oder mit Reset neu beginnen.",
    "repair_prompt": "Ich bin nicht sicher, ob ich das richtig gehört habe. Bitte prüfen und korrigieren Sie den Text oder sagen Sie es noch einmal.",
    "clarify_prompt_template": "Nur zur Sicherheit: Meinen Sie {options}?", "clarify_or": "oder",
}


def pack(d: dict) -> dict:
    assert len(d["answer"]) == len(KEYS) and len(d["short"]) == len(SHORT_KEYS)
    intents = {k: {"answer": a} for k, a in zip(KEYS, d["answer"])}
    for k, s in zip(SHORT_KEYS, d["short"]):
        intents[k]["short"] = s
        intents[k]["label"] = s
    return {"intents": intents, **{k: d[k] for k in ("fallback_out_of_scope", "fallback_repeated", "repair_prompt", "clarify_prompt_template", "clarify_or")}}


def main() -> None:
    doc = {"_provenance": "Author-written, not reviewed by native speakers; replaces machine translation for these languages.",
           "hi": pack(HI), "pa": pack(PA), "de": pack(DE)}
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", OUT, {k: len(v["intents"]) for k, v in doc.items() if isinstance(v, dict)})


if __name__ == "__main__":
    main()
