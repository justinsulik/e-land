# e-land

Script can be run in 2 ways. Either from terminal or via browser.  

# From terminal

Just use python3 to run `sim.py`

Set the parameters for the simulation with dictionary `sim_parameters` on line 139. 
E.g. if `sim_parameters` contains key `social_threshold` with value `[{'alpha': 2, 'beta': 3}, {'alpha': 20, 'beta': 30}]`
then each run of the simulation will either have agents' social thresholds sampled from beta distribution (2,3) or beta distribution (20, 30). For descriptions of the various parameters, see comments in `landscape.py` or `population.py`.

It will run 100 simulations for each combination of parameter settings in `sim_parameters`. So if `sim_parameters = {x: [a, b], y: [c, d]}` then it will do 400 runs, split roughly equally between a+c, a+d, b+c and b+d.

If you're running with python, it will try save the output in a folder `../data/` so will probably give you an error if it doesn't exist.

# From browser

Use `nodemon app.js` (which may need `npm install nodemon` first) to launch the server, then open browser and go to `localhost:5000`. This will run one simulation with the default settings (which can be manually changed in `GlobalParams`) to see what's going on.  

Ultimately I'll add in inputs here so that the parameters can be changed from the browser).
