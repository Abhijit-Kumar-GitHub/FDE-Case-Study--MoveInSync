"""Keyword rules: the free, deterministic fallback for the classification step.

Used (1) by the scheduled job when no API key is configured, and (2) as an
independent second opinion — where rules and AI labels disagree, the review goes
to the human review queue.

Designed for precision over recall: a theme fires only when its words appear
together with a complaint, and a 4-5 star review with no complaint cue is praise.
Anything the rules cannot place confidently is left as U, which sends it to a person.

Careful with commute jargon: in this app "login"/"logout" usually mean the
to-office and from-office *trips*, so "logout cab was late" is not a sign-in issue.
"""
import re

FLAGS = re.I

# Words that turn a mention into a complaint, used inside several theme patterns.
BAD = (r"(not|n't|never|no|wrong|incorrect|inaccurate|stuck|slow|lag\w*|late|delay\w*|jump\w*|old|ago|stale|"
       r"useless|poor|bad|worst|weak|unreliable|fail\w*|error|missing|disappear\w*|pathetic|terrible|horrible|"
       r"issue|problem|keeps? (changing|increasing|jumping)|frozen|freez\w*)")

# Stage code -> pattern. Order = priority when more than three match.
STAGE_RULES = [
    # "logout" written as one word is usually the evening trip, so sign-outs need "log out"/"logged out"/"logs out".
    ("J1.session", r"\blog(s|ged|ging)?\s+(me\s+)?(out|off)\s*(automatically|every|frequent|again|by itself|daily|after|often|when)"
                   r"|logouts? (automatically|frequently|every \d+)|logout frequently|logouting"
                   r"|keeps?\s+log(ging)?\s*(me\s*)?(out|off)\b(?! trip| cab)|logged\s*(me\s*)?out|auto(matically)?\s*log(s|ged)?\s*(me\s*)?(out|off)\b(?! trip| cab)"
                   r"|sign(s|ed)?\s*(me\s*)?out\s*(every|automatic|daily)|(login|log in|otp)\s*(every|each)\s*time|every\s*time.{0,25}(login|log in|otp)"
                   r"|session expired|validate (my )?identity|stay (logged|signed) in|keep (us|me) (logged|signed) in|re-?login|log ?in again|too many otps?|so many otps?|this much otp"),
    ("J1.otp", r"\botp\b.{0,40}(not|never|n't|late|delay|expire|after \d+)|(no|not|never|didn'?t|n'?t)\s+(get|getting|receiv\w*|sent|send\w*|com\w*|generat\w*)\s+(the\s+|any\s+)?otp"
               r"|otp (is |are )?(not|never)|no otps?\b|verification code|(getting|generat\w*|receiv\w*|deliver\w*)\s.{0,12}otp"
               r"|otp.{0,20}(issue|problem|taking|took)|verifying my (no|number|mobile|email)|(unable to|can'?t|cannot|not able to)\s+(get|receive)\s+(the\s+|any\s+)?otp"
               r"|verif\w* via (number|phone|mobile|email)|takes? \w+ to verify"),
    ("J1.address", r"change\s+(my\s+|the\s+)?(home\s+)?(address|pick ?up (point|location)|nodal|drop location)|(address|pin|home location)\s+(change|update|not|is wrong|wrong)"
                   r"|wrong address|nodal point selection|pin ?code|address.{0,30}(old|previous|different|not (taken|accepted|updated|synced|matching))|update (my |the )?(address|location)|location (is )?(not )?suggest|address search|search (for )?(the )?(address|location)"),
    ("J1.other", r"(can'?t|cannot|unable to|not able to|couldn'?t)\s+(log ?in|sign ?in|login|register|sign up|verify)|login (issue|problem|error)"
                 r"|not registered|user not (present|in system)|subscription|no (option to )?register|authentication"),
    ("J3.window", r"cut ?-?off|(hours?|hrs?|days?)\s+(before|prior)|(can'?t|cannot|unable to|not able to|doesn'?t allow\w*|won'?t (let|allow)\w*|no option to)\s+(\w+\s+){0,3}(book|cancel|schedule)\b.{0,40}(advance|before|within|after|same day|week|period|hours?)"
                  r"|same day|wait ?-?list|cancellation period|out of (hiring|service) zone|(\d+|two|three|four|eight|twelve|48|24)\s*(hours?|hrs|days?)\s+(before|prior|in advance|advance)"),
    ("J3.fail", r"(unable|can'?t|cannot|not able|couldn'?t)\s+(to\s+)?(book|schedule|roster)|book(ing)?\s+(failed|fails|error|not (going|saved|happening))"
                r"|book now.{0,20}disabled|bookings?\s+(disappear|vanish|not show|not reflect)|no (schedules?|trips?) (are )?available|book(ing)?.{0,20}(difficult|failed|error|problem)"),
    ("J3.modify", r"(cancel|edit|modify|reschedule|amend)\w*\s.{0,25}(booking|trip|schedule|ride|roster)(?!.{0,20}no ?show)|change\s+(the\s+)?(destination|timing)"),
    ("J3.steps", r"(\d+|too many|number of)\s+(steps|clicks|taps|selections).{0,40}(book|schedul|roster|request|pickup)|(book|schedul)\w*.{0,40}(\d+|too many|number of)\s+(steps|clicks|taps)"
                 r"|2 step|two step|bulk book|date range|am/?pm"),
    ("J4.route", r"(wrong|long|longer|longest|bad|worst|poor|incorrect|unusual|nonsensical|illogical|random|stupid|terrible|weird)\s+(\w+\s+)?(rout(e|es|ing)|clubbing|pooling)"
                 r"|rout(e|es|ing)\s+(\w+\s+){0,3}(is |are |was )?(bad|worst|poor|wrong|pathetic|pethic|terrible|long|not good|very bad|messy|mess)"
                 r"|club(bing|bed).{0,40}(bad|worst|poor|different|wrong|far|not)|(bad|worst|poor|very bad) club|detour|"
                 r"nodal points?.{0,40}(far|removed|walk|km)|\d+\s*(km|kilometers?).{0,20}walk|route (planning|creator|algorithm)|routing (team|algorithm|engine|system)"),
    ("J4.time", r"too early|early pick|pick ?up time.{0,25}(early|chang|var|wrong|differ)|\b(\d|two|three)\s*(\.\d)?\s*(hours?|hrs)\b.{0,20}(reach|daily|in (the )?cab|travel)"),
    ("J4.alloc", r"(not|never)\s+(been\s+)?(assigned|allocated|allotted)|(cab|vehicle)\s+(allocation|allotment|assign)\w*.{0,20}(late|delay|not|bad|poor|worst)|no cabs?\b|cabs? (not|never) available|insufficient cabs|not assigning"),
    ("J5.noise", r"(too many|lot of|lots of|unnecessary|annoying|unwanted|so many|constant|excessive)\s+(push\s+)?(notifications?|alerts?|pop ?-?ups?)|keeps? (on )?(sending|giving) notifications|notifications?.{0,40}pop ?-?ups?|pop ?-?ups?.{0,40}notifications?"),
    ("J5.missing", r"(no|not getting|didn'?t get|missing|late|delayed|wrong)\s+(push\s+)?(notifications?|alerts?|sms|messages?)\b|notifications?.{0,15}(not|late|delay|never)"
                   r"|cab (number|details) (is |are )?(not|missing)|pick ?up time (is )?not|(not|never) (getting|receiving|showing)\s+(the\s+)?(pick ?up time|cab details|vehicle details|cab number|car number)|doesn'?t show (the )?(pick ?up|cab|exact time|time)"),
    ("J6", rf"\b(track(ing|er)?|gps|eta|live location|location|map|real ?-?time|position)\b\W+(\w+\W+){{0,6}}?{BAD}"
           rf"|{BAD}\W+(\w+\W+){{0,3}}?\b(track(ing|er)?|gps|eta|location|map|mapping|navigation|real ?-?time)\b"
           r"|(can'?t|cannot|unable to|not able to|won'?t let)\W+(\w+\W+){0,3}(see|track|view)\b.{0,40}(cab|vehicle|driver|bus|shuttle|van|location|co-?passeng|cab ?mates|colleagues|who)"
           r"|\bzoom|improve (the )?(map|tracking|gps|navigation)|who (all )?(is |are )?(clubbed|travell?ing)|co-?passengers?|cab ?mates|fellow (travell?ers|passengers|colleagues|cab ?mates)|co-?employees|sequence number"
           r"|arrival (time )?(shows|changes|jumps)|(cab|vehicle|bus) (location|timing|position)s?\b.{0,30}(not|n't|wrong|incorrect)|how long the (vehicle|cab) is"),
    ("J7.noshow", r"no[ -]?show|\bncns\b"),
    ("J7.board", r"\bqr\b|\bscan|check ?-?in|check ?-?out|seat ?belt|guard otp|boarding"),
    ("J7.contact", r"(unable|can'?t|cannot|not able) to (contact|call|reach) (the )?(driver|employees?|passengers?)|(call|contact|reach|message|chat)\w*\s.{0,15}driver|driver.{0,25}(not reachable|unreachable|doesn'?t (pick|answer)|not (pick|answer))"
                   r"|calling (option|feature|issue|facility)|chat (option|box|feature)|call (option|button)"),
    ("J7.late", r"(cab|bus|shuttle|driver|vehicle)s?\s+(is\s+|are\s+|was\s+|were\s+)?(always\s+|never\s+|often\s+|regularly\s+)?(late|delayed|not on time|never (came|comes)|didn'?t (come|arrive))"
                r"|(don'?t|doesn'?t|won'?t|didn'?t)\s+(even\s+)?wait|never on time|late by"),
    ("J8.driver", r"drivers?.{0,40}(rude|unprofessional|rash|speeding|abusive|shout|misbehav|harsh|aggressive|don'?t know how to (behave|talk)|behave (badly|rudely)|thie|not (helpful|professional))"
                  r"|rash driving|over ?-?speed|speeding|(rude|unprofessional|abusive|bad|worst|poor|untrained) driv(er|ers|ing)"),
    ("J8.vehicle", r"\bac\b.{0,20}(not|n't|no|off)|vehicle condition|dirty|(\d|four|five) (people|persons?|passengers?) in (a )?\w*.?seater|uncomfortable"),
    ("J8.drop", r"door drop|dropped (me )?(far|before|at the wrong|in the middle)|drop (is |was )?(always )?(late|delay\w*)|late drops?|drop cab (is )?(always )?late"),
    ("J9", r"\b(no|poor|bad|worst|useless|zero|unhelpful|rude|pathetic|waste|third class)\W+(\w+\W+){0,2}(customer )?(support|help ?desk|helpline|customer (care|service)|transport team|staff)\b"
           r"|\b(help ?desk|helpline|customer (care|service)|transport (help )?team|support team)\W+(\w+\W+){0,6}?(not|never|no|n't|rude|useless|busy|unreachable|disconnect\w*|cut|hang\w*|ignor\w*|doesn'?t|blame)"
           r"|(can'?t|cannot|unable to|not able to|not avle to)\s+(connect|reach|contact)\s+(with\s+)?(the\s+)?(help ?desk|support|customer care|transport)"
           r"|complain\w*.{0,40}(ignor|no response|not|never)|escalat|\bivr\b|sahayta|no (option|way) (to )?(give |provide )?feedback|no feedback (option|link)|feedback (box|text box)"
           r"|feedback.{0,30}(ignored|no response|not|never)|can'?t (rate|report)|no one (is )?(helping|responding|picking)|not helpful at all|irresponsible staff"),
    ("X2.interrupt", r"(terms|policy|policies|agreement|i agree|disclaimer|t ?& ?c).{0,40}(every|again|each|multiple|repeated|twice)|(every|each) time.{0,40}(terms|policy|agreement|disclaimer)"
                     r"|(annoying|unnecessary|too many|lot of|full ?-?screen|keeps?|every time|can'?t close|won'?t close|difficult to close|remove (your|the|these))\W+(\w+\W+){0,3}pop ?-?ups?(?!.{0,40}notif)"
                     r"|pop ?-?ups?.{0,30}(every time|again and again|annoying|can'?t (be )?close|won'?t close|keep (coming|showing)|on (every )?(launch|open))|banner"
                     r"|(forc\w*|mandator\w*|compulsor\w*|always|keeps?|every)\s.{0,25}(rat(e|ing)|review|feedback)\b|skip\s+(the\s+)?(rating|feedback|review)"
                     r"|(asks?|asking|forc\w*|nag\w*|every time|too (many|much)|mandatory|compulsory|why|annoy\w*).{0,40}permission|permission.{0,30}(every time|again|mandatory|forc|always)"
                     r"|forc\w+ .{0,25}(notification|permission)|play ?store reviews?|rating system|only (given )?options? like|seat ?belt"),
    ("X1.crash", r"crash|(not|won'?t|doesn'?t|unable to|can'?t|couldn'?t)\s+(even\s+)?(be\s+)?open\b|not (working and )?opening|hang(s|ing)?\b|freez|blank (screen|page)"
                 r"|close[sd]?\s+(itself|automatically|by itself|immediately|in a sec)|not (been )?(installed|downloaded) (from|thru|through|in)|showing not installed|rooted|re-?install"
                 r"|stopped working|not responding|outage|server (is )?down|\b404\b|android \d+|compatib|huawei"
                 r"|(pixel|oneplus|one plus|vivo|samsung|realme|redmi|oppo)\b.{0,40}(not|n't|crash|issue|open|work)|buggy|full of bugs|too many bugs|lots? of (bugs|glitches)"),
    ("X1.slow", r"(app|application|loading|load|opening)\W+(\w+\W+){0,3}?slow|\bslow (app|application|to (load|open))|^\W*slow\b|lag(s|gy|ging)\b"
                r"|takes? (too much|a lot of|long|forever|ages)( time)? to (load|open)|load(ing)? (time|forever|slow)|keeps? (on )?loading|battery|latency|optimi[sz]ation"),
    ("X2.design", r"not (very )?user ?-?friendly|un ?-?friendly|user ?-?unfriendly|(\bui\b|\bux\b|interface|design|layout|navigation)\W+(\w+\W+){0,3}?(bad|poor|worst|horrible|terrible|pathetic|confusing|complicated|difficult|not (good|simple|easy|intuitive)|worse|ghastly|cartoonish)"
                  r"|(bad|poor|worst|horrible|terrible|pathetic|confusing|complicated|simplify the|improve (the )?|easier) (\bui\b|\bux\b|interface|design)|new (\bui\b|update|design|interface|version).{0,40}(bad|worse|worst|confusing|difficult|hard|ghastly|not)"
                  r"|old (version|app|ui).{0,20}(better|back)|bring (back the old|the old)|dark (mode|theme)|font|too many (screens|taps|clicks)|hard to (find|use|navigate)|not intuitive|unintuitive|confusing(?!.{0,45}(book|roster|schedul))|tutorial|error messages?.{0,30}(confus|truncat|can'?t read|unclear)|can'?t read the error"),
    ("X3", r"\bdesk\b|meeting room|parking|floor map"),
]
STAGE_RULES = [(code, re.compile(p, FLAGS)) for code, p in STAGE_RULES]

# Generic phrases ("app not working", "very slow") count only when nothing more specific
# matched — the same way a careful labeller treats them.
FALLBACK_RULES = [
    ("X1.crash", r"(app|application|it)\s+(is\s+)?(not working|doesn'?t work|isn'?t working|keeps? (crashing|stopping))|not working|doesn'?t work|never works"
                 r"|no (internet|network)|wi-?fi|mobile data|something went wrong|glitch|\bbugs?\b|\bstuck\b|app issue|technical (issue|error)|\berror\b"),
    ("X1.slow", r"\bslow\b|delay in (the )?app|takes? (too much|a lot of|long|forever|ages)"),
]
FALLBACK_RULES = [(code, re.compile(p, FLAGS)) for code, p in FALLBACK_RULES]
OTHER_INTERRUPT = re.compile(r"terms|polic|agree|disclaimer|banner|permission|seat ?belt|rat(e|ing)|review|feedback|forc", FLAGS)
LIVE_WORDS = re.compile(r"track|gps|\beta\b|cab|vehicle|driver|\bbus\b|shuttle|zoom|real ?-?time", FLAGS)
TRIP_OTP = re.compile(r"guard|boarding|trip otp|otp.{0,30}(driver|cab|trip|ride)|(driver|cab|trip|ride).{0,30}otp|sign-?in and sign-?out|tracking page", FLAGS)
LOGIN_WORDS = re.compile(r"\blog ?in\b(?! trip| cab)|register|verif|sign ?in to|access the app", FLAGS)

PRAISE = re.compile(r"\b(good|nice|great|excellent|awesome|amazing|super|best|helpful|useful|convenient|easy|smooth|love|reliable|user friendly|thank)", FLAGS)
NEGATIVE = re.compile(r"\b(worst|wrost|worse|bad|poor|pathetic|useless|waste|horrible|terrible|irritat|annoy|frustrat|disappoint|rubbish|trash|bekar|bekaar|bakwas|"
                      r"not|never|no|can'?t|cannot|unable|doesn'?t|don'?t|won'?t|fail|issue|problem)\b", FLAGS)
# A 4-5 star review needs one of these before any problem theme is assigned.
COMPLAINT_CUE = re.compile(r"\b(but|however|except|improve\w*|should|need|needs|wish|please|bring back|missing|not|never|issue|issues|problem|problems|"
                           r"bug|bugs|lag\w*|slow|wrong|worst|bad|poor|pathetic|useless|unable|cannot|fail\w*|error|stuck|delay\w*|late|annoying|irritating|"
                           r"frustrating|hard|difficult|confusing|forced|forcing)\b|n't\b", FLAGS)
# Risk words only — "safe" on its own is usually praise ("super safe").
SAFETY = re.compile(r"unsafe|not safe|no safety|safety (concern|issue|risk)|harass|misbehav|\bsos\b|\brash(ly)?\b|\bdrunk|over ?-?speed|speeding|"
                    r"escort|threat|abusive|dangerous|(women|female|girl|ladies)\W{0,3}\w*\W{0,3}(safety|security|alone|night)", FLAGS)

APP_FAMILIES = {"J1", "J5", "J6", "X1", "X2", "X3"}
OPS_FAMILIES = {"J4", "J8"}


def family(code):
    return code.split(".")[0]


def classify(text, stars):
    """Return a label dict in the same shape the AI labeller produces."""
    t = " ".join(str(text).split())
    neg = bool(NEGATIVE.search(t))
    pos = bool(PRAISE.search(t))
    if stars >= 4 and not COMPLAINT_CUE.search(t):
        stages = []  # praise or neutral: no problem theme
    else:
        stages = [code for code, rx in STAGE_RULES if rx.search(t)]
        if not stages:
            stages = [code for code, rx in FALLBACK_RULES if rx.search(t)]
        # Notification pop-ups are noise, not a launch interruption, unless something else interrupts too.
        if "J5.noise" in stages and "X2.interrupt" in stages and not OTHER_INTERRUPT.search(t):
            stages.remove("X2.interrupt")
        # "Location"/"map" in an address complaint is about the saved address, not live tracking.
        if "J1.address" in stages and "J6" in stages and not LIVE_WORDS.search(t):
            stages.remove("J6")
        # The OTP shown to the driver/guard at pickup is boarding, not login.
        if "J1.otp" in stages and TRIP_OTP.search(t) and not LOGIN_WORDS.search(t):
            stages = [("J7.board" if s == "J1.otp" else s) for s in stages]
            stages = list(dict.fromkeys(stages))
    if not stages:
        stages = ["P"] if pos and not (neg and stars <= 3) else ["U"]
    sentiment = "mixed" if (pos and neg and len(t) > 40) else "neg" if neg else "pos" if pos else "neu"
    fams = {family(s) for s in stages} - {"P", "U"}
    kinds = set()
    for s in stages:
        f = family(s)
        if s == "J3.window":
            kinds.add("policy")
        elif s in ("J4.route", "J4.time"):
            kinds.update(("app", "ops"))  # routing engine (MoveInSync software) + ops/client configuration
        elif f in APP_FAMILIES or s in {"J3.fail", "J3.steps", "J3.modify", "J3.other", "J7.board", "J7.contact"}:
            kinds.add("app")
        elif f in OPS_FAMILIES or s in {"J7.late", "J7.noshow", "J9"}:
            kinds.add("ops")
    attribution = "none" if not fams else (kinds.pop() if len(kinds) == 1 else "mixed")
    return {"stages": "|".join(stages[:3]), "attribution": attribution,
            "text_sentiment": sentiment, "safety_flag": bool(SAFETY.search(t)) and (stars <= 3 or neg),
            "detail": "", "labeller": "rules-v2"}


def primary_family(stages):
    return family(str(stages).split("|")[0])


def families(stages):
    return {family(s) for s in str(stages).split("|") if s}
