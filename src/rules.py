"""Keyword rules: the free, deterministic fallback for the classification step.

Used (1) by the scheduled job when no API key is configured, and (2) as an
independent second opinion — where rules and AI labels disagree, the review goes
to the human review queue.

Careful with commute jargon: in this app "login"/"logout" usually mean the
to-office and from-office *trips*, so "logout cab was late" is not a sign-in issue.
"""
import re

FLAGS = re.I

# Stage code -> pattern. Order = priority when more than three match.
STAGE_RULES = [
    ("J1.session", r"log(s|ged|ging)?\s*(me\s*)?(out|off)\s*(automatically|every|frequent|again|by itself|daily|after|often|when)"
                   r"|keeps?\s+log(ging)?\s*(me\s*)?(out|off)|logged\s*(me\s*)?out|auto(matically)?\s*log(s|ged)?\s*(me\s*)?(out|off)"
                   r"|sign(s|ed)?\s*(me\s*)?out\s*(every|automatic|daily)|(login|log in|otp)\s*(every|each)\s*time|every\s*time.{0,25}(login|log in|otp)"
                   r"|session expired|validate (my )?identity|stay (logged|signed) in|keep (us|me) (logged|signed) in|re-?login|log ?in again"),
    ("J1.otp", r"\botp\b.{0,40}(not|never|n't|late|delay|expire|after \d+)|(no|not|never|didn'?t|n'?t)\s+(get|getting|receiv\w*|sent|send\w*|com\w*|generat\w*)\s+(the\s+|any\s+)?otp"
               r"|otp (is |are )?(not|never)|no otps?\b|verification code|(getting|generat\w*|receiv\w*|deliver\w*)\s.{0,12}otp"
               r"|otp.{0,20}(issue|problem|taking|took)|verifying my (no|number|mobile|email)"),
    ("J1.other", r"(can'?t|cannot|unable to|not able to|couldn'?t)\s+(log ?in|sign ?in|login|register|sign up|verify)|login (issue|problem|error)"
                 r"|not registered|user not (present|in system)|subscription|no (option to )?register"),
    ("J3.window", r"cut ?-?off|(hours?|hrs?|days?)\s+(before|prior|in advance|advance)|in advance|same day|wait ?-?list|cancellation period|out of (hiring|service) zone"),
    ("J3.fail", r"(unable|can'?t|cannot|not able|couldn'?t)\s+(to\s+)?(book|schedule|roster)|book(ing)?\s+(failed|fails|error|not (going|saved|happening))"
                r"|book now.{0,20}disabled|bookings?\s+(disappear|vanish|not show|not reflect)|no (schedules?|trips?) (are )?available|book(ing)?.{0,20}(difficult|failed|error|issue|problem)"),
    ("J3.modify", r"(cancel|edit|modify|reschedule|amend)\w*\s.{0,25}(booking|trip|schedule|ride|roster)|change\s+(my\s+|the\s+)?(address|location|pick ?up|drop|destination)"
                  r"|(address|location) (change|update)"),
    ("J3.steps", r"(too many|number of|\d+)\s+(steps|clicks|taps|selections)|2 step|two step|bulk book|date range|am/?pm"),
    ("J4.route", r"rout(e|es|ing)\b|club(bing|bed)?\b|pool(ing)?\b|detour|nodal|longest|sequence"),
    ("J4.time", r"too early|early pick|pick ?up time.{0,25}(early|chang|var|wrong|differ)|\b(\d|two|three)\s*(\.\d)?\s*(hours?|hrs)\b.{0,20}(reach|daily|in (the )?cab|travel)"),
    ("J4.alloc", r"(not|never)\s+(been\s+)?(assigned|allocated|allotted)|(cab|vehicle)\s+(allocation|allotment|assign)|no cabs?\b|cabs? (not|never) available|insufficient cabs"),
    ("J5.noise", r"(too many|lot of|lots of|unnecessary|annoying|unwanted|so many|constant|excessive)\s+(push\s+)?(notifications?|alerts?|pop ?-?ups?)|keeps? (on )?(sending|giving) notifications"),
    ("J5.missing", r"(no|not getting|didn'?t get|missing|late|delayed|wrong)\s+(push\s+)?(notifications?|alerts?|sms|messages?)\b|notifications?.{0,15}(not|late|delay|never)"
                   r"|cab (number|details) (is |are )?(not|missing)|pick ?up time (is )?not|(not|never) (getting|receiving|showing)\s+(the\s+)?(pick ?up time|cab details|vehicle details|cab number|car number)|doesn'?t show (the )?(pick ?up|cab|exact time|time)"),
    ("J6", r"track(ing|er)?\b|\bgps\b|\beta\b|live location|real ?-?time|\bmaps?\b|zoom|location (is |was )?(wrong|incorrect|inaccurate|not (updat|correct|accurate|show))"),
    ("J7.noshow", r"no[ -]?show|\bncns\b"),
    ("J7.board", r"\bqr\b|\bscan|check ?-?in|check ?-?out|seat ?belt|guard otp|boarding"),
    ("J7.contact", r"(call|contact|reach|message|chat)\w*\s.{0,15}driver|driver.{0,25}(not reachable|unreachable|doesn'?t (pick|answer)|not (pick|answer))"
                   r"|calling (option|feature|issue|facility)|chat (option|box|feature)|call (option|button)"),
    ("J7.late", r"(cab|bus|shuttle|driver|vehicle)s?\s+(is\s+|are\s+|was\s+|were\s+)?(always\s+|never\s+|often\s+|regularly\s+)?(late|delayed|not on time|never (came|comes)|didn'?t (come|arrive))"
                r"|(don'?t|doesn'?t|won'?t|didn'?t)\s+(even\s+)?wait|never on time|late by"),
    ("J8.driver", r"drivers?.{0,40}(rude|behav|unprofessional|rash|speed|abusive|shout|misbehav|harsh|aggressive)|rash driving|over ?-?speed"),
    ("J8.vehicle", r"\bac\b|vehicle condition|dirty|seater|clean(liness)?\b"),
    ("J8.drop", r"door drop|drop(ped)?\s+(point|location|far|late|before|in the middle)|drop (is |was )?(always )?(late|delay)"),
    ("J9", r"help ?desk|helpline|customer (care|service|support)|\bsupport\b|complain|escalat|transport team|sahayta|\bivr\b|feedback"),
    ("X2.interrupt", r"(terms|policy|policies|agreement|i agree|disclaimer|t ?& ?c).{0,40}(every|again|each|multiple|repeated|twice)|(every|each) time.{0,40}(terms|policy|agreement|disclaimer)"
                     r"|pop ?-?ups?|banner|(forc\w*|mandator\w*|compulsor\w*|always|keeps?|every)\s.{0,25}(rate|rating|review|feedback)|skip\s+(the\s+)?(rating|feedback|review)|permission"),
    ("X1.crash", r"crash|(not|won'?t|doesn'?t|unable to|can'?t)\s+(even\s+)?open|hang(s|ing)?\b|freez|blank (screen|page)|\bstuck\b|not working|doesn'?t work|\bbugs?\b|buggy|glitch"
                 r"|\berror\b|not (installed|downloaded) from|rooted|reinstall|no (internet|network)|wi-?fi|mobile data"),
    ("X1.slow", r"\bslow|\blag|takes? (too much|a lot of|long|forever|ages)|load(ing)? (time|forever|slow)|keeps? (on )?loading|battery|latency"),
    ("X2.design", r"\bui\b|\bux\b|interface|user ?-?friendly|confusing|design|dark (mode|theme)|font|not intuitive|navigation (inside|is not)"),
    ("X3", r"\bdesk\b|meeting room|parking|floor map"),
]
STAGE_RULES = [(code, re.compile(p, FLAGS)) for code, p in STAGE_RULES]

PRAISE = re.compile(r"\b(good|nice|great|excellent|awesome|amazing|super|best|helpful|useful|convenient|easy|smooth|love|reliable|user friendly|thank)", FLAGS)
NEGATIVE = re.compile(r"\b(worst|wrost|worse|bad|poor|pathetic|useless|waste|horrible|terrible|irritat|annoy|frustrat|disappoint|rubbish|trash|bekar|bekaar|bakwas|"
                      r"not|never|no|can'?t|cannot|unable|doesn'?t|don'?t|won'?t|fail|issue|problem)\b", FLAGS)
# Risk words only — "safe" on its own is usually praise ("super safe").
SAFETY = re.compile(r"unsafe|not safe|no safety|safety (concern|issue|risk)|harass|misbehav|\bsos\b|rash|drunk|over ?-?speed|speeding|"
                    r"escort|threat|abusive|dangerous|(women|female|girl|ladies)\W{0,3}\w*\W{0,3}(safety|security|alone|night)", FLAGS)

APP_FAMILIES = {"J1", "J5", "J6", "X1", "X2", "X3"}
OPS_FAMILIES = {"J4", "J8"}


def family(code):
    return code.split(".")[0]


def classify(text, stars):
    """Return a label dict in the same shape the AI labeller produces."""
    t = " ".join(str(text).split())
    stages = [code for code, rx in STAGE_RULES if rx.search(t)]
    neg = bool(NEGATIVE.search(t))
    pos = bool(PRAISE.search(t))
    if not stages:
        stages = ["P"] if pos and not neg else ["U"]
    sentiment = "mixed" if (pos and neg and len(t) > 40) else "neg" if neg else "pos" if pos else "neu"
    fams = {family(s) for s in stages} - {"P", "U"}
    kinds = set()
    for s in stages:
        f = family(s)
        if s == "J3.window":
            kinds.add("policy")
        elif f in APP_FAMILIES or s in {"J3.fail", "J3.steps", "J3.modify", "J3.other", "J7.board", "J7.contact"}:
            kinds.add("app")
        elif f in OPS_FAMILIES or s in {"J7.late", "J7.noshow", "J9"}:
            kinds.add("ops")
    attribution = "none" if not fams else (kinds.pop() if len(kinds) == 1 else "mixed")
    return {"stages": "|".join(stages[:3]), "attribution": attribution,
            "text_sentiment": sentiment, "safety_flag": bool(SAFETY.search(t)) and (stars <= 3 or neg),
            "detail": "", "labeller": "rules-v1"}


def primary_family(stages):
    return family(str(stages).split("|")[0])


def families(stages):
    return {family(s) for s in str(stages).split("|") if s}
