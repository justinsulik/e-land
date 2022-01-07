import sys, os, re, itertools, concurrent.futures, json, random
from simulation import Simulation, GlobalParams, singleRun
import files
from tqdm import tqdm

if __name__ == "__main__":
    try:
        # when called from the node app, the first arg is 'browser'
        sim_type = sys.argv[1]
    except:
        sim_type = 'test'
    try:
        # 3 levels of detail in reporting are available
        # 'time': all time steps (no agents):
        # 'agents': all agents (no time steps)
        # 'basic': just group-level info at end of run (report neither timesteps nor individual agents)
        # (both all times & all agents seems overkill for now...)
        detail = sys.argv[2]
    except:
        detail = 'basic'

    # Set up sim runs depending whether this is called from Node app or with python3 at command line
    if sim_type == "browser":
        simulation = Simulation(GlobalParams, {}, sim_type, detail)
        simulation.run()
    else:
        if sim_type == 'test':
            print("Test run...")
            print("Data will overwrite temp files...")

        # Set up sim runs for various combinations of parameter settings
        sim_parameters = {
         # 'social_threshold': [{'k': 1.1, 'theta': 0.05},
         #     {'k': 1, 'theta': 0.2},
         #     {'k': 1, 'theta': 0.35},
         #     {'k': 1.1, 'theta': 0.5}],
         'social_threshold': [
            {'alpha': 1, 'beta': 9},
            {'alpha': 3, 'beta': 7},
            {'alpha': 5, 'beta': 5},
            {'alpha': 7, 'beta': 3},
            {'alpha': 9, 'beta': 1},
            ],
         # 'social_threshold': [
         # {'proportion': 0.2, 'conformist_threshold': 0, 'maverick_threshold': 1},
         # {'proportion': 0.4, 'conformist_threshold': 0, 'maverick_threshold': 1},
         # {'proportion': 0.6, 'conformist_threshold': 0, 'maverick_threshold': 1},
         # {'proportion': 0.8, 'conformist_threshold': 0, 'maverick_threshold': 1}
         # ],
         # 'social_threshold': [{'slope': 0}, {'slope': 1}, {'slope': 10}, {'slope': 100}],
         'tolerance': [0, 0.2, 0.4],
         # 'velocity': [0.2, 0.4],
         # 'map_size': [40, 50],
         # 'agent_number': [20, 40],
         # 'resilience': [0.95, 0.995, 1.0],
         # 'hill_width': [3, 6],
         # 'depletion_rate': [0.1, 0.2],
         # 'noise': [6, 8],
         'social_type': [
            'heterogeneous',
            'homogeneous'
         ],
        }

        # Set up filenames for storing data and sim parameters
        file_id = files.fileSuffix(sim_type)

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
        data_file_headers = files.get_data_headers(sim_parameters)
        with open(data_file, "w") as f:
            f.write(data_file_headers)

        # to store agent-level data and the params that vary across sims
        if detail == 'agents':
            agents_file = "../data/agents{}.csv".format(file_id)
            agent_columns_to_get = ['id', 'highest_point', 'threshold', 'consumed', 'patches_visited', 'sim']
            agent_file_headers = files.get_data_headers(sim_parameters, agent_columns_to_get)
            with open(agents_file, "w") as f:
                f.write(agent_file_headers)
        else:
            agents_file = None

        # Create list of tasks to run in parallel
        keys = sim_parameters.keys()
        values = (sim_parameters[key] for key in keys)
        # get combinations of above keys (params) and values (possible settings of params)
        run_list = [dict(zip(keys, combination)) for combination in itertools.product(*values)]
        # Either aim to get roughly 200 runs per cell
        R = 200*len(run_list)
        # OR just set number of runs manually, e.g. for testing, by uncommenting and updating the following
        # R = 1
        # Sample randomly from the list of runs
        tasks = [(GlobalParams, random.choice(run_list), i, detail, data_file, agents_file) for i in range(R)]

        with concurrent.futures.ProcessPoolExecutor() as executor:
            results_ = list(tqdm(executor.map(singleRun, tasks), total=R)) # list() needed for tqdm to work for some reason
