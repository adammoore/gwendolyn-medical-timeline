"""
This module contains the Public Health Budget (PHB) details for Gwendolyn Vials Moore.
It provides structured information about her health conditions and needs that can be
linked to medical events in the timeline.
"""

PHB_CATEGORIES = {
    "Respiratory": {
        "description": "Severe, frequent, hard-to-predict apnoea not related to seizures",
        "details": [
            "Central and obstructive sleep apnoea",
            "Ventilation and respiratory arrests",
            "Under specialist respiratory and sleep teams",
            "Requested sleep study due to deterioration"
        ],
        "severity": "SEVERE",
        "keywords": ["apnoea", "apnea", "sleep", "respiratory", "breathing", "ventilation", "oxygen"]
    },
    "Nutrition": {
        "description": "Problems with intake of food and drink",
        "details": [
            "Vomiting and reflux due to gastric issues including GERD",
            "May need tube feeding or thickeners",
            "Prefers drinking through a straw to reduce choking risk",
            "Dietary and behavioral complexities including food obsession and PICA",
            "Obesity requiring specialist input"
        ],
        "severity": "HIGH",
        "keywords": ["food", "drink", "vomit", "reflux", "gastric", "GERD", "tube", "feed", "thickener", "straw", "chok", "diet", "PICA", "obesity"]
    },
    "Mobility": {
        "description": "Mobility impairments",
        "details": [
            "Multiple major orthopaedic surgeries (osteotomy and patella stabilization)",
            "Atypical anatomy (flat bones, partial kneecap, leg length discrepancy)",
            "Lower-limb instability and severe pain",
            "Pending further specialist surgery on both legs",
            "Requires 2:1 assistance for transfers/positioning",
            "Uses bespoke NHS wheelchair",
            "Significant changes between head and neck joints"
        ],
        "severity": "HIGH",
        "keywords": ["mobility", "orthopaedic", "orthopedic", "surgery", "knee", "leg", "bone", "pain", "transfer", "wheelchair", "osteotomy", "patella", "joint"]
    },
    "Continence": {
        "description": "Continence & toileting needs",
        "details": [
            "Cannot wipe or clean independently",
            "Regular accidents",
            "Under care of continence team and urology nurses",
            "Recurrent UTIs",
            "PDA-related avoidance behaviors",
            "Gynae infections",
            "Monthly bleeds since age 7",
            "No capacity to change pads or manage personal hygiene"
        ],
        "severity": "HIGH",
        "keywords": ["continence", "toilet", "wipe", "clean", "accident", "UTI", "urinary", "urology", "gynae", "bleed", "pad", "hygiene"]
    },
    "Skin": {
        "description": "Skin integrity & wound management",
        "details": [
            "Eczema",
            "Allergies to plaster/dressings",
            "Reopens wounds",
            "Slow/failed healing",
            "Requires specialist dressing regimes",
            "Under skin viability and wound care teams",
            "History of removing plaster casts prematurely",
            "Broke four different types of braces (even titanium)"
        ],
        "severity": "HIGH",
        "keywords": ["skin", "eczema", "allergy", "wound", "heal", "dressing", "plaster", "cast", "brace"]
    },
    "Communication": {
        "description": "Communication difficulties",
        "details": [
            "Difficulty communicating emotions and needs",
            "Requires visual or tactile aids",
            "Speech understandable only to familiar adults",
            "Communication deteriorates when anxious, tired, or in unfamiliar surroundings",
            "Needs structured, low-demand approach",
            "Uses sign-based and visual supports"
        ],
        "severity": "MODERATE",
        "keywords": ["communication", "speech", "language", "sign", "visual", "aid", "makaton", "signalong"]
    },
    "Medication": {
        "description": "Drug therapies and medication",
        "details": [
            "Requires daily management by registered nurse",
            "Regular medical practitioner oversight",
            "Unstable gastro conditions",
            "Intense pain from orthopaedic complications",
            "Disrupted/painful nights",
            "Constant monitoring for respiratory status, reflux, and pain"
        ],
        "severity": "SEVERE",
        "keywords": ["medication", "drug", "therapy", "pain", "gastro", "nurse", "monitor"]
    },
    "Psychological": {
        "description": "Psychological & emotional vulnerability",
        "details": [
            "Acute and prolonged emotional dysregulation",
            "Severe anxiety",
            "Poor impulse control",
            "ASD/PDA diagnosis",
            "Down Syndrome"
        ],
        "severity": "HIGH",
        "keywords": ["psychological", "emotional", "anxiety", "impulse", "ASD", "PDA", "autism", "down syndrome", "downs"]
    },
    "Seizures": {
        "description": "Seizure activity",
        "details": [
            "Ongoing concerns about absence seizures",
            "Recorded episodes in clinical settings",
            "Occur several times a day",
            "Does not routinely require rescue medication",
            "Constant supervision essential"
        ],
        "severity": "MODERATE",
        "keywords": ["seizure", "epilepsy", "absence", "episode"]
    },
    "Behavioral": {
        "description": "Behavioral challenges",
        "details": [
            "Intense, severe behaviors threatening safety",
            "Complex combination of DS/ASD/PDA",
            "Frequent high-risk behaviors",
            "Meltdowns in public places",
            "Refusals to move from roads",
            "Impulsive acts endangering herself and others",
            "Requires constant supervision and structured approach"
        ],
        "severity": "SEVERE",
        "keywords": ["behavior", "behaviour", "meltdown", "risk", "impulsive", "supervision", "safety"]
    }
}

PHB_SUPPORTS = {
    "Personal Assistant": {
        "description": "Personal Assistant (PA) for 1:1 or 2:1 Support Outside of School",
        "details": [
            "Constant supervision for safety",
            "2:1 care for toileting, transfers, mobility",
            "Behavioral redirection due to PDA",
            "Trained PA who understands medical conditions, sensory needs, and communication",
            "25 hours/week of outside-of-school support"
        ],
        "keywords": ["assistant", "PA", "support", "supervision", "care"]
    },
    "Hippotherapy": {
        "description": "Therapeutic Horse Riding (Hippotherapy)",
        "details": [
            "Improves core strength, balance, lower-limb stability, and sensory integration",
            "Aids posture and muscle tone management",
            "Reduces injury risk",
            "Educational dimension: learning about animals, routines, communication/social skills",
            "Regular specialist-led sessions"
        ],
        "keywords": ["horse", "riding", "hippotherapy", "therapy", "core", "balance", "posture"]
    },
    "Swimming": {
        "description": "Specialist 1:1 Swimming/Hydrotherapy Sessions",
        "details": [
            "Improves muscle tone, range of motion, and cardio-respiratory health",
            "Limited awareness of danger",
            "Cannot concentrate or behave safely in group lessons",
            "Educational benefits through structured instruction",
            "Twice-weekly 1:1 sessions"
        ],
        "keywords": ["swim", "hydrotherapy", "pool", "water", "muscle", "tone", "float"]
    },
    "Respite": {
        "description": "Respite: Support & Short-Stay Accommodation/Holiday",
        "details": [
            "Continuous supervision needs",
            "Short breaks reduce caregiver burnout",
            "Maintain stable home environment",
            "Claire House has been positive",
            "Success depends on familiar staff and sensory-friendly environment",
            "Short-stay breaks in specialized setting"
        ],
        "keywords": ["respite", "break", "holiday", "accommodation", "claire house", "caregiver", "burnout"]
    },
    "Technology": {
        "description": "Assistive/Interactive Technology (iPad Pro & Apple Pencil)",
        "details": [
            "Visual and hearing impairments",
            "Previously used Makaton/Signalong",
            "Needs large print (18pt+) and accessible apps",
            "iPad Pro with Apple Pencil for specialized communication software",
            "Supports fine motor development and independent learning"
        ],
        "keywords": ["technology", "ipad", "apple", "pencil", "app", "communication", "software", "visual", "hearing"]
    }
}

def get_phb_category_for_event(event_text):
    """
    Determine which PHB category an event belongs to based on keywords.
    Returns a list of matching categories with their severity.
    """
    if not event_text:
        return []
    
    event_text = event_text.lower()
    matches = []
    
    for category, info in PHB_CATEGORIES.items():
        for keyword in info["keywords"]:
            if keyword.lower() in event_text:
                matches.append({
                    "category": category,
                    "severity": info["severity"],
                    "description": info["description"]
                })
                break
    
    return matches

def get_phb_support_for_event(event_text):
    """
    Determine which PHB support an event relates to based on keywords.
    Returns a list of matching supports.
    """
    if not event_text:
        return []
    
    event_text = event_text.lower()
    matches = []
    
    for support, info in PHB_SUPPORTS.items():
        for keyword in info["keywords"]:
            if keyword.lower() in event_text:
                matches.append({
                    "support": support,
                    "description": info["description"]
                })
                break
    
    return matches
