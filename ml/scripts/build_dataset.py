"""Build the VoxSure intent dataset (deterministic, seed=42).

Provenance: every seed utterance below was written by the project author for this
project (no scraped or third-party data, no licence issues). Seeds are expanded with
conversational fillers and plausible ASR-style corruptions. All variants of one seed
share a `group` id and are assigned to ONE split together, which prevents
near-duplicate leakage between train/val/test.

Outputs (ml/data/): train.jsonl, val.jsonl, test.jsonl, ambiguous_eval.jsonl, stats.json
"""
from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

SEED = 42
OUT = Path(__file__).resolve().parents[1] / "data"

SEEDS: dict[str, list[str]] = {
    "library_hours": [
        "What time does the library open?",
        "Until what time is the library open tonight?",
        "Is the library open on Sundays?",
        "What are the library timings during exams?",
        "Does the library stay open late on weekdays?",
        "When does the library close today?",
        "Library opening hours please",
        "Can I study in the library on public holidays?",
        "Tell me the reading room timings",
        "How late can I stay at the central library?",
        "Is the library open this weekend?",
        "What are the working hours of the library?",
        "Is the reading hall open twenty four hours during finals?",
        "At what time does the library shut on Saturdays?",
        "Are there special library hours in the vacation?",
        "I want to know when the library is open",
    ],
    "library_borrow": [
        "How many books can I borrow from the library?",
        "How do I renew a library book?",
        "What is the fine for returning a book late?",
        "I lost a library book, what should I do?",
        "How long can I keep a borrowed book?",
        "Can I issue a book with my student ID card?",
        "How do I reserve a book that is already checked out?",
        "Where do I return borrowed books?",
        "Can I access e-journals and online databases from home?",
        "How do I get a library membership card?",
        "What is the loan period for reference books?",
        "Can I extend the due date of my issued book?",
        "How do I pay my overdue library fine?",
        "I want to renew my books online",
        "Is there a limit on the number of books I can take out?",
        "How do I request a book that the library does not have?",
    ],
    "academic_calendar": [
        "When does the next semester start?",
        "What are the dates of the winter break?",
        "When is the last day of classes this term?",
        "Where can I find the academic calendar?",
        "When do the semester registrations begin?",
        "Is there a holiday on the national day?",
        "What is the last date to add or drop a course?",
        "When does the spring term begin?",
        "Tell me the important dates for this semester",
        "When is the convocation ceremony?",
        "When will the new academic year start?",
        "What is the schedule for the mid semester break?",
        "Can you tell me the last working day before vacation?",
        "When is the course registration deadline?",
        "How many holidays do we get in the semester?",
        "When do classes resume after the break?",
    ],
    "exam_info": [
        "How many attempts do I get to clear a paper?",
        "Can I see my answer sheet after the result?",
        "What is the dress code for the exam hall?",
        "How do I change my exam centre?",
        "What if I lose my admit card on the exam day?",
        "Will there be a make up test for missed internals?",
        "How long do I have to apply for rechecking?",
        "When are practical exams held?",
        "When are the final exams?",
        "How do I download my hall ticket?",
        "Where can I see the exam timetable?",
        "When will the exam results be declared?",
        "How do I apply for revaluation of my paper?",
        "What is the procedure to apply for a supplementary exam?",
        "What should I carry to the examination hall?",
        "How can I check my semester results?",
        "What happens if I miss an exam because of illness?",
        "Is a calculator allowed in the exam?",
        "When is the date sheet for end semester exams released?",
        "How do I get my admit card for the test?",
        "Can I see my marks for the internal assessment?",
        "How do I apply for a re-exam?",
        "What is the passing criteria for a course?",
        "Where do I check my seat number for the exam?",
    ],
    "fee_payment": [
        "I paid twice by mistake, can I get one payment back?",
        "Can parents pay the fees on my behalf?",
        "How do I get a bank challan for fees?",
        "What happens if I miss the fee deadline?",
        "Can I pay the examination fee online?",
        "Where do I see my pending dues?",
        "Is the hostel fee included in the tuition fee?",
        "Can I pay fees using an education loan?",
        "How do I pay my tuition fees?",
        "What is the last date to pay the semester fee?",
        "Can I pay my fees in instalments?",
        "Is there a late fee for delayed payment?",
        "How do I get a fee receipt?",
        "My fee payment failed but money was deducted, what now?",
        "Can I pay the fees online?",
        "Where can I find the fee structure?",
        "How do I get a refund of my fees?",
        "Which payment methods are accepted for fees?",
        "I want to know the hostel and tuition fee amount",
        "How do I check whether my fees are paid?",
        "Is there a fee waiver or concession for siblings?",
        "What is the due date for the next fee instalment?",
        "I need a duplicate fee receipt",
        "Where do I go to pay fees in person?",
    ],
    "hostel_info": [
        "What is the mess menu this week?",
        "Can I bring my own electric kettle to the hostel?",
        "How do I vacate my hostel room?",
        "What is the hostel security deposit?",
        "Is there a gym or common room in the hostel?",
        "Can I get a roommate of my choice?",
        "What time does the hostel mess serve dinner?",
        "How do I complain about noise in the hostel?",
        "How do I apply for a hostel room?",
        "What are the hostel curfew timings?",
        "Can I change my hostel room?",
        "What facilities are available in the hostel?",
        "Are visitors allowed inside the hostel?",
        "How much is the hostel rent per semester?",
        "How do I report a maintenance problem in my hostel room?",
        "Is the hostel mess food included in the fee?",
        "What is the hostel check-out procedure before vacation?",
        "Do the hostels have laundry service?",
        "Can first year students stay in the hostel?",
        "What are the hostel rules about guests?",
        "How do I apply for a single room in the hostel?",
        "Who is the warden I should contact?",
        "When will the hostel allotment list be out?",
        "Is there a late entry permission for the hostel?",
    ],
    "it_helpdesk": [
        "My laptop cannot connect to the eduroam network",
        "How do I get a new student email account?",
        "The projector login in my classroom is not working",
        "How do I change my portal password?",
        "Where can I print documents using my student account?",
        "The online exam portal will not open for me",
        "I am getting an error when I upload my assignment",
        "How do I enable two step verification on my university account?",
        "I forgot my student portal password",
        "How do I connect to the campus wifi?",
        "The wifi is not working in my hostel",
        "How do I reset my university email password?",
        "I can't log in to the student portal",
        "Who do I contact for IT support?",
        "How do I get access to the computer lab?",
        "My campus email account is locked",
        "How can I install the licensed software provided by the university?",
        "The internet is very slow in the classroom block",
        "How do I set up the campus VPN?",
        "Where is the IT helpdesk located?",
        "How do I register my laptop for the campus network?",
        "The learning management system is not loading for me",
        "How do I raise a ticket with the helpdesk?",
        "I am unable to access my online course materials",
    ],
    "placement_process": [
        "How does the campus placement process work?",
        "When does the placement season start?",
        "Which companies visit the campus for recruitment?",
        "How do I register for placements?",
        "What are the eligibility criteria for campus placements?",
        "Can I sit for placements if I have a backlog?",
        "How do I upload my resume to the placement portal?",
        "Are there mock interviews or training before placements?",
        "How do I apply for an internship through the placement cell?",
        "Who do I contact in the training and placement office?",
        "What is the average package offered last year?",
        "Can I attend more than one company's selection process?",
        "How are students shortlisted for interviews?",
        "I want to know about the pre placement talks",
        "What documents do I need for the placement drive?",
        "Is there a minimum CGPA to be eligible for placement?",
    ],
    "scholarship_aid": [
        "Is there any aid for students who lose a parent?",
        "How do I apply for a freeship from the university?",
        "Which scholarships are open to first year students?",
        "What is the minimum percentage for a merit scholarship?",
        "Can I hold two scholarships at the same time?",
        "Where do I upload my income certificate for aid?",
        "Will my scholarship stop if I fail a subject?",
        "Are there scholarships for girls in engineering?",
        "What scholarships are available for students?",
        "How do I apply for a merit scholarship?",
        "What is the deadline for scholarship applications?",
        "Am I eligible for financial aid?",
        "What documents are needed for a scholarship application?",
        "How do I check my scholarship status?",
        "Is there a scholarship for students from low income families?",
        "How can I get an education loan through the university?",
        "Can I get a fee waiver based on my marks?",
        "Where do I submit the scholarship form?",
        "When will the scholarship amount be credited?",
        "Are there any sports quota scholarships?",
        "Does the university offer need based financial assistance?",
        "How do I renew my scholarship for the next year?",
        "Who handles scholarship queries?",
        "I would like to know about government scholarships",
    ],
    "certificates": [
        "How do I get my transcript?",
        "How can I apply for a bonafide certificate?",
        "How long does it take to get a degree certificate?",
        "I need a character certificate, how do I apply?",
        "How do I request a duplicate marksheet?",
        "Can I get my transcripts sent to another university?",
        "What is the fee for an official transcript?",
        "Where do I collect my provisional certificate?",
        "I need a letter confirming that I am a student here",
        "How do I get a no objection certificate for an internship?",
        "How do I apply for the migration certificate?",
        "Can I get my documents attested on campus?",
        "How do I apply for a transfer certificate?",
        "What is the process to get a medium of instruction letter?",
        "I lost my original degree, can I get a duplicate?",
        "How do I get my id card replaced?",
    ],
    "campus_services": [
        "Is there parking for students on campus?",
        "Where can I keep my bicycle safely?",
        "Does the university have a counselling centre?",
        "Can I talk to a counsellor about stress?",
        "Is there a swimming pool I can use?",
        "Where can I get a photocopy or printout on campus?",
        "What are the opening hours of the medical centre?",
        "How do I book a badminton court?",
        "Is there a cafe near the academic block?",
        "Are there lockers for students?",
        "How do I join the music or drama society?",
        "Where is the student activity centre?",
        "What time does the canteen open?",
        "Where is the campus medical center?",
        "Is there a bus service from the campus to the city?",
        "Where can I find the sports complex timings?",
        "How do I book the auditorium for an event?",
        "Is there an ATM on the campus?",
        "Where is the nearest pharmacy on campus?",
        "What are the gym timings?",
        "Is there a shuttle between the hostel and the academic block?",
        "How do I join a student club?",
        "Where is the campus health clinic and when is it open?",
        "Is there a bookstore or stationery shop on campus?",
        "Where can I park my bicycle or bike?",
        "How do I get a campus bus pass?",
        "What food options are available in the food court?",
        "Does the campus have a counselling service?",
    ],
    "greeting": [
        "Hello",
        "Hi there",
        "Hey VoxSure",
        "Good morning",
        "Good afternoon",
        "Good evening",
        "Hello, anyone there?",
        "Hey, good to see you",
        "Hi, is this the student assistant?",
        "Hey there",
        "Hello, hope you are well",
        "Hiya",
        "Yo, hello",
        "Hi, good to see you",
        "Hey, anyone around?",
        "Namaste",
        "Hi assistant",
        "Hello there",
    ],
    "thanks_bye": [
        "Thank you",
        "Thanks a lot",
        "That was helpful, thanks",
        "Goodbye",
        "Bye bye",
        "See you later",
        "Thanks, that's all I needed",
        "Okay, thank you so much",
        "Great, thanks for the help",
        "Alright, bye",
        "Cheers, that is all",
        "Thank you very much, have a good day",
        "Thanks for your help",
        "Appreciate it, goodbye",
        "That answers my question, thank you",
        "Okay, I'm done, bye",
        "Many thanks",
        "Perfect, thanks, talk to you later",
        "I'm all set, thank you",
        "Bye for now",
        "Thanks, you've been really useful",
        "Good night, and thanks",
        "Take care, goodbye",
        "Got it, thanks",
    ],
    "about_bot": [
        "What is your name?",
        "Who are you?",
        "Hi, what's your name?",
        "Who built you?",
        "Are you a robot?",
        "Are you a real person?",
        "How are you?",
        "How are you doing today?",
        "Tell me about yourself",
        "What should I call you?",
        "Which model are you?",
        "Are you an AI?",
        "Who created this assistant?",
        "What are you?",
    ],
    "help_capabilities": [
        "What can you do?",
        "How can you help me?",
        "What can I ask you?",
        "What topics do you cover?",
        "What can you help me with?",
        "Show me what you can do",
        "What kind of questions can you answer?",
        "List the things you can help with",
        "I need some help",
        "Can you help me?",
        "How do I use this assistant?",
        "What if I ask something you do not know?",
        "If I want something else answered, what will you do?",
        "What are your features?",
        "Which subjects do you support?",
        "Tell me what you can do for students",
    ],
    "out_of_scope": [
        "What is the weather like today?",
        "Tell me a joke",
        "Who won the cricket match yesterday?",
        "What is the price of bitcoin?",
        "How do I cook pasta?",
        "Can you write my essay for me?",
        "What is the capital of France?",
        "Play some music",
        "Book me a flight to Mumbai",
        "What are the latest news headlines?",
        "Who is the president of the United States?",
        "How do I lose weight fast?",
        "Order me a pizza",
        "Translate this sentence into Spanish",
        "What is the meaning of life?",
        "Can you give me a stock tip?",
        "Solve this calculus problem for me",
        "How do I fix my car engine?",
        "What movies are playing this weekend?",
        "Tell me about the history of Rome",
        "What is the best phone to buy?",
        "Give me a recipe for chocolate cake",
        "What is my horoscope today?",
        "How do I get a visa for Canada?",
        "Can you diagnose my headache?",
        "Who is the best football player in the world?",
        "Set an alarm for six in the morning",
        "What is the exchange rate for the dollar?",
        "Write a python program to sort a list",
        "Where can I buy a cheap laptop?",
        "How tall is Mount Everest?",
        "Recommend a good restaurant in town",
        "Explain how black holes work",
        "What is the speed of light?",
        "Can you call my mother?",
        "Sing me a song",
        "Do you know any good vacation spots?",
        "How do I file my income tax return?",
        "Tell me the lyrics of a popular song",
        "What should I name my new puppy?",
    ],
}

# Plausible ASR confusions applied to some variants (word -> replacement).
ASR_SUBS = {
    "library": "libary", "hostel": "hostile", "fees": "feeds", "fee": "free",
    "exam": "example", "exams": "examples", "wifi": "why fi", "semester": "seminar",
    "scholarship": "scholar ship", "scholarships": "scholar ships", "transcript": "transcribe",
    "placement": "placements", "placements": "placement", "renew": "renew you",
    "bonafide": "bona fide", "canteen": "can teen", "hall": "hole", "ticket": "tick it",
    "borrow": "barrow", "books": "box", "deadline": "dead line", "timings": "timing",
    "result": "results", "results": "result", "campus": "camp us", "calendar": "calender",
    "password": "pass word", "portal": "pour tal", "resume": "resume a", "warden": "warding",
    "curfew": "curfew", "convocation": "convocation", "revaluation": "re evaluation",
}
PREFIXES = ["", "", "", "um ", "hey ", "can you tell me ", "i want to know ", "please tell me ",
            "quick question ", "excuse me ", "so ", "hi, ", "okay so "]
SUFFIXES = ["", "", "", " please", " thanks", " right now", " if you know", " today"]


def normalise_asr(text: str) -> str:
    """ASR-style: lower case, no punctuation."""
    return "".join(c for c in text.lower() if c.isalnum() or c.isspace() or c == "'").strip()


def corrupt(text: str, rng: random.Random) -> str:
    words = normalise_asr(text).split()
    out = []
    changed = False
    for w in words:
        if w in ASR_SUBS and rng.random() < 0.6:
            out.append(ASR_SUBS[w]); changed = True
        elif len(words) > 5 and rng.random() < 0.06:
            changed = True  # dropped word
        else:
            out.append(w)
    if not changed and len(words) > 4:  # guarantee some noise: drop one interior word
        out.pop(rng.randrange(1, len(out) - 1))
    return " ".join(out)


def variants(seed: str, rng: random.Random, n: int) -> list[str]:
    base = seed
    res = [base]
    seen = {base.lower()}
    tries = 0
    while len(res) < n and tries < 60:
        tries += 1
        mode = rng.random()
        core = base[0].lower() + base[1:] if len(base) > 1 else base
        if mode < 0.35:
            v = normalise_asr(base)
        elif mode < 0.65:
            v = normalise_asr(rng.choice(PREFIXES) + core.rstrip("?.") + rng.choice(SUFFIXES))
        else:
            v = corrupt(rng.choice(PREFIXES) + core.rstrip("?."), rng)
        v = " ".join(v.split())
        if v and v.lower() not in seen:
            seen.add(v.lower()); res.append(v)
    return res


# Hand-written ambiguous utterances: the *correct behaviour* is to clarify rather than
# answer. `plausible` lists the intents a reasonable reader could mean. Used ONLY for
# evaluation (never for training).
AMBIGUOUS = [
    ("When does it open?", ["library_hours", "campus_services"]),
    ("What time does it close?", ["library_hours", "campus_services"]),
    ("I need help with my form", ["scholarship_aid", "certificates", "fee_payment"]),
    ("Tell me about the dates", ["academic_calendar", "exam_info"]),
    ("When is the deadline?", ["fee_payment", "scholarship_aid", "academic_calendar"]),
    ("How do I apply?", ["scholarship_aid", "hostel_info", "placement_process"]),
    ("What is the fine?", ["library_borrow", "fee_payment"]),
    ("I want to renew", ["library_borrow", "scholarship_aid"]),
    ("Where do I go for that?", ["certificates", "it_helpdesk", "campus_services"]),
    ("Is it free?", ["campus_services", "fee_payment"]),
    ("I have a problem with my account", ["it_helpdesk", "fee_payment"]),
    ("Can I get a receipt?", ["fee_payment", "certificates"]),
    ("How long does it take?", ["certificates", "exam_info"]),
    ("Who do I contact?", ["it_helpdesk", "hostel_info", "placement_process"]),
    ("What are the timings?", ["library_hours", "campus_services", "hostel_info"]),
    ("I lost my card", ["library_borrow", "certificates"]),
    ("Tell me about the results", ["exam_info", "placement_process"]),
    ("Is it allowed?", ["exam_info", "hostel_info"]),
    ("When will it be credited?", ["scholarship_aid", "fee_payment"]),
    ("I need a letter", ["certificates", "placement_process"]),
    ("What documents do I need?", ["placement_process", "scholarship_aid", "certificates"]),
    ("Check my status", ["scholarship_aid", "fee_payment", "exam_info"]),
    ("The portal is not showing it", ["it_helpdesk", "exam_info", "fee_payment"]),
    ("Can I change it?", ["hostel_info", "academic_calendar"]),
    ("What's the last date?", ["academic_calendar", "fee_payment", "scholarship_aid"]),
    ("I want information about registration", ["academic_calendar", "placement_process"]),
    ("Do I need permission?", ["hostel_info", "certificates", "placement_process"]),
    ("Is there a limit?", ["library_borrow", "placement_process"]),
    ("When is the next one?", ["academic_calendar", "exam_info", "placement_process"]),
    ("Tell me more about the process", ["placement_process", "certificates", "hostel_info"]),
    ("Is it open on weekends?", ["library_hours", "campus_services"]),
    ("How much does it cost?", ["fee_payment", "hostel_info", "certificates"]),
    ("I want to apply for it", ["scholarship_aid", "hostel_info", "placement_process"]),
    ("When do I get it back?", ["library_borrow", "exam_info", "certificates"]),
    ("It is not working", ["it_helpdesk", "campus_services"]),
    ("Where is the office?", ["certificates", "fee_payment", "placement_process"]),
    ("Can someone help me with my request?", ["it_helpdesk", "certificates", "fee_payment"]),
    ("Is there any update?", ["exam_info", "scholarship_aid", "hostel_info"]),
    ("Tell me the rules", ["hostel_info", "library_borrow", "exam_info"]),
    ("Do I have to pay for that?", ["fee_payment", "certificates", "campus_services"]),
    ("What is the procedure?", ["certificates", "exam_info", "placement_process"]),
    ("How early should I arrive?", ["exam_info", "placement_process"]),
    ("I missed the date", ["academic_calendar", "fee_payment", "scholarship_aid"]),
    ("Can I extend it?", ["library_borrow", "academic_calendar", "hostel_info"]),
    ("Who is in charge?", ["hostel_info", "placement_process", "it_helpdesk"]),
    ("I need to reset it", ["it_helpdesk", "hostel_info"]),
    ("Is the form available online?", ["scholarship_aid", "certificates", "exam_info"]),
    ("Where can I see the list?", ["hostel_info", "placement_process", "exam_info"]),
    ("When does it start?", ["academic_calendar", "placement_process", "campus_services"]),
    ("What happens if I am late?", ["library_borrow", "fee_payment", "exam_info"]),
]


def main() -> None:
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    groups: list[dict] = []
    gid = 0
    for intent, seeds in SEEDS.items():
        for s in seeds:
            n = 7 if intent not in ("greeting", "thanks_bye") else 5
            if intent == "out_of_scope":
                n = 6
            for v in variants(s, rng, n):
                groups.append({"group": gid, "intent": intent, "text": v, "seed": s})
            gid += 1

    # split by group within each intent: 70/15/15
    by_intent: dict[str, list[int]] = {}
    for g in groups:
        by_intent.setdefault(g["intent"], [])
        if g["group"] not in by_intent[g["intent"]]:
            by_intent[g["intent"]].append(g["group"])
    split_of: dict[int, str] = {}
    for intent, gids in by_intent.items():
        rng.shuffle(gids)
        n = len(gids)
        n_test, n_val = max(2, round(n * 0.15)), max(2, round(n * 0.15))
        for i, g in enumerate(gids):
            split_of[g] = "test" if i < n_test else "val" if i < n_test + n_val else "train"

    splits: dict[str, list[dict]] = {"train": [], "val": [], "test": []}
    for g in groups:
        splits[split_of[g["group"]]].append(
            {"text": g["text"], "intent": g["intent"], "group": g["group"]})
    for name, rows in splits.items():
        rng.shuffle(rows)
        with (OUT / f"{name}.jsonl").open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    amb = list(AMBIGUOUS)
    rng.shuffle(amb)
    half = len(amb) // 2
    for name, rows in (("ambiguous_val", amb[:half]), ("ambiguous_test", amb[half:])):
        with (OUT / f"{name}.jsonl").open("w", encoding="utf-8") as f:
            for text, plausible in rows:
                f.write(json.dumps({"text": text, "plausible": plausible}) + "\n")

    # leakage check: no identical normalised text across splits
    texts = {k: {normalise_asr(r["text"]) for r in v} for k, v in splits.items()}
    overlap = {f"{a}&{b}": len(texts[a] & texts[b])
               for a, b in (("train", "val"), ("train", "test"), ("val", "test"))}
    stats = {"seed": SEED, "n_seed_utterances": gid, "sizes": {k: len(v) for k, v in splits.items()},
             "per_class": {k: dict(Counter(r["intent"] for r in v)) for k, v in splits.items()},
             "exact_overlap_between_splits": overlap, "n_ambiguous_eval": len(AMBIGUOUS)}
    (OUT / "stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps(stats["sizes"]), "overlap:", overlap)


if __name__ == "__main__":
    main()
