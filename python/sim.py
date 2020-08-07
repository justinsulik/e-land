import sys
from landscape import Landscape
from population import Population
from plot import plot3d
import json, pandas as pd, numpy as np

class SimParams():
    """
    General parameters for the simulation
    """
    map_size = 50
    time_steps = 500

    # EPISTEMIC PARAMETERS
    desert = 10 #below which value is a patch considered desert (used for initial placement)
    #sigThreshold = 0.8 #used for epistemic_progress -- as quantile of mass
    depletion = 0.5

    # HILLS
    hill_number = 2
    hill_width = 2
    #hill_distance = 1 #1 = max poss equal spacing in landscape size

    # NOISE PARAMETERS
    noise = 5
    smoothing = 4
    octaves = 2

    # AGENTS
    agent_number = 40
    # params for beta distribution https://homepage.divms.uiowa.edu/~mbognar/applets/beta.html
    alpha = 1
    beta = 1
    velocity = 0.4
    social_threshold = 0.1


def runsim(params, report_type, save=False):
    report(report_type, 'message', "Python: sim starting...")
    save_data = {}
    landscape = Landscape(params)
    total_epistemic_mass = landscape.epistemicMass()
    population = Population(landscape, params)
    report(report_type, "data", json.dumps({'landscape': landscape.reportGrid(), 'population': population.reportAgents()}))
    for step in range(params.time_steps):
        for i in range(params.agent_number):
            population.explore(i)
        population.move()
        population.consume(params.depletion)
        save_data[len(save_data)] = {'timestep': step, 'mass': 1 - landscape.epistemicMass()/total_epistemic_mass, 'alpha': params.alpha}
        population.updateHeight()
        report(report_type, "data", json.dumps({'landscape': landscape.reportGrid(), 'population': population.reportAgents()}))
    report(report_type, "message", "Python: sim done...")
    if save:
        data_out = pd.DataFrame.from_dict(save_data, orient="index")
        return(data_out)

def report(report_type, data_type, data):
    if report_type != 'silent':
        if report_type == 'browser':
            print(json.dumps({'type': data_type, 'data': data}))
            sys.stdout.flush()
        elif data_type != 'data':
            print(data)

if __name__ == "__main__":
    try:
        report_type = sys.argv[1]
    except:
        report_type = 'silent'
    report(report_type, 'message', 'reporting style: '+report_type)
    if report_type == "browser":
        runsim(SimParams, report_type)
    else:
        data = []
        R = 2000
        #beta_max = 10
        for sim in range(R):
            print(sim)
            social_threshold = np.random.randint(1,11,1)[0]/10
            hill_width = np.random.choice([3, 10])
            noise = np.random.choice([1, 5])
            # alpha = np.random.randint(1,beta_max,1)[0]
            # beta = beta_max - alpha
            SimParams.social_threshold = social_threshold
            SimParams.hill_width = hill_width
            SimParams.noise = noise
            # SimParams.alpha = alpha
            # SimParams.beta = alpha
            sim_data = runsim(SimParams, report_type, True)

            # Store sim parameters
            sim_data['sim'] = sim
            sim_data['social_threshold'] = social_threshold
            sim_data['hill_width'] = hill_width
            sim_data['noise'] = noise
            data.append(sim_data)
        data = pd.concat(data)
        data.to_csv("../data/data3.csv")
            #runsim(SimParams, report_type, True)



# print("Python: script done...")
# print(json.dumps({"message": "Python: script done..."}))
