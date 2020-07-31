print("Loading population...")
import numpy as np, math

class Population():

    def __init__(self, landscape, Sim):
        """
        Required params: landscape, agent_number, alpha, beta, desert, velocity
        """
        self.landscape = landscape
        self.agent_number = Sim.agent_number
        self.agents = np.zeros((self.agent_number),dtype=[('x','f4'),('y','f4'), #position on continuum
                                                  ('x_patch','i4'),('y_patch','i4'), #position on grid
                                                  ('heading','f4'),
                                                  ('velocity','f4'),
                                                  ('previous_significance','f4'),
                                                  ('social_threshold','f4')])

        # INITIALIZE AGENTS
        # set heading to random; velocity to sim;
        self.agents['heading'] = np.random.uniform(0,2*math.pi,self.agent_number)
        self.agents['velocity'] = Sim.velocity
        # have not visited any previous patch, so previous_significance also 0
        self.agents['previous_significance'] = 0
        # set social_threshold according to beta distribution (1,1 = uniform)
        self.agents['social_threshold'] = np.random.beta(Sim.alpha, Sim.beta, size=self.agent_number)

        #PLACE ALL AGENTS IN THE DESERT
        for agent in self.agents:
            low = False
            while not low:
                x = np.random.uniform(0,self.landscape.x_size)
                y = np.random.uniform(0,self.landscape.y_size)
                if self.landscape.getSig(int(x),int(y)) < Sim.desert:
                    agent['x'] = x
                    agent['y'] = y
                    agent['x_patch'] = int(x)
                    agent['y_patch'] = int(y)
                    low = True
        print(self.agents)
