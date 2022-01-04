# Functions for handling data files
# It assumes data files are stored in `../data`

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
                if 'proportion' in sim_parameters[param][0]:
                    param_name = 'social_threshold_proportion'
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
