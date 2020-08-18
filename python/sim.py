import sys, os, re, itertools
from landscape import Landscape
from population import Population
from plot import plot3d
from tqdm import tqdm
import json, pandas as pd, numpy as np

# Classes for running a simulation with some default global params, and some run-specific or variable params
class GlobalParams():
    """
    General parameters for the run of simulations
    """
    map_size = 50
    timesteps = 400

    # EPISTEMIC PARAMETERS
    desert = 10 #below which value is a patch considered desert (used for initial placement)
    #sigThreshold = 10
    depletion = 0.5

    # HILLS
    hill_number = 2
    hill_width = 3
    #hill_distance = 1 #1 = max poss equal spacing in landscape size

    # NOISE PARAMETERS
    noise = 5
    smoothing = 2
    octaves = 3

    # AGENTS
    agent_number = 40
    velocity = 0.4

    social_threshold = {'alpha': 1, 'beta': 1}
    social_type = 'homogeneous' #values: homogeneous, heterogeneous, proportional
    mavericks = 0.1 # what proportion to make complete mavericks. Only has effect of social_type = proportional
    tolerance = 0 # how much decrease in value they can handle before doing social learning
    resilience = 1 # rate at which their social threshold decreases if they aren't climbing

class Simulation():
    """
    Class for an individual simulation run, combining global parameters with run-specific parameters
    """
    def __init__(self,global_params,run_params,report_type):
        self.params = global_params
        self.report_type = report_type
        self.changed = []
        for param_name in run_params:
            # Keep track of which parameters are specific to this run
            self.changed.append(param_name)
            # And update the parameter object to reflect them
            setattr(self.params, param_name, run_params[param_name])

    def run(self):
        # One run of the simulation, consisting of multiple timesteps during which agents do stuff
        self.report('message', "Python: sim starting...")
        self.data = {}
        self.landscape = Landscape(self.params)
        self.population = Population(self.landscape, self.params)

        for timestep in range(self.params.timesteps):
            self.updateData(timestep)
            self.population.explore()
            self.population.move()
            self.population.findPatches()
            self.population.consume(self.params.depletion)
            self.population.updateHeight()

        self.report('message', "Python: sim done...")

    def updateData(self, timestep):
        # Before each time step, store the current state of the simulation
        self.report("data", json.dumps({'landscape': self.landscape.reportGrid(), 'population': self.population.reportAgents()}))
        step_data = {'timestep': timestep,
            'mass': self.landscape.epistemicMassDiscovered()}
        if self.report_type != 'browser':
            self.data[timestep] = step_data

    def getData(self, sim):
        # Include whatever variables have changed in this specific run in the run's data
        data_out = pd.DataFrame.from_dict(self.data, orient="index")
        data_out['sim'] = sim
        for param_name in self.changed:
            param_value = getattr(self.params, param_name)
            try:
                #If the param is an object, save each as a column
               for key in param_value:
                   data_out["{}_{}".format(param_name,key)] = param_value[key]
            except:
                #Save the value as a column
                data_out[param_name] = param_value
        return(data_out)

    def report(self, data_type, data):
        # This functionality --- as opposed to just printing the output --- is needed to pass data on to the node app
        # Messages are just printed in the terminal window, whereas data is passed on to the node app
        if self.report_type != 'silent':
            if self.report_type == 'browser':
                print(json.dumps({'type': data_type, 'data': data}))
                sys.stdout.flush()
            elif data_type != 'data':
                print(data)

def fileSuffix(report_type):
    # If this is a test run, save data to "data_temp.csv".
    # Otherwise, see how many data files are in directory, and increment to get new ID
    if report_type == 'test':
        return("_temp")
    else:
        max_id = 0
        if os.path.exists("../data/"):
            for file in os.listdir("../data/"):
                files = re.search('data([0-9]+).csv', file)
                if files:
                    file_id = int(files.group(1))
                    if file_id > max_id:
                        max_id = file_id
        return(max_id + 1)

if __name__ == "__main__":
    try:
        report_type = sys.argv[1]
    except:
        report_type = 'silent'
    if report_type == "browser":
        simulation = Simulation(GlobalParams, {}, report_type)
        simulation.run()
    else:
        if report_type == 'test':
            print("Test run...")

        file_id = fileSuffix(report_type)
        data_file = "../data/data{}.csv".format(file_id)
        param_file = "../data/param{}.json".format(file_id)

        sim_parameters = {
         # 'social_threshold': [{'alpha': 2, 'beta': 3}, {'alpha': 20, 'beta': 30}],
         'mavericks': [x/10 for x in range(11)],
         'noise': [2, 6],
         'social_type': ['proportional']
        }
        with open(param_file, "w") as file_out:
            json.dump(sim_parameters, file_out, indent=4)

        keys = sim_parameters.keys()
        values = (sim_parameters[key] for key in keys)
        run_list = [dict(zip(keys, combination)) for combination in itertools.product(*values)]

        R = 100*len(run_list) # get 100 runs per cell
        # R = 1

        for sim in tqdm(range(R)):
            run_parameters = np.random.choice(run_list)
            # run_parameters = {}
            simulation = Simulation(GlobalParams, run_parameters, report_type)
            simulation.run()
            run_data = simulation.getData(sim)
            print_header = sim==0
            run_data.to_csv(data_file, mode="a", header=print_header, index=False)
