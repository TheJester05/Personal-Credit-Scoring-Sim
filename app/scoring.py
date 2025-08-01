WEIGHTS = {
    "payment_history": 0.35,       
    "credit_utilization": 0.30,    
    "length_of_history": 0.15,     
    "credit_mix": 0.10,            
    "inquiries": 0.10              
}

ACTION_EFFECTS = {
    "missed_payment": -50,
    "paid_off_debt": +30,
    "opened_new_loan": -10,
    "closed_old_card": -15,
    "paid_credit_card": +15
}

def normalize_history(years: float) -> float:
    """
    Normalize credit history years to a 0–100 scale.
    For example:
    - 0 years = 0
    - 10+ years = 100
    """
    if years >= 10:
        return 100.0
    return round((years / 10) * 100, 2)

def compute_credit_score(profile: dict, actions: list = None):
    """
    Compute the credit score from a user's financial profile.
    profile: a dict with keys matching WEIGHTS (values should be 0–100)
    actions: optional list of string events that can impact the final score
    """

    total_score = 0
    breakdown = {}

    for factor, weight in WEIGHTS.items():
        raw = profile.get(factor, 0)         
        weighted = raw * weight * 8.5        
        score_piece = int(weighted)
        breakdown[factor] = score_piece
        total_score += score_piece

    total_score = max(300, min(850, total_score))

    if actions:
        for action in actions:
            effect = ACTION_EFFECTS.get(action, 0)
            total_score += effect

        total_score = max(300, min(850, total_score))

    return {
        "total": total_score,
        **breakdown
    }
