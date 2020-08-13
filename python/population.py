import numpy as np

# Since the agent info is passed to the js script as a dict rather than a tuple,
# this dict maps between the agent info keys and tuple indices
key_dict = {'id': 0,
    'x': 1,
    'y': 2,
    'x_patch': 3,
    'y_patch': 4,
    'height': 5,
    'heading': 6,
    'velocity': 7,
    'previous_x_patch': 8,
    'previous_y_patch': 9,
    'previous_height': 10,
    'social_threshold': 11,
    'status': 12,
    'tolerance': 13,
    'resilience': 14}

class Population():

    def __init__(self, landscape, params):
        """
        Required params: landscape, agent_number, social_threshold, beta, desert, velocity
        """
        self.landscape = landscape
        self.agent_number = params.agent_number
        self.base_velocity = params.velocity
        self.agents = np.zeros((self.agent_number),dtype=[('id', 'i4'),
                                                  ('x','f4'),('y','f4'), #position on continuum
                                                  ('x_patch','i4'),('y_patch','i4'), #position on grid
                                                  ('height','f4'),
                                                  ('heading','f4'),
                                                  ('velocity','f4'),
                                                  ('previous_x_patch','i4'),('previous_y_patch','i4'),
                                                  ('previous_height','f4'),
                                                  ('social_threshold','f4'),
                                                  ('status', 'i4'),
                                                  ('tolerance', 'i4'),
                                                  ('resilience', 'f4')])

        # INITIALIZE AGENTS
        # assign index id
        self.agents['id'] = range(self.agent_number)
        # set heading to random
        self.agents['heading'] = np.random.uniform(0,2*np.pi,self.agent_number)
        # have not visited any previous patch, so previous_height also 0
        self.agents['previous_height'] = 0
        # Set status to explore
        self.agents['status'] = 0
        # set other params to given vals
        self.agents['velocity'] = params.velocity
        self.agents['tolerance'] = params.tolerance
        self.agents['resilience'] = params.resilience

        # SOCIAL LEARNING
        # Set values in range (0,1)
        if params.social_type == 'homogeneous':
            # If population is homogenous, everyone gets same value: the mean of the beta distribution
            # beta(a,b) has mean = a/(a+b)
            self.agents['social_threshold'] = params.social_threshold['alpha']/(params.social_threshold['alpha']+params.social_threshold['beta'])
        elif params.social_type == 'heterogeneous':
            # If population is heterogeneous, draw randomly from beta distribution
            self.agents['social_threshold'] = np.random.beta(params.social_threshold['alpha'], params.social_threshold['beta'],self.agent_number)
        ## Adjust values according to map size and height, such that base value 1 -- generated above --- maps to max(height)/max(distance)
        #normalisation_factor = self.landscape.max_height/max(self.landscape.x_size/2, self.landscape.y_size/2)
        #self.agents['social_threshold'] *= normalisation_factor




        #PLACE ALL AGENTS IN THE DESERT
        for agent in self.agents:
            low = False
            while not low:
                x = np.random.uniform(0,self.landscape.x_size)
                y = np.random.uniform(0,self.landscape.y_size)
                if 0 <= self.landscape.getSig(int(x),int(y)) < params.desert:
                    agent['x'] = x
                    agent['y'] = y
                    agent['x_patch'] = int(x)
                    agent['y_patch'] = int(y)
                    low = True

    def reportAgents(self):
        """
        Generate list of agents with x, y, height vals
        """
        # Needed for the node app visualization
        # 3d-d3 uses y as height, hence switching z and y
        # Offset by half mapsize
        agents = [{'x': agent[key_dict['x']]-self.landscape.x_size/2,
            'z': agent[key_dict['y']]-self.landscape.y_size/2,
            'y': self.landscape.getSig(agent[key_dict['x_patch']], agent[key_dict['y_patch']]),
            'status': agent[key_dict['status']]} for agent in self.agents.tolist()]
        return(agents)

    def findPatches(self):
        #end of each round, calculate patches for all agents, reduces unnecessary np.round()
        #update height while at it
        self.agents['x_patch'] = np.floor(self.agents['x'])
        self.agents['y_patch'] = np.floor(self.agents['y'])

    def wrap(self,coord,limit):
        """
        Wrap agent position around edge of map
        Since modulo handles integers, separate these out from decimals
        """
        coord_integer = np.floor(coord)
        coord_decimal = coord%coord_integer if coord_integer != 0 else coord
        coord_sign = 1 if coord > 0 else -1
        coord_new = coord_integer%limit + coord_sign*coord_decimal
        return(coord_new)

    def move(self):
        for agent in self.agents:
            agent['x'] += np.cos(agent['heading'])*agent['velocity']
            agent['y'] += np.sin(agent['heading'])*agent['velocity']
            agent['x'] = self.wrap(agent['x'],self.landscape.x_size)
            agent['y'] = self.wrap(agent['y'],self.landscape.y_size)

    def consume(self, depletion_rate):
        for agent in self.agents:
            significance = self.landscape.getSig(agent['x_patch'], agent['y_patch'])
            if significance >= depletion_rate:
                new_significance = significance - depletion_rate
                self.landscape.setSig(agent['x_patch'], agent['y_patch'], new_significance)
            elif 0 < significance < depletion_rate:
                self.landscape.setSig(agent['x_patch'], agent['y_patch'], 0)


    def updateHeight(self):
        for agent in self.agents:
            agent['previous_height'] = self.landscape.getSig(agent['x_patch'], agent['y_patch'])

    def checkSocialLearning(self, i):
        # Find out the amounts that could be learned (as inclines) from all other agents
        agent = self.agents[i]
        agentX = agent['x']
        agentY = agent['y']
        distX1 = self.agents['x']-agentX
        distX2 = self.landscape.x_size - distX1 #WRAPPED DISTANCE
        distY1 = self.agents['y']-agentY
        distY2 = self.landscape.y_size - distY1 #WRAPPED DISTANCE
        distX = np.minimum(distX2,distX1)
        distY = np.minimum(distY2,distY1)
        heightDeltas = self.agents['previous_height'] - self.landscape.getSig(agent['x_patch'],agent['y_patch']) #COMPARE YOUR OWN ELEVATION TO HEIGHT OF OTHERS AT LAST TIMESTEP
        distX[i] = np.nan # agents can't follow themselves
        distY[i] = np.nan

        dist = np.sqrt(distX**2 + distY**2)
        denominator = dist
        inclines = heightDeltas / denominator
        return(inclines)

    def goneTooFarDown(self, i):
        # See if the agent is doing uphill or downhill.
        # And if downhill, if it's too far downhill to be acceptable given the agents tolerance value
        agent = self.agents[i]
        current_height = self.landscape.getSig(agent['x_patch'],agent['y_patch'])
        # Is the agent going downhill, more than what is within their tolerance?
        if current_height < agent['previous_height'] + agent['tolerance']:
            return True
        else:
            return False

    def explore(self):
        # self.landscape.incVisit(agent['x_patch'],agent['y_patch'])
        for i, agent in enumerate(self.agents):
            intolerable_decrease = self.goneTooFarDown(i)
            agent = self.agents[i]
            if intolerable_decrease:
                # Lower the agent's resilience because of failure to climb
                agent['social_threshold'] = round(agent['social_threshold'] * agent['resilience'], 3)
                # Find out out much agent could learn
                inclines = self.checkSocialLearning(i)
                max_learnable = np.nanmax(inclines)
                # Check if that amount is above threshold
                if max_learnable > agent['social_threshold']:
                    # If yes, identify best candidate to follow
                    # (choose randomly if tie)
                    maxAgent = self.agents[np.random.choice(np.flatnonzero(inclines == np.nanmax(inclines)))]
                    self.setHeadingToPatch(i, maxAgent['x'],maxAgent['y'])
                    agent['status'] = 1 # social learning
                else:
                    self.exploreLocalArea(i)
            else:
                agent['status'] = 0


    def exploreLocalArea(self, i):
        # Since there is no suitable agent to follow:
        # First check Moore neighborhood for a higher patch
        # If no higher patches, pick a random direction
        agent = self.agents[i]
        current_height = self.landscape.getSig(agent['x_patch'],agent['y_patch'])
        neighborhood = self.landscape.getMooreNeighborhood(agent['x_patch'],agent['y_patch'])
        # Compare heights
        mooreElevations = neighborhood['height']-current_height
        geqMoores = neighborhood[mooreElevations >= 0] #geq: greater than or equal to

        if len(geqMoores) > 0:
            # If any neighboring patch is higher, select a random higher patch to check
            chosenPatch = np.random.choice(geqMoores)
            self.setHeadingToPatch(i,chosenPatch['x'],chosenPatch['y'])
            agent['status'] = 4 # exploring-local
        else:
            # If no patches are higher, pick a completely random direction
            agent['heading'] = np.random.uniform(0,2*np.pi)
            agent['status'] = 3 # completely lost


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
        cosArray = xTarget-agent['x_patch']
        minInd = np.argmin(np.absolute(cosArray)) #get index for the point at shortest distance
        cos = cosArray[minInd]

        yTarget = np.array([0,0,0])
        yTarget[0] = yTarg-self.landscape.y_size
        yTarget[1] = yTarg #the actual point
        yTarget[2] = yTarg+self.landscape.y_size
        sinArray = yTarget-agent['y_patch']
        minInd = np.argmin(np.absolute(sinArray)) #get index for the point at shortest distance
        sin = sinArray[minInd]

        #check for division by zero
        if cos == 0:
            if sin > 0:
                agent['heading'] = np.pi/2
            else:
                agent['heading'] = 3*np.pi/2
        else:
            tan = sin / cos
            #choose the heading in the correct quadrant
            if cos > 0:
                agent['heading'] = np.arctan(tan) % (2*np.pi) #modulo makes the angle > 0
            else:
                agent['heading'] = (np.pi+np.arctan(tan))%(2*np.pi)
