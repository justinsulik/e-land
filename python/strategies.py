import numpy as np

def set_thresholds(params):
    # SET SOCIAL LEARNING THRESHOLDS
    # The social learning thresholds can be set as:
        # distributions (beta, gamma)
        # constants
        # proportions
    # if population is homogeneous, everyone gets the same value (e.g., the mean of the distribution)
    # if population is heterogeneous, everyone gets different values (e.g., random sample from the distribution)

    if params.social_threshold_type == 'homogeneous':
        # As a reminder:
            # mean of beta distribution (a,b) = a/(a+b)
            # mean of gamma distribution (k, theta) = k*theta
            # for more, see https://www.essycode.com/distribution-viewer/
        if 'alpha' in params.social_threshold and 'beta' in params.social_threshold:
            # it's a beta distribution
            return params.social_threshold['alpha']/(params.social_threshold['alpha']+params.social_threshold['beta'])
        elif 'k' in params.social_threshold and 'theta' in params.social_threshold:
            # it's a gamma distribution
            return params.social_threshold['k']*params.social_threshold['theta']
        elif 'slope' in params.social_threshold:
            # constant value, everyone gets the same (there's no heterogeneous version of this)
            return params.social_threshold['slope']
        elif 'proportion' in params.social_threshold:
            # 'proportion' refers to proportion of mavericks (p) vs. conformists (1-p)
            # (see heterogeneous version below).
            # However, for 'homogemeous' version of proportion, obviously cant have these distinct categories
            # so instead, get weighted mean of the given thresholds: p*conformists + (1-p)*mavericks
            return params.social_threshold['proportion']*params.social_threshold['maverick_threshold'] + (1-params.social_threshold['proportion'])*params.social_threshold['conformist_threshold']
        else:
            raise Exception("social_threshold type not recognised")

    elif params.social_threshold_type == 'heterogeneous':
        if 'alpha' in params.social_threshold and 'beta' in params.social_threshold:
            # it's a beta distribution
            return np.random.beta(params.social_threshold['alpha'], params.social_threshold['beta'], params.agent_number)
        elif 'k' in params.social_threshold and 'theta' in params.social_threshold:
            # it's a gamma distribution
            return np.random.gamma(params.social_threshold['k'], params.social_threshold['theta'], params.agent_number)
        elif 'proportion' in params.social_threshold and 'conformist_threshold' in params.social_threshold and 'maverick_threshold' in params.social_threshold:
            # 'proportion' refers to proportion of mavericks (p) vs. conformists (1-p)
            mavericks_count = int(params.agent_number*params.social_threshold['proportion'])
            conformists_count = params.agent_number - mavericks_count
            social_thresholds = conformists_count*[params.social_threshold['conformist_threshold']] + mavericks_count*[params.social_threshold['maverick_threshold']]
            return social_thresholds
        else:
            raise Exception("social_threshold type not recognised")
    else:
        raise Exception("social_type not recognised")

def set_depletion_rate(params):
    if params.depletion_rate_type == 'homogeneous':
        return params.depletion_rate
    else:
        raise Exception("Variable depletion rate not yet implemented!")

def set_velocity(params):
    if params.velocity_type == 'homogeneous':
        return params.velocity
    else:
        raise Exception("Variable velocity not yet implemented!")

def set_anticonformity(params):
    if params.anticonformity_type == 'homogeneous':
        if 'alpha' in params.anticonformity and 'beta' in params.anticonformity:
            # it's a beta distribution
            return params.anticonformity['alpha']/(params.anticonformity['alpha']+params.anticonformity['beta'])
        else:
            raise Exception("Other forms of anticonformity not yet implemented!")
    else:
        if 'alpha' in params.anticonformity and 'beta' in params.anticonformity:
            # it's a beta distribution
            return np.random.beta(params.anticonformity['alpha'], params.anticonformity['beta'], params.agent_number)
        else:
            raise Exception("Other forms of anticonformity not yet implemented!")

def set_resilience(params):
    if params.resilience_type == 'homogeneous':
        if 'alpha' in params.resilience and 'beta' in params.resilience:
            # it's a beta distribution
            return params.resilience['alpha']/(params.resilience['alpha']+params.resilience['beta'])
        else:
            raise Exception("Other forms of resilience not yet implemented!")
    else:
        if 'alpha' in params.resilience and 'beta' in params.resilience:
            # it's a beta distribution
            return np.random.beta(params.resilience['alpha'], params.resilience['beta'], params.agent_number)
        else:
            raise Exception("Other forms of resilience not yet implemented!")

def set_tolerance(params):
    if params.tolerance_type == 'homogeneous':
        return params.tolerance
    else:
        return np.random.binomial(1, params.tolerance, params.agent_number)
