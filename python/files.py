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

def get_data_headers(sim_parameters, agent_columns_to_get=[]):
    # Is this looking for group-level or agent-level data?
    if len(agent_columns_to_get)==0:
        # group-level data only
        headers = 'timestep,mass,sim'
    else:
        # agent-level data
        headers = ','.join(agent_columns_to_get)
    if len(sim_parameters)==0:
        headers += '\n'
    else:
        headers += ',' + get_sim_headers(sim_parameters)
    return(headers)

def get_sim_headers(sim_parameters):
    headers = ''
    for i, param in enumerate(sim_parameters):
        if param == 'social_threshold':
            param_name = ','.join(sim_parameters[param][0].keys())
        else:
            param_name = param
        if i<len(sim_parameters)-1:
            headers += param_name + ','
        else:
            headers += param_name + '\n'
    return(headers)
