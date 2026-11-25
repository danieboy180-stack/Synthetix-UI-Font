"""V6 registered thresholds and constants: the single source of truth for every build gate.

Mirrored in STACKRA-SANS/V6_CONTRACT.md.  Rule (plan 98/100 item 8): a threshold is never relaxed after a failed
result.  A change needs a dated entry in DECISIONS.md and applies only to the NEXT pre-registered run.
Values marked CARRIED come from the V5 PROCEDURE_REVIEW registration; values marked V6-NEW were registered when the
V6 gate was introduced, before that gate had produced a result.
"""

# --- weights / masters -------------------------------------------------------------------------------------------
PUBLIC_WEIGHTS = (300, 400, 500)             # CARRIED: only weights that passed the V5 validity gates
MASTER_WEIGHTS = (300, 350, 400, 450, 500)   # V6: VF masters.  350/450 are intermediate masters added because the dense
                                             # gate (items 54-55) failed with 3 masters; thresholds were NOT relaxed
EXPERIMENTAL_WEIGHTS = (600, 700)            # never shipped; kept only to document why they fail
WEIGHT_NAMES = {300: 'Light', 400: 'Regular', 500: 'Medium', 600: 'SemiBold', 700: 'Bold'}
AXIS_DEFAULT = 400
DENSE_AXIS_STEP = 25                         # V6-NEW (plan item 55): sample every 25 wght units

# --- outline fit / interpolation ---------------------------------------------------------------------------------
FIT_ERR_MAX_UNITS = 1.5                      # CARRIED
INTERP_AREA_MAX = 0.02                       # CARRIED: <= 2 % signed-area deviation at intermediates
INTERP_BBOX_MAX_UNITS = 2.0                  # CARRIED
INTERP_ADVANCE_MAX_UNITS = 2.0               # V6-NEW; registered 1.0, corrected to 2.0 (DECISIONS D-0007): below the integer-rounding noise bound
MASTER_PARITY_BBOX_MAX_UNITS = 1.0           # V6-NEW: VF at a master location vs direct static
MASTER_PARITY_AREA_MAX = 0.005               # V6-NEW

# --- contour correctness (plan item 27) -------------------------------------------------------------------------
MIN_CONTOUR_AREA = 150                       # CARRIED from boolop.finalize
MAX_ABS_Y_UNITS = 1000                       # V6-NEW: sanity bound on any outline coordinate
ADVANCE_RANGE = (80, 1300)                   # V6-NEW: sanity bound for non-space advances
CONTOUR_CORRESPONDENCE_MAX_SHIFT = 160       # V6-NEW: matched contours may not move more than this between masters
CONTOUR_CORRESPONDENCE_AREA_RATIO = (0.2, 5.0)
MISSING_EXTREMA_TOLERANCE = 1.0              # control-box vs true bounds, font units

# --- confusables @14px (CARRIED registered maxima) ---------------------------------------------------------------
CONFUSABLE_MAX_14PX = {'Il': 0.60, 'l1': 0.30, 'O0': 0.45, 'rnm': 0.40, 'cld': 0.45}

# --- boolean engine independent validation (plan item 26) ------------------------------------------------------
BOOL_MISMATCH_MAX_FRACTION = 0.05            # V6-NEW placeholder, calibrated in DECISIONS.md D-0006 before gating

# --- metrics (plan item 61) -------------------------------------------------------------------------------------
VMETRICS = dict(ascender=950, descender=-250, line_gap=0,       # hhea == OS/2 typo, USE_TYPO_METRICS set
                typo_ascender=950, typo_descender=-250, typo_line_gap=0,
                win_ascent=1000, win_descent=280)                # must cover every glyph of every public weight

# --- file-size budgets, bytes, registered BEFORE measuring (plan items 76, 79) -----------------------------------
BUDGET_VF_TTF_BYTES = 60_000                 # V6-NEW
BUDGET_VF_WOFF2_BYTES = 30_000               # V6-NEW
BUDGET_STATIC_WOFF2_BYTES = 14_000           # V6-NEW

# --- versioning ---------------------------------------------------------------------------------------------------
FONT_VERSION_MAJOR, FONT_VERSION_MINOR = 0, 6
VERSION_STRING = 'Version 0.600'
UNIQUE_ID_SUFFIX = '0.6.0-dev'               # 'dev' stays until every hard gate in V6_CONTRACT.md is closed
FAMILY = 'Stackra Sans'                      # WORKING NAME: legally uncleared (BLOCKER 3 / 96 / 97)
PS_FAMILY = 'StackraSans'
PROTO_STRINGS = ('Proto', 'EXPERIMENTAL', 'placeholder', 'TODO')
