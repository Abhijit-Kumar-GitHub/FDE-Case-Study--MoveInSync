"""Central configuration: which apps to track and how far back to look."""

COUNTRY = "in"
LANG = "en"

# Primary subject of the analysis: the employee app (effectively "the" MoveInSync rating).
PRIMARY_APP = "com.moveinsync.ets"

# role: employee | driver | competitor
# history: how many days of reviews to pull (None = everything available)
APPS = {
    "com.moveinsync.ets": {"name": "MoveInSync", "role": "employee", "history": None},
    "com.moveinsync.publictransit": {"name": "TransitInSync", "role": "employee", "history": None},
    "com.moveinsync.driver.dco": {"name": "MoveInSync Driver Partner", "role": "driver", "history": None},
    "com.moveinsync.driver.lite": {"name": "Moveinsync Partner Lite", "role": "driver", "history": None},
    "in.mtap.iincube.safetrax.commuter": {"name": "Safetrax Commuter", "role": "competitor", "history": 730},
    "com.routematic.employee": {"name": "Routematic", "role": "competitor", "history": 730},
    "in.iincube.commuter": {"name": "Safetrax (older app)", "role": "competitor", "history": 730},
    "com.agiledge.myatom": {"name": "NeOffice Commute", "role": "competitor", "history": 730},
    "in.smarttransport.emp": {"name": "SMT Employee", "role": "competitor", "history": 730},
    "com.app.newt.employee": {"name": "eFmFm Employee", "role": "competitor", "history": 730},
    "com.proficio.commute": {"name": "COMMUTE (Proficio)", "role": "competitor", "history": 730},
}

# Extra pulls for the primary app.
MOST_RELEVANT_COUNT = 40      # what a visitor sees first on the listing
HINDI_SAMPLE_COUNT = 2000     # to measure how much we miss by analysing English only

# Analysis knobs.
LABEL_WINDOW_DAYS = 365       # AI-label everything <=3 stars (and longer 4-5 star reviews) in this window
MIN_VERSION_N = 30            # minimum reviews before a version's numbers are shown
DAILY_RIDERS = 1_500_000      # from the case study (all platforms) — assumption A3

# Production classifier (simulated tonight; see src/classify_api.py).
API_MODEL = "claude-sonnet-5-5"
API_BUDGET_USD = 2.00         # abort a run whose estimated cost exceeds this
