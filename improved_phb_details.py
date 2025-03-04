"""
This module contains the enhanced Public Health Budget (PHB) details for Gwendolyn Vials Moore.
It provides structured information about her health conditions and needs that can be
linked to medical events in the timeline, with improved keyword matching and categorization.
"""

# Define more comprehensive keywords for better matching
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
        "keywords": ["apnoea", "apnea", "sleep", "respiratory", "breathing", "ventilation", "oxygen", 
                    "airway", "breath", "lung", "pulmonary", "chest", "inhale", "exhale", "suffocate",
                    "choke", "arrest", "cyanosis", "blue", "saturation", "sats", "desaturation", "cpap",
                    "bipap", "sleep study", "polysomnography", "snore", "obstruction", "central", "hypoxia"]
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
        "keywords": ["food", "drink", "vomit", "reflux", "gastric", "GERD", "tube", "feed", "thickener", 
                    "straw", "chok", "diet", "PICA", "obesity", "weight", "nutrition", "eat", "swallow", 
                    "dysphagia", "aspiration", "calorie", "meal", "appetite", "hungry", "thirst", "digest",
                    "stomach", "intestine", "bowel", "gastro", "nausea", "regurgitate", "gag", "chew"]
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
        "keywords": ["mobility", "orthopaedic", "orthopedic", "surgery", "knee", "leg", "bone", "pain", 
                    "transfer", "wheelchair", "osteotomy", "patella", "joint", "walk", "stand", "sit", 
                    "move", "limp", "gait", "posture", "balance", "stability", "unstable", "fall", "trip",
                    "dislocation", "subluxation", "fracture", "break", "sprain", "strain", "physio", 
                    "physiotherapy", "physical therapy", "rehab", "rehabilitation", "crutch", "walker",
                    "frame", "mobility aid", "transfer", "lift", "carry", "position", "reposition"]
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
        "keywords": ["continence", "toilet", "wipe", "clean", "accident", "UTI", "urinary", "urology", 
                    "gynae", "bleed", "pad", "hygiene", "wet", "soil", "diaper", "nappy", "catheter", 
                    "bladder", "kidney", "renal", "infection", "bacteria", "menstrual", "period", "sanitary",
                    "incontinence", "leak", "dribble", "frequency", "urgency", "retention", "constipation",
                    "diarrhea", "bowel", "stool", "feces", "urine", "pee", "poo"]
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
        "keywords": ["skin", "eczema", "allergy", "wound", "heal", "dressing", "plaster", "cast", "brace", 
                    "sore", "ulcer", "pressure", "rash", "irritation", "itch", "scratch", "dermatitis", 
                    "dermatology", "bandage", "gauze", "tape", "adhesive", "suture", "stitch", "staple",
                    "incision", "cut", "abrasion", "laceration", "scar", "tissue", "viability", "integrity",
                    "barrier", "protection", "moisture", "dry", "crack", "blister", "callus"]
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
        "keywords": ["communication", "speech", "language", "sign", "visual", "aid", "makaton", "signalong", 
                    "talk", "speak", "verbal", "nonverbal", "express", "understand", "comprehend", "interpret",
                    "gesture", "point", "picture", "symbol", "pecs", "board", "device", "app", "vocabulary",
                    "word", "sentence", "phrase", "articulation", "pronunciation", "stutter", "stammer",
                    "fluency", "clarity", "salt", "speech therapy", "speech and language"]
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
        "keywords": ["medication", "drug", "therapy", "pain", "gastro", "nurse", "monitor", "dose", "tablet", 
                    "pill", "capsule", "liquid", "injection", "infusion", "prescription", "prescribe", 
                    "administer", "dispense", "pharmacy", "pharmacist", "side effect", "reaction", "allergy",
                    "contraindication", "interaction", "therapeutic", "treatment", "regime", "schedule",
                    "compliance", "adherence", "titration", "wean", "increase", "decrease", "adjust"]
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
        "keywords": ["psychological", "emotional", "anxiety", "impulse", "ASD", "PDA", "autism", "down syndrome", 
                    "downs", "mental health", "behavior", "behaviour", "mood", "affect", "regulation", 
                    "dysregulation", "control", "impulsive", "compulsive", "obsessive", "rigid", "routine",
                    "transition", "change", "stress", "distress", "upset", "calm", "agitated", "frustrated",
                    "angry", "sad", "happy", "emotion", "feeling", "sensory", "overstimulation", "meltdown",
                    "shutdown", "overwhelm", "demand", "avoidance", "pathological", "resistance"]
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
        "keywords": ["seizure", "epilepsy", "absence", "episode", "fit", "convulsion", "spasm", "jerk", 
                    "twitch", "shake", "tremor", "vacant", "stare", "unresponsive", "unconscious", "aware",
                    "aura", "postictal", "ictal", "tonic", "clonic", "tonic-clonic", "grand mal", "petit mal",
                    "focal", "generalized", "status", "eeg", "electroencephalogram", "anticonvulsant",
                    "antiepileptic", "rescue", "emergency", "diazepam", "midazolam", "buccal"]
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
        "keywords": ["behavior", "behaviour", "meltdown", "risk", "impulsive", "supervision", "safety", 
                    "danger", "hazard", "threat", "harm", "injury", "accident", "incident", "challenge",
                    "difficult", "problematic", "disruptive", "aggressive", "violent", "destructive",
                    "self-harm", "self-injurious", "hit", "kick", "bite", "scratch", "throw", "break",
                    "run", "elope", "wander", "escape", "hide", "refuse", "resist", "comply", "cooperate",
                    "transition", "change", "routine", "structure", "boundary", "limit", "rule"]
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
        "keywords": ["assistant", "PA", "support", "supervision", "care", "carer", "caregiver", "aide", 
                    "helper", "staff", "worker", "professional", "specialist", "trained", "qualified",
                    "experienced", "knowledgeable", "familiar", "consistent", "regular", "reliable",
                    "trustworthy", "responsible", "attentive", "vigilant", "observant", "responsive"]
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
        "keywords": ["horse", "riding", "hippotherapy", "therapy", "core", "balance", "posture", "equine", 
                    "equestrian", "mount", "dismount", "saddle", "bridle", "reins", "stable", "barn",
                    "arena", "paddock", "field", "trot", "walk", "canter", "gait", "rhythm", "movement",
                    "sensory", "integration", "proprioception", "vestibular", "coordination", "strength",
                    "muscle", "tone", "stability", "control", "confidence", "independence", "achievement"]
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
        "keywords": ["swim", "hydrotherapy", "pool", "water", "muscle", "tone", "float", "aquatic", "aqua", 
                    "bath", "shower", "splash", "wet", "buoyancy", "resistance", "pressure", "temperature",
                    "warm", "hot", "cold", "therapy", "exercise", "movement", "range", "motion", "flexibility",
                    "stretch", "strengthen", "relax", "calm", "soothe", "comfort", "enjoy", "fun", "pleasure",
                    "recreation", "leisure", "activity", "skill", "technique", "stroke", "kick", "arm", "leg"]
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
        "keywords": ["respite", "break", "holiday", "accommodation", "claire house", "caregiver", "burnout", 
                    "rest", "relief", "support", "help", "assist", "aid", "service", "provision", "facility",
                    "center", "centre", "hospice", "home", "house", "residence", "stay", "visit", "overnight",
                    "weekend", "week", "day", "hour", "short", "brief", "temporary", "occasional", "regular",
                    "planned", "emergency", "crisis", "stress", "strain", "pressure", "demand", "need"]
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
        "keywords": ["technology", "ipad", "apple", "pencil", "app", "communication", "software", "visual", 
                    "hearing", "tablet", "device", "screen", "touch", "digital", "electronic", "computer",
                    "laptop", "desktop", "mobile", "portable", "handheld", "wireless", "bluetooth", "wifi",
                    "internet", "online", "download", "upload", "install", "update", "program", "application",
                    "game", "play", "learn", "education", "skill", "development", "progress", "achievement"]
    }
}

# Define personnel types for better categorization
PERSONNEL_TYPES = {
    "Doctor": ["dr", "doctor", "consultant", "physician", "surgeon", "specialist", "registrar", "fellow", "attending"],
    "Nurse": ["nurse", "sister", "matron", "rn", "lpn", "cn", "nursing", "staff nurse"],
    "Therapist": ["therapist", "physiotherapist", "physio", "occupational therapist", "ot", "speech therapist", 
                 "speech and language therapist", "salt", "slp", "psychologist", "counselor", "counsellor"],
    "Specialist": ["specialist", "technician", "technologist", "audiologist", "optometrist", "optician", 
                  "dietitian", "nutritionist", "pharmacist", "social worker", "case manager", "coordinator"],
    "Support": ["assistant", "aide", "helper", "support worker", "care worker", "carer", "pa", "personal assistant"]
}

# Define hospital/facility types for better categorization
FACILITY_TYPES = {
    "Hospital": ["hospital", "medical center", "medical centre", "infirmary", "clinic", "health center", 
                "health centre", "healthcare facility", "nhs trust", "foundation trust"],
    "Specialty Center": ["children's hospital", "pediatric hospital", "paediatric hospital", "specialty hospital", 
                        "specialist hospital", "rehabilitation center", "rehabilitation centre", "rehab"],
    "Therapy Center": ["therapy center", "therapy centre", "rehabilitation center", "rehabilitation centre", 
                      "physical therapy", "occupational therapy", "speech therapy", "behavioral therapy", 
                      "behavioural therapy", "mental health center", "mental health centre"],
    "Community": ["community center", "community centre", "day center", "day centre", "respite center", 
                 "respite centre", "hospice", "nursing home", "care home", "group home", "residential facility"],
    "School": ["school", "special school", "educational facility", "learning center", "learning centre", 
              "academy", "college", "university", "institute"]
}

def determine_specialty(text, title=""):
    """
    Determine medical specialty based on comprehensive analysis of text content.
    Returns the specialty and a confidence score.
    """
    if not text:
        return {"specialty": "Unknown", "confidence": 0}
    
    combined_text = (text + " " + title).lower()
    
    # Define medical specialties and keywords for classification
    SPECIALTIES = {
        'Neurology': ['neuro', 'brain', 'seizure', 'epilepsy', 'neurologist', 'eeg', 'mri brain'],
        'Cardiology': ['heart', 'cardiac', 'cardio', 'cardiologist', 'ecg', 'echo'],
        'Pulmonology': ['lung', 'pulmonary', 'respiratory', 'breathing', 'pulmonologist', 'apnea', 'apnoea', 'sleep study', 'ventilation', 'oxygen'],
        'Gastroenterology': ['stomach', 'intestine', 'gastro', 'gi', 'gastroenterologist', 'reflux', 'gerd', 'feeding', 'tube', 'peg'],
        'Orthopedics': ['bone', 'joint', 'fracture', 'ortho', 'orthopedist', 'orthopedic', 'orthopaedic', 'knee', 'leg', 'hip', 'osteotomy', 'patella'],
        'Endocrinology': ['hormone', 'thyroid', 'diabetes', 'endocrine', 'endocrinologist', 'growth', 'obesity'],
        'Ophthalmology': ['eye', 'vision', 'ophthalmologist', 'glasses', 'sight'],
        'ENT': ['ear', 'nose', 'throat', 'ent', 'hearing', 'audiology'],
        'Dermatology': ['skin', 'rash', 'dermatologist', 'eczema', 'allergy'],
        'Hematology': ['blood', 'anemia', 'hematologist'],
        'Oncology': ['cancer', 'tumor', 'oncologist'],
        'Nephrology': ['kidney', 'renal', 'nephrologist', 'urinary', 'urology', 'bladder'],
        'Urology': ['bladder', 'urinary', 'urologist', 'catheter', 'continence'],
        'Rheumatology': ['arthritis', 'rheumatoid', 'rheumatologist', 'joint pain'],
        'Immunology': ['immune', 'allergy', 'immunologist', 'allergic'],
        'Psychiatry': ['mental', 'psychiatric', 'psychiatrist', 'behavior', 'behaviour', 'asd', 'autism', 'pda'],
        'Pediatrics': ['pediatric', 'pediatrician', 'child', 'children', 'paediatric', 'paediatrician'],
        'General': ['doctor', 'physician', 'gp', 'general practitioner', 'check-up', 'checkup', 'appointment'],
        'Therapy': ['therapy', 'therapist', 'physiotherapy', 'physio', 'occupational therapy', 'ot', 'speech', 'language'],
        'Surgery': ['surgery', 'surgical', 'operation', 'procedure', 'pre-op', 'post-op']
    }
    
    # Count keyword matches for each specialty
    specialty_scores = {}
    for specialty, keywords in SPECIALTIES.items():
        match_count = 0
        for keyword in keywords:
            if keyword in combined_text:
                match_count += 1
        
        if match_count > 0:
            # Calculate confidence score based on matches and keyword density
            confidence = min(100, (match_count / len(keywords)) * 100 * 2)
            specialty_scores[specialty] = confidence
    
    if specialty_scores:
        # Return the specialty with the highest confidence
        best_specialty = max(specialty_scores.items(), key=lambda x: x[1])
        return {"specialty": best_specialty[0], "confidence": round(best_specialty[1], 1)}
    
    return {"specialty": "Unknown", "confidence": 0}

def get_phb_category_for_event(event_text):
    """
    Determine which PHB category an event belongs to based on keywords.
    Returns a list of matching categories with their severity and confidence score.
    """
    if not event_text:
        return []
    
    event_text = event_text.lower()
    matches = []
    
    for category, info in PHB_CATEGORIES.items():
        # Count how many keywords match
        match_count = 0
        matched_keywords = []
        
        for keyword in info["keywords"]:
            if keyword.lower() in event_text:
                match_count += 1
                matched_keywords.append(keyword)
        
        # If we have matches, calculate a confidence score
        if match_count > 0:
            # Calculate confidence score (0-100) based on number of matches and keyword density
            confidence = min(100, (match_count / len(info["keywords"])) * 100 * 2)
            
            matches.append({
                "category": category,
                "severity": info["severity"],
                "description": info["description"],
                "confidence": round(confidence, 1),
                "matched_keywords": matched_keywords
            })
    
    # Sort by confidence score (highest first)
    matches.sort(key=lambda x: x["confidence"], reverse=True)
    
    return matches

def get_phb_support_for_event(event_text):
    """
    Determine which PHB support an event relates to based on keywords.
    Returns a list of matching supports with confidence score.
    """
    if not event_text:
        return []
    
    event_text = event_text.lower()
    matches = []
    
    for support, info in PHB_SUPPORTS.items():
        # Count how many keywords match
        match_count = 0
        matched_keywords = []
        
        for keyword in info["keywords"]:
            if keyword.lower() in event_text:
                match_count += 1
                matched_keywords.append(keyword)
        
        # If we have matches, calculate a confidence score
        if match_count > 0:
            # Calculate confidence score (0-100) based on number of matches and keyword density
            confidence = min(100, (match_count / len(info["keywords"])) * 100 * 2)
            
            matches.append({
                "support": support,
                "description": info["description"],
                "confidence": round(confidence, 1),
                "matched_keywords": matched_keywords
            })
    
    # Sort by confidence score (highest first)
    matches.sort(key=lambda x: x["confidence"], reverse=True)
    
    return matches

def categorize_personnel(name, title=""):
    """
    Categorize personnel based on their name and title.
    Returns the personnel type and specialty if available.
    """
    if not name:
        return {"type": "Unknown", "specialty": "Unknown"}
    
    combined_text = (name + " " + title).lower()
    
    # Determine personnel type
    personnel_type = "Unknown"
    for type_name, keywords in PERSONNEL_TYPES.items():
        for keyword in keywords:
            if keyword in combined_text:
                personnel_type = type_name
                break
        if personnel_type != "Unknown":
            break
    
    # Determine specialty
    specialty = "Unknown"
    for category, info in PHB_CATEGORIES.items():
        for keyword in info["keywords"]:
            if keyword in combined_text:
                specialty = category
                break
        if specialty != "Unknown":
            break
    
    return {"type": personnel_type, "specialty": specialty}

def categorize_facility(facility_name):
    """
    Categorize a facility based on its name.
    Returns the facility type and specialty if available.
    """
    if not facility_name:
        return {"type": "Unknown", "specialty": "Unknown"}
    
    facility_name = facility_name.lower()
    
    # Determine facility type
    facility_type = "Unknown"
    for type_name, keywords in FACILITY_TYPES.items():
        for keyword in keywords:
            if keyword in facility_name:
                facility_type = type_name
                break
        if facility_type != "Unknown":
            break
    
    # Determine specialty
    specialty = "Unknown"
    for category, info in PHB_CATEGORIES.items():
        for keyword in info["keywords"]:
            if keyword in facility_name:
                specialty = category
                break
        if specialty != "Unknown":
            break
    
    return {"type": facility_type, "specialty": specialty}

def get_severity_color(severity):
    """
    Get a color code for a severity level.
    """
    if severity == "SEVERE":
        return "rgba(255, 0, 0, 0.7)"  # Red
    elif severity == "HIGH":
        return "rgba(255, 165, 0, 0.7)"  # Orange
    elif severity == "MODERATE":
        return "rgba(255, 255, 0, 0.7)"  # Yellow
    else:
        return "rgba(128, 128, 128, 0.7)"  # Gray
