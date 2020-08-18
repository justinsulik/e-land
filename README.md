# e-land

Script can be run in 2 ways. Either from terminal or via browser.  

# From terminal

Just use python to run sim.py. Set the paramters for the simulation with sim_parameters on line 139. 
E.g. if sim_paramters contains key `social_threshold` with value `[{'alpha': 2, 'beta': 3}, {'alpha': 20, 'beta': 30}]` 
then each run of the simulation will eithr have social_threshold sampled from beta distribution (2,3) or from beta distribution (20, 30). 
