import sys
from landscape import Landscape
from population import Population
from plot import plot3d
import json, pandas as pd

class SimParams():
    """
    General parameters for the simulation
    """
    map_size = 50
    time_steps = 10

    # EPISTEMIC PARAMETERS
    desert = 20 #below which value is a patch considered desert (used for initial placement)
    sigThreshold = 100 #used for eProg*
    depletion = 0.5 #todo

    # HILLS
    hill_number = 2
    hill_width = 3
    hill_distance = 1 #1 = max poss equal spacing in landscape size
    max1sig = 1000 #todo
    max2sig = 800 #todo

    #todo: auto space hils

    # NOISE PARAMETERS
    noise = 6
    smoothing = 4
    octaves = 2

    # AGENTS
    agent_number = 60
    # params for beta distribution https://homepage.divms.uiowa.edu/~mbognar/applets/beta.html
    alpha = 1
    beta = 1
    velocity = 0.4
    social_threshold = 10


def runsim(params, report_type):
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
        save_data[step] = {'mass': 1 - landscape.epistemicMass()/total_epistemic_mass, 'social': params.social_threshold}
        population.updateHeight()
        report(report_type, "data", json.dumps({'landscape': landscape.reportGrid(), 'population': population.reportAgents()}))
    #plot3d(landscape)
    report(report_type, "message", "Python: sim done...")
    if report_type == 'terminal':
        data_out = pd.DataFrame.from_dict(save_data, orient="index")
        print(data_out)

def report(report_type, data_type, data):
    if report_type == 'browser':
        print(json.dumps({'type': data_type, 'data': data}))
        sys.stdout.flush()
    elif data_type != 'data':
        print(data)

if __name__ == "__main__":
    try:
        report_type = sys.argv[1]
    except:
        report_type = 'terminal'
    report(report_type, 'message', 'reporting style: '+report_type)
    runsim(SimParams, report_type)

# print("Python: script done...")
# print(json.dumps({"message": "Python: script done..."}))
