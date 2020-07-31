from landscape import Landscape
from population import Population
from plot import plot3d

class Sim():
    """
    General parameters for the simulation
    """
    map_size = 50
    agent_speed = 1

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
    noise = 5
    smoothing = 15

    # AGENTS
    agent_number = 1
    # params for beta distribution https://homepage.divms.uiowa.edu/~mbognar/applets/beta.html
    alpha = 1
    beta = 1
    velocity = 1

if __name__ == "__main__":
    landscape = Landscape(Sim)
    population = Population(landscape, Sim)
    plot3d(landscape)
