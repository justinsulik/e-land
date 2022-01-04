import sys, os, re, itertools, concurrent.futures
from landscape import Landscape
from population import Population
#from plot import plot3d
from tqdm import tqdm
import json, pandas as pd, numpy as np

# Classes for running a simulation with some default global params, and some run-specific or variable params
class GlobalParams():
    """
    General parameters for the run of simulations
    """
    map_size = 40
    timesteps = 500

    # EPISTEMIC PARAMETERS
    desert = 2 #below which value is a patch considered desert (used for initial placement)
    sig_threshold = 0 #below which value a patch isn't worth excavating (used for evaluating epistemic work)
    depletion = 0.1

    # HILLS
    hill_number = 2
    hill_width = 3
    #hill_distance = 1 #1 = max poss equal spacing in landscape size

    # NOISE PARAMETERS
    noise = 6
    smoothing = 3
    octaves = 4

    # AGENTS
    agent_number = 20
    velocity = 0.2

    # Examples of setting social learning thresholds:
    # 2 options for distributions:
    # social_threshold = {'alpha': 1, 'beta': 9}
    # social_threshold = {'k': 20, 'theta': 20}
    # 1 option for constant
    # social_threshold = {'slope': 10000000}
    # 1 option for proportion
    social_threshold = {'proportion': 0.2, 'conformist_threshold': 0, 'maverick_threshold': 1}

    social_type = 'homogeneous' #values: homogeneous, heterogeneous
    tolerance = 0 # how much decrease in value they can handle before doing social learning. 0 = looks at social info anytime goes downhill
    resilience = 1 # rate at which their social threshold decreases if they aren't climbing. 1 = stays constant (the effect is multiplicative)

class Simulation():
    """
    Class for an individual simulation run, combining global parameters with run-specific parameters
    """
    def __init__(self,global_params,run_params,sim_type,detail):
        self.params = global_params
        self.sim_type = sim_type
        self.changed = []
        # 3 levels of detail in reporting are available
        # all time steps (no agents): 'time'
        # all agents (no time steps): 'agents'
        # neither: 'basic'
        # (all times and all agents seems overkill for now...)
        self.reportsteps = detail == 'all'
        self.reportagents = detail == 'agents'
        for param_name in run_params:
            # Keep track of which parameters are specific to this run
            self.changed.append(param_name)
            # And update the parameter object to reflect them
            setattr(self.params, param_name, run_params[param_name])

    def run(self):
        # One run of the simulation, consisting of multiple timesteps during which agents do stuff
        self.report('message', "Python: sim starting...")
        self.group_data = {}
        self.agent_data = []
        self.landscape = Landscape(self.params)
        self.population = Population(self.landscape, self.params)

        for timestep in range(self.params.timesteps):
            # This is the stuff that gets done at each timestep
            self.updateData(timestep)
            self.population.findPatches()
            self.population.explore()
            self.population.move()
            self.population.updatePatches()
            self.population.consume(self.params.depletion)
            self.population.updateHeight()

        self.report('message', "Python: sim done...")

    def updateData(self, timestep):
        #either 'print' the data for the node app to see or store it for later saving
        if self.sim_type == 'browser':
            self.report("data", json.dumps({'landscape': self.landscape.reportGrid(), 'population': self.population.trackAgents()}))
        else:
            if self.reportsteps or timestep==self.params.timesteps-1:
                # Before each timestep OR just final timestep, store the current state of the simulation
                step_data = {'timestep': timestep,
                    'mass': self.landscape.epistemicMassDiscovered()}
                self.group_data[timestep] = step_data
            if self.reportagents and timestep==self.params.timesteps-1:
                self.agent_data = self.population.reportSuccess()

    def getGroupData(self, sim):
        # Include whatever variables have changed in this specific run in the run's data,
        # focusing on group-level outcomes
        data_out = pd.DataFrame.from_dict(self.group_data, orient="index").round(2)
        data_out['sim'] = sim
        for param_name in self.changed:
            param_value = getattr(self.params, param_name)
            try:
                #If the param is a dict, save each key as a column
               for key in param_value:
                   data_out["{}_{}".format(param_name,key)] = param_value[key]
            except:
                #Save the value as a column
                data_out[param_name] = param_value
        return(data_out)

    def getAgentsData(self, sim):
        # Include various metrics of success/behavior for each agent
        data_out = pd.DataFrame.from_dict(self.agent_data, orient="index").round(2)
        data_out['sim'] = sim
        for param_name in self.changed:
            # not needed because every agent has their own social_threshold
            if param_name != "social_threshold":
                param_value = getattr(self.params, param_name)
                try:
                    #If the param is a dict, save each key as a column
                    for key in param_value:
                        data_out["{}_{}".format(param_name,key)] = param_value[key]
                except:
                    #Save the value as a column
                    data_out[param_name] = param_value
        return(data_out)

    def report(self, data_type, data):
        # This functionality --- as opposed to just printing the output --- is needed to pass data on to the node app
        # Messages are just printed in the terminal window, whereas data is passed on to the node app
        if self.sim_type != 'silent':
            if self.sim_type == 'browser':
                print(json.dumps({'type': data_type, 'data': data}))
                sys.stdout.flush()
            elif data_type != 'data':
                print(data)

def singleRun(inputs):
    glob, loc, i, detail, data_file, agents_file = inputs
    simulation = Simulation(glob, loc, 'silent', detail)
    simulation.run()
    # We'll always need data on the overall/group outcomes
    group_data = simulation.getGroupData(i)
    group_data.to_csv(data_file, mode="a", header=False, index=False)
    # If necessary, also provide data on individual agents
    if detail == 'agents':
        agent_data = simulation.getAgentsData(i)
        agent_data.to_csv(agents_file, mode="a", header=False, index=False)
    return("done")

def fileSuffix(sim_type):
    # If this is a test run, save data to "data_temp.csv".
    # Otherwise, see how many data files are in directory, and increment to get new ID
    if sim_type == 'test':
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

def get_data_headers(sim_parameters):
    headers = 'timestep,mass,sim'
    if len(sim_parameters)==0:
        headers += '\n'
    else:
        headers += ','
        for i, param in enumerate(sim_parameters):
            if param == 'social_threshold':
                if 'alpha' in sim_parameters[param][0]:
                    param_name = 'social_threshold_alpha,social_threshold_beta'
                if 'theta' in sim_parameters[param][0]:
                    param_name = 'social_threshold_k,social_threshold_theta'
                if 'slope' in sim_parameters[param][0]:
                    param_name = 'social_threshold_slope'
            else:
                param_name = param
            if i<len(sim_parameters)-1:
                headers += param_name + ','
            else:
                print('here')
                headers += param_name + '\n'
    return(headers)

def get_agent_headers(sim_parameters, agent_columns_to_get):
    headers = ','.join(agent_columns_to_get)
    if len(sim_parameters)==0 or (len(sim_parameters)==1 and 'social_threshold' in sim_parameters):
        headers += '\n'
    else:
        headers += ','
        for i, param in enumerate(sim_parameters):
            # don't need sim-level social threshold, as agents have their own
            if param != 'social_threshold':
                if i<len(sim_parameters)-1:
                    headers += param + ','
                else:
                    headers += param + '\n'
    return(headers)

if __name__ == "__main__":
    try:
        # when called from the node app, the first arg is 'browser'
        sim_type = sys.argv[1]
    except:
        sim_type = 'silent'
    try:
        # detail = report every time step or just final outcome
        detail = sys.argv[2]
    except:
        detail = 'basic'

    # Set up sim runs depending whether this is called from Node app or command line
    if sim_type == "browser":
        simulation = Simulation(GlobalParams, {}, sim_type, detail)
        simulation.run()
    else:
        if sim_type == 'test':
            print("Test run...")

        # Set up sim runs for various combinations of parameter settings
        sim_parameters = {
        #  https://www.essycode.com/distribution-viewer/
         # 'social_threshold': [{'k': 1.1, 'theta': 0.05},
         #     {'k': 1, 'theta': 0.2},
         #     {'k': 1, 'theta': 0.35},
         #     {'k': 1.1, 'theta': 0.5}],
         # 'social_threshold': [{'alpha': 1, 'beta': 9},
         #    {'alpha': 3, 'beta': 7},
         #    {'alpha': 5, 'beta': 5},
         #    {'alpha': 7, 'beta': 3},
         #    {'alpha': 9, 'beta': 1}],
         'social_threshold' = [{'proportion': 0, 'conformist_threshold': 0, 'maverick_threshold': 1},
         {'proportion': 0.2, 'conformist_threshold': 0, 'maverick_threshold': 1},
         {'proportion': 0.4, 'conformist_threshold': 0, 'maverick_threshold': 1},
         {'proportion': 0.6, 'conformist_threshold': 0, 'maverick_threshold': 1},
         {'proportion': 0.8, 'conformist_threshold': 0, 'maverick_threshold': 1},
         {'proportion': 1, 'conformist_threshold': 0, 'maverick_threshold': 1}]
         # 'social_threshold': [{'slope': 0}, {'slope': 1}, {'slope': 10}, {'slope': 100}],
         #'noise': [1,6,10],
         #'tolerance': [0, 0.2, 0.4],
         #'resilience': [0.95, 0.995, 1.0],
         #'hill_width': [3, 6],
         #'depletion_rate': [0.1, 0.2, 0.3, 0.4],
         'social_type': ['heterogeneous', 'homogeneous']
        }

        # Set up filenames for storing data and sim parameters
        file_id = fileSuffix(sim_type)

        # to store the invariant parameters
        param_file = "../data/param{}.json".format(file_id)
        with open(param_file, "w") as file_out:
            # store all (global and simulation-specific) parameters
            all_params = vars(GlobalParams)
            all_params = {x: all_params[x] for x in all_params if '__' not in x}
            for param in sim_parameters:
                all_params[param] = sim_parameters[param]
            json.dump(all_params, file_out, indent=4)

        # to store group-level data and the params that vary across sims
        data_file = "../data/data{}.csv".format(file_id)
        print('will save to {}'.format(data_file))
        data_file_headers = get_data_headers(sim_parameters)
        with open(data_file, "w") as f:
            f.write(data_file_headers)

        # to store agent-level data and the params that vary across sims
        if detail == 'agents':
            agents_file = "../data/agents{}.csv".format(file_id) if detail == 'agents' else None
            agent_columns_to_get = ['id', 'highest_point', 'social_threshold', 'consumed', 'patches_visited', 'sim']
            agent_file_headers = get_agent_headers(sim_parameters, agent_columns_to_get)
            with open(agents_file, "w") as f:
                f.write(agent_file_headers)
        else:
            agents_file = None

        # Create list of tasks to run in parallel, then execute
        keys = sim_parameters.keys()
        values = (sim_parameters[key] for key in keys)
        run_list = [dict(zip(keys, combination)) for combination in itertools.product(*values)]
        R = 200*len(run_list) # get roughly 200 runs per cell
        # R = 1
        tasks = [(GlobalParams, np.random.choice(run_list), i, detail, data_file, agents_file) for i in range(R)]

        with concurrent.futures.ProcessPoolExecutor() as executor:
            results_ = list(tqdm(executor.map(singleRun, tasks), total=R)) # list() needed for tqdm to work for some reason
