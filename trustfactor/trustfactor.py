import math

# temporary, retrieve info from DB to set the vars, use this for testing trust factor
# the vars MUST be these names unless you choose to modify the code, you can just be quick and set it to these names
likes = 0
dislikes = 0
reports = 0
views = 0

def trust_factor(likes, dislikes, reports, views,
                 report_weight = 1.5,  # reports are weighed differently, 1 report = 3 dislikes
                 decay_k = 0.2,        # exponential decay rate for reports
                 virt_view = 200,      # virtual views are given to new guides (ex: to not give 0% trust factor to a guide with 1 view and one dislike)
                 init_score = 0.75,    # initial trust factor is 50%
                 view_penalty= 0.05,   # fraction of non engaging views to dilute the score and make views matter
                 scale_factor= 1.1):   # scale factor because its a lil harsh
    
    """
    the following will be the equation to create trust factor rating
    it will return a value from 0 to 100 and will also check for triggers
    """

    # the weight of the reports decreases as the amount of reports increase
    effective_report_weight = report_weight * math.exp(-decay_k * max(0, reports - 1))

    #net score
    net_score = likes - dislikes - (effective_report_weight * reports)

    # account for the full engagement to be put into the engagement factor
    total_engagement = likes + dislikes + reports

    # reduces view penalty for guides with moderate engagement
    engagement_factor = 1 / (1 + total_engagement)  # more engagement -> less view dilution

    # Denominator
    denominator = virt_view + total_engagement + view_penalty * engagement_factor * max(0, views - total_engagement)

    # Bayesian trust scaling
    trust_score = (virt_view * init_score + net_score) / denominator

    # Apply scale factor
    trust_score *= scale_factor

    # Clamp 0–1, scale to 0–100
    trust_score = max(0.0, min(1.0, trust_score)) * 100

    return round(trust_score, 2)


# wrapper for trust_factor(), this returns a rating score
def scale(likes, dislikes, reports, views):
    score = trust_factor(likes, dislikes, reports, views)

    if score >= 90:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Mixed"
    elif score >= 30:
        return "Poor"
    else:
        return "Very Poor"
    

# scale will give you what it is considered, use a star system
# the actual trust factor function gives the real trust factor from 0 - 100, use if needed, but you should really only need scale
print(trust_factor(likes, dislikes, reports, views))
print(scale(likes, dislikes, reports, views))


    






