# Classes and functions for running a simulation with some default global params, and some run-specific or variable params
# The singleRun() function below is used to run a simulation using these parameters

from landscape import Landscape
from population import Population
import pandas as pd, json, sys

class GlobalParams():
    """
    General parameters for the run of simulations
    """
    map_size = 40
    timesteps = 400

    # EPISTEMIC PARAMETERS
    desert = 2 #below which value is a patch considered desert (used for initial placement)
    sig_threshold = 0 #below which value a patch isn't worth excavating (used for evaluating epistemic work)
    depletion_rate = 0.2

    # HILLS
    hill_number = 2
    hill_width = 3
    #hill_distance = 1 #1 = max poss equal spacing in landscape size

    # NOISE PARAMETERS
    noise = 6
    smoothing = 3
    octaves = 4

    # AGENTS
    agent_number = 40
    velocity = 0.2

    # Examples of setting social learning thresholds:
    # See population.py for a description of what they do
    ## 2 options for distributions:
    social_threshold = {'alpha': 1, 'beta': 9}
    # social_threshold = {'k': 20, 'theta': 20}
    ## 1 option for constant
    # social_threshold = {'slope': 10000000}
    ## 1 option for proportion
    # social_threshold = {'proportion': 0.2, 'conformist_threshold': 0, 'maverick_threshold': 1}

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
        self.reportsteps = detail == 'time'
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
            self.population.move()
            self.population.evaluate()
            self.population.explore()
            self.population.updateNewPatches()

            self.population.consume(self.params.depletion_rate)
            self.population.updateHeight()

            self.updateData(timestep)

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
                # Report agents' outcomes from previous timestep
                self.agent_data = self.population.reportSuccess()

    def getData(self, sim_number, details='time'):
        # Include whatever variables have changed in this specific run in the run's data,
        if details in ['time', 'basic']:
            data_out = pd.DataFrame.from_dict(self.group_data, orient="index").round(2)
        elif details =='agents':
            data_out = pd.DataFrame.from_dict(self.agent_data, orient="index").round(2)
        else:
            raise Exception("details option not recognised (choose from: 'time', 'agents', 'basic')")

        data_out['sim'] = sim_number
        for param_name in self.changed:
            param_value = getattr(self.params, param_name)
            try:
                #If the param is a dict, save each key as a column
               for key in param_value:
                   data_out[key] = param_value[key]
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
    group_data = simulation.getData(i)
    group_data.to_csv(data_file, mode="a", header=False, index=False)
    # If necessary, also provide data on individual agents
    if detail == 'agents':
        agent_data = simulation.getData(i, 'agents')
        agent_data.to_csv(agents_file, mode="a", header=False, index=False)
    return("done")
