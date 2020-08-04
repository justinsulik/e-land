# print("Loading population...")
import numpy as np, math

# Since the agent info is passed to the js script as a dict rather than a tuple,
# this dict maps between the agent info keys and tuple indices
key_dict = {'x': 0,
    'y': 1,
    'x_patch': 2,
    'y_patch': 3,
    'height': 4,
    'heading': 5,
    'velocity': 6,
    'previous_x_patch': 7,
    'previous_y_patch': 8,
    'previous_height': 9,
    'social_threshold': 10,
    'status': 11}


class Population():

    def __init__(self, landscape, Sim):
        """
        Required params: landscape, agent_number, social_threshold, beta, desert, velocity
        """
        self.landscape = landscape
        self.agent_number = Sim.agent_number
        self.base_velocity = Sim.velocity
        self.agents = np.zeros((self.agent_number),dtype=[('x','f4'),('y','f4'), #position on continuum
                                                  ('x_patch','i4'),('y_patch','i4'), #position on grid
                                                  ('height','f4'),
                                                  ('heading','f4'),
                                                  ('velocity','f4'),
                                                  ('previous_x_patch','i4'),('previous_y_patch','i4'),
                                                  ('previous_height','f4'),
                                                  ('social_threshold','f4'),
                                                  ('status', 'i4')])

        # INITIALIZE AGENTS
        # set heading to random; velocity to sim;
        self.agents['heading'] = np.random.uniform(0,2*math.pi,self.agent_number)
        self.agents['velocity'] = Sim.velocity
        # have not visited any previous patch, so previous_height also 0
        self.agents['previous_height'] = 0
        # set social_threshold according to beta distribution (1,1 = uniform)
        self.agents['social_threshold'] = Sim.social_threshold#np.random.beta(Sim.social_threshold, Sim.beta, size=self.agent_number)
        # set type to explore
        self.agents['status'] = 0

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

    def reportAgents(self):
        """
        Generate list of agents with x, y, height vals
        """
        # Stupidly, 3d-ds uses y as height
        # Offset by half mapsize
        agents = [{'x': agent[key_dict['x']]-self.landscape.x_size/2,
            'z': agent[key_dict['y']]-self.landscape.y_size/2,
            'y': self.landscape.getSig(agent[key_dict['x_patch']], agent[key_dict['y_patch']]),
            'status': agent[key_dict['status']]} for agent in self.agents.tolist()]
        return(agents)

    def findPatches(self):
        #end of each round, calculate patches for all agents, reduces unnecessary np.round()
        #update height while at it
        self.agents['x_patch'] = np.round(self.agents['x'])
        self.agents['y_patch'] = np.round(self.agents['y'])

    def wrap(self,coord,limit):
        """
        Wrap agent position around edge of map
        Since modulo handles integers, separate these out from decimals
        """
        coord_integer = np.floor(coord)
        coord_decimal = coord%coord_integer if coord_integer != 0 else coord
        coord_sign = 1 if coord >= 0 else -1
        coord_new = coord_integer%limit + coord_sign*coord_decimal
        return(coord_new)


    def move(self, i):
        agent = self.agents[i]
        agent['x'] += np.cos(agent['heading'])*agent['velocity']
        agent['y'] += np.sin(agent['heading'])*agent['velocity']

        agent['x'] = self.wrap(agent['x'],self.landscape.x_size)
        agent['y'] = self.wrap(agent['y'],self.landscape.y_size)
        agent['x_patch'] = int(agent['x'])
        agent['y_patch'] = int(agent['y'])

    def consume(self, i):
        agent = self.agents[i]
        sig = self.landscape.getSig(agent['x_patch'], agent['y_patch']);
        if sig>1:
            self.landscape.setSig(agent['x_patch'], agent['y_patch'], sig-1)

    def explore(self, i):
        agent = self.agents[i]
        # self.landscape.incVisit(agent['x_patch'],agent['y_patch'])
        sig = self.landscape.getSig(agent['x_patch'],agent['y_patch'])
        previous_height = agent['previous_height']
        agentX = agent['x']
        agentY = agent['y']

        #GOING DOWNHILL?
        if sig < previous_height:
            #1. SOCIAL LEARNING:
            distX1 = self.agents['x']-agentX
            distX2 = self.landscape.x_size - distX1 #WRAPPED DISTANCE
            distY1 = self.agents['y']-agentY
            distY2 = self.landscape.y_size - distY1
            distX = np.minimum(distX1,distX2)
            distY = np.minimum(distY1,distY2)

            heightDeltas = self.agents['previous_height']-sig #COMPARE YOUR OWN ELEVATION TO HEIGHT OF OTHERS AT LAST TIMESTEP

            distX[i] = np.nan #10000 #don't follow yourself
            distY[i] = np.nan #10000

            dist = np.sqrt(distX**2 + distY**2)

            denominator = dist

            inclines = heightDeltas / denominator

            #agentsInCone = self.agents[inclines > agent['social_threshold']] #CHOOSE THOSE AGENTS WHO ARE ABOVE THE REQUIRED ANGLE (TAN A) = ALPHA

            maxIncline = np.nanmax(inclines) #max social incline
            #print "maxIncline", maxIncline

            if maxIncline > agent['social_threshold']:

                maxAgent = self.agents[np.nanargmax(inclines)]
                self.setHeadingToPatch(i,maxAgent['x'],maxAgent['y'])
                agent['velocity'] = self.base_velocity
                agent['status'] = 1 # social learning

            else:
                #IF NO OTHER AGENTS IN CONE --> INDIVIDUAL SEARCH
                nh = self.landscape.getMooreNeighborhood(agent['x_patch'],agent['y_patch'])

                #compare heights
                mooreElevations = nh['height']-sig
                geqMoores = nh[mooreElevations > 0]
                if len(geqMoores) > 0:
                    # Select a random patch to explore
                    chosenPatch = np.random.choice(geqMoores) #choose a new (geq) patch randomdly)
                    # If the random patch is better than the previous height, go there
                    if chosenPatch['height'] >= previous_height:
                        self.setHeadingToPatch(i,chosenPatch['x'],chosenPatch['y'])
                        agent['status'] = 0 # exploring-random
                    else:
                        self.setHeadingToPatch(i, agent['previous_x_patch'], agent['previous_y_patch'])
                        agent['status'] = 3 # exploring-return to previous


                else:
                    #IF ONLY LOWER PATCHES, STOP:
                    agent['velocity'] = 0.0
                    agent['status'] = 2 # stopped
                    #print "stopping"

        else: #MOVING UPHILL, NO NEED TO UPDATE HEADING
            agent['velocity'] = self.base_velocity

        #MOVE
        agent['previous_height'] = sig
        self.move(i)
        self.consume(i)

    def setHeadingToPatch(self,i,xTarg,yTarg):
        """
        sets agent's heading towards the center of a target patch
        takes fastest route, i.e. takes wrapping into account
        """
        agent = self.agents[i]

        #for both x and y, there are three cases to consider: actual value x/yTarg and its projections on both sides
        xTarget = np.array([0,0,0])
        xTarget[0] = xTarg-self.landscape.x_size
        xTarget[1] = xTarg #the actual point
        xTarget[2] = xTarg+self.landscape.x_size #projection to the right
        cosArray = xTarget-agent['x']
        minInd = np.argmin(np.absolute(cosArray)) #get index for the point at shortest distance
        cos = cosArray[minInd]

        yTarget = np.array([0,0,0])
        yTarget[0] = yTarg-self.landscape.y_size
        yTarget[1] = yTarg #the actual point
        yTarget[2] = yTarg+self.landscape.y_size
        sinArray = yTarget-agent['y']
        minInd = np.argmin(np.absolute(sinArray)) #get index for the point at shortest distance
        sin = sinArray[minInd]

        #check for division by zero
        if cos == 0:
            if sin > 0: agent['heading'] = math.pi/2
            else: agent['heading'] = 3*math.pi/2
        else:
            tan = sin / cos
            #choose the heading in the correct quadrant
            if cos > 0:
                agent['heading'] = np.arctan(tan) % (2*np.pi) #modulo makes the angle > 0
            else:
                agent['heading'] = (np.pi+np.arctan(tan))%(2*np.pi)
