import sys
from landscape import Landscape
from population import Population
from plot import plot3d
import json

class SimParams():
    """
    General parameters for the simulation
    """
    map_size = 50
    runs = 100

    # EPISTEMIC PARAMETERS
    desert = 20 #below which value is a patch considered desert (used for initial placement)
    sigThreshold = 100 #used for eProg*
    depletion = 1 #todo

    # HILLS
    hill_number = 2
    hill_width = 3
    hill_distance = 1 #1 = max poss equal spacing in landscape size
    max1sig = 1000 #todo
    max2sig = 800 #todo

    #todo: auto space hils

    # NOISE PARAMETERS
    noise = 4
    smoothing = 4

    # AGENTS
    agent_number = 10
    # params for beta distribution https://homepage.divms.uiowa.edu/~mbognar/applets/beta.html
    alpha = 1
    beta = 1
    velocity = 0.8


def runSim(params, report_type):
    report(report_type, 'message', "Python: sim starting...")
    landscape = Landscape(params)
    population = Population(landscape, params)
    report(report_type, "data", json.dumps({'landscape': landscape.reportGrid(), 'population': population.reportAgents()}))
    for i in range(params.runs):
        for i in range(params.agent_number):
            population.explore(i)
        report(report_type, "data", json.dumps({'landscape': landscape.reportGrid(), 'population': population.reportAgents()}))
    #plot3d(landscape)
    report(report_type, "message", "Python: sim done...")

def report(report_type, type, data):
    if report_type == 'browser':
        print(json.dumps({'type': type, 'data': data}))
        sys.stdout.flush()
    elif type != 'data':
        print(data)

if __name__ == "__main__":
    try:
        report_type = sys.argv[1]
    except:
        report_type = 'terminal'
    report(report_type, 'message', 'reporting style: '+report_type)
    runSim(SimParams, report_type)

# print("Python: script done...")
# print(json.dumps({"message": "Python: script done..."}))
