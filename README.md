# e-land

Script can be run in 2 ways. Either from terminal or via browser.  

# From terminal

Just use python3 to run `sim.py`

Set the paramters for the simulation with dictionary `sim_parameters` on line 139. 
E.g. if `sim_paramters` contains key `social_threshold` with value `[{'alpha': 2, 'beta': 3}, {'alpha': 20, 'beta': 30}]`
then each run of the simulation will either have agents' social thresholds sampled from beta distribution (2,3) or beta distribution (20, 30) (for descriptions of the various parameters, see comments in `landscape.py` or `population.py`). 

It will run 100 simulations for each combination of parameter settings in `sim_parameters`. So if `sim_parameters` **also** has key `social_type` with value `['heterogeneous', 'homogeneous']`, where heterogeneous is sampled randomly from the beta distribution (a,b) and homogeneous is all agents set to the mean of the beta distribution = $a/(a+b)$, then it will run:

- 100 heterogeneous from beta(2,3)
- 100 heterogeneous from beta(20,30)
- 100 homogeneous at mean of beta(2,3)
- 100 homogenous at mean of beta(20,30) 

# From browser

Use `nodemon app.js` to launch the server, then open browser and go to localhost:5000. This will run one simulation with the default settings (which can be manually changed in `GlobalParam`) to see what's going on.  

Ultimately I'll add in inputs here so that the parameters can be changed from the browser). 


