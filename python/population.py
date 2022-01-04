import numpy as np
from collections import defaultdict

# Since the agent info is passed to the js script as a dict, but is handled as a structured array in the numpy matrices here,
# this dict maps between the agent info keys and array indices
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
    'resilience': 14,
    'highest_point': 15}

class Population():

    def __init__(self, landscape, params):
        """
        Generate a population of agents and drop them in the desert
        """
        self.landscape = landscape
        self.agent_number = params.agent_number
        self.agents = np.zeros((self.agent_number),dtype=[
                                                  ('id', 'i4'),
                                                  ('x','f4'),('y','f4'), #position on continuum
                                                  ('x_patch','i4'), ('y_patch','i4'), #position on grid
                                                  ('height','f4'),
                                                  ('heading','f4'),
                                                  ('velocity','f4'),
                                                  ('previous_x_patch','i4'),('previous_y_patch','i4'),
                                                  ('previous_height','f4'),
                                                  ('social_threshold','f4'),
                                                  ('status', 'i4'),
                                                  ('tolerance', 'i4'),
                                                  ('resilience', 'f4'),
                                                  ('highest_point', 'f4'),
                                                  ('consumed', 'f4'),
                                                  ('starting_x', 'i4'), ('starting_y', 'i4')])
        # INITIALIZE AGENTS
        # assign index id
        self.agents['id'] = range(self.agent_number)
        # set heading to random
        self.agents['heading'] = np.random.uniform(0,2*np.pi,self.agent_number)
        # have not visited any previous patch, so previous_height is 0
        self.agents['previous_height'] = 0
        # at the start, each agent has made 0 progress
        self.agents['consumed'] = 0
        # Set status to explore
        self.agents['status'] = 0
        # set other params to given vals
        self.agents['velocity'] = params.velocity
        self.agents['resilience'] = params.resilience
        self.agents['tolerance'] = params.tolerance

        # for tracking *unique* patches visited by each agent (uniqueness handled by type "set")
        self.patches_visited = defaultdict(set)

        # SET SOCIAL LEARNING THRESHOLDS
        # The social learning thresholds can be set as:
            # distributions (beta, gamma)
            # constants
            # proportions
        # if population is homogeneous, everyone gets the same value (e.g., the mean of the distribution)
        # if population is heterogeneous, everyone gets different valuers (e.g., random sample from the distribution)
        if params.social_type == 'homogeneous':
            # As a reminder:
                # mean of beta distribution (a,b) = a/(a+b)
                # mean of gamma distribution (k, theta) = k*theta
            if 'alpha' in params.social_threshold and 'beta' in params.social_threshold:
                # it's a beta distribution
                self.agents['social_threshold'] = params.social_threshold['alpha']/(params.social_threshold['alpha']+params.social_threshold['beta'])
            elif 'k' in params.social_threshold and 'theta' in params.social_threshold:
                # it's a gamma distribution
                self.agents['social_threshold'] = params.social_threshold['k']*params.social_threshold['theta']
            elif 'slope' in params.social_threshold:
                # constant value, everyone gets the same (there's no heterogeneous version of this)
                self.agents['social_threshold'] = params.social_threshold['slope']
            elif 'proportion' in params.social_threshold:
                # 'proportion' refers to proportion of conformists (p) vs. mavericks (1-p)
                # (see heterogeneous version below).
                # However, for 'homogemeous' version of proportion, obviously cant have conformists vs. mavericks
                # so instead, get weighted mean of the given thresholds: p*conformists + (1-p)*mavericks
                self.agents['social_threshold'] = params.social_threshold['proportion']*params.social_threshold['conformist_threshold'] + (1-params.social_threshold['proportion'])*params.social_threshold['maverick_threshold']
            else:
                raise Exception("social_threshold type not recognised")
        elif params.social_type == 'heterogeneous':
            if 'alpha' in params.social_threshold and 'beta' in params.social_threshold:
                # it's a beta distribution
                self.agents['social_threshold'] = np.random.beta(params.social_threshold['alpha'], params.social_threshold['beta'], self.agent_number)
            elif 'k' in params.social_threshold and 'theta' in params.social_threshold:
                # it's a gamma distribution
                self.agents['social_threshold'] = np.random.gamma(params.social_threshold['k'], params.social_threshold['theta'], self.agent_number)
            elif 'proportion' in params.social_threshold and 'conformist_threshold' in params.social_threshold and 'maverick_threshold' in params.social_threshold:
                # 'proportion' refers to proportion of conformists (p) vs. mavericks (1-p)
                conformists_count = int(self.agent_number*params.social_threshold['proportion'])
                mavericks_count = self.agent_number - conformists_count
                social_thresholds = conformists_count*[params.social_threshold['conformist_threshold']] + mavericks_count*[params.social_threshold['maverick_threshold']]
                self.agents['social_threshold'] = social_thresholds
            else:
                raise Exception("social_threshold type not recognised")
        else:
            raise Exception("social_type not recognised")

        #PLACE ALL AGENTS IN THE DESERT
        for agent in self.agents:
            # Iteratively check if the random placement is below the minimum significance for it to count as the desert
            low = False
            while not low:
                x = np.random.uniform(0,self.landscape.x_size)
                y = np.random.uniform(0,self.landscape.y_size)
                starting_height = self.landscape.getSig(int(x),int(y))
                if 0 <= starting_height < params.desert:
                    agent['x'] = x
                    agent['y'] = y
                    agent['highest_point'] = starting_height
                    low = True
        self.agents['starting_x'] = self.agents['x_patch'] = np.floor(self.agents['x'])
        self.agents['starting_y'] = self.agents['y_patch'] = np.floor(self.agents['y'])

    def trackAgents(self):
        """
        Generate list of agents with x, y, height vals
        """
        # Needed for the node app visualization
        # the javascript library "3d-d3" uses y as height, hence switching z and y
        # Offset by half mapsize
        agents = [{'x': agent[key_dict['x']]-self.landscape.x_size/2,
            'z': agent[key_dict['y']]-self.landscape.y_size/2,
            'y': self.landscape.getSig(agent[key_dict['x_patch']], agent[key_dict['y_patch']]),
            'status': agent[key_dict['status']]} for agent in self.agents.tolist()]
        return(agents)

    def reportSuccess(self):
        keys = ['id', 'highest_point', 'social_threshold', 'consumed']
        data = {x['id']: {key: x[key] for key in keys} for x in self.agents[keys]}
        for id in self.patches_visited:
            data[id]['patches_visited'] = len(self.patches_visited[id])
        return(data)

    def findPatches(self):
        # Update to reflect their previous patch
        self.agents['previous_x_patch'] = self.agents['x_patch']
        self.agents['previous_y_patch'] = self.agents['y_patch']

    def updatePatches(self):
        # Reflect current position
        self.agents['x_patch'] = np.floor(self.agents['x'])
        self.agents['y_patch'] = np.floor(self.agents['y'])

        # Track if patch is new
        same_patch = np.logical_and(self.agents['x_patch'] == self.agents['previous_x_patch'], self.agents['y_patch'] == self.agents['previous_y_patch'])

        # If so, add it to set of patches visited by agents
        # I wish I knew how to do this without a for-loop
        for i, same in enumerate(same_patch):
            if not same:
                patch = (self.agents[i]['x_patch'], self.agents[i]['y_patch'])
                self.patches_visited[i].add(patch)


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
            agent['consumed'] += significance

    def updateHeight(self):
        for agent in self.agents:
            agent_height = self.landscape.getSig(agent['x_patch'], agent['y_patch'])
            agent['previous_height'] = agent_height
            if agent_height > agent['highest_point']:
                agent['highest_point'] = agent_height

    def checkSocialLearning(self, i):
        # Find out the amounts that could be learned (height/distance, i.e. as slopes) from all other agents
        # Find out where focal agent is
        agent = self.agents[i]
        agentX = agent['x']
        agentY = agent['y']
        # Calculate distance to all agents (in 2 directions, given that the landscape wraps around)
        distX1 = self.agents['x']-agentX
        distX2 = self.landscape.x_size - distX1 #WRAPPED DISTANCE
        distY1 = self.agents['y']-agentY
        distY2 = self.landscape.y_size - distY1 #WRAPPED DISTANCE
        distX = np.minimum(distX2,distX1)
        distY = np.minimum(distY2,distY1)
        # Calculate how high others were at the end of the previous time step
        othersHeights = self.agents['previous_height']
        # Don't follow anyone who is below the significance threshold: they have no epistemic value to offer!
        othersHeights[othersHeights < self.landscape.sig_threshold] = np.nan
        # Compare your own elevation to the height of others
        heightDeltas = othersHeights - self.landscape.getSig(agent['x_patch'],agent['y_patch'])
        distX[i] = np.nan # agents can't follow themselves
        distY[i] = np.nan # agents can't follow themselves

        # Calculate distance
        distance = np.sqrt(distX**2 + distY**2)
        inclines = heightDeltas / distance
        return(inclines)

    def goneTooFarDown(self, i):
        # See if the agent is doing uphill or downhill.
        # And if downhill, if it's too far downhill to be acceptable given the agents tolerance value
        agent = self.agents[i]
        current_height = self.landscape.getSig(agent['x_patch'],agent['y_patch'])
        # Is the agent going downhill, more than what is within their tolerance?
        if current_height < agent['previous_height'] - agent['tolerance']:
            return True
        else:
            return False

    def explore(self):
        # Do general exploration, and check progress (uphill vs. too far downhill)
        # If too far downhill, make a decision about learning strategy
        for i, agent in enumerate(self.agents):
            intolerable_decrease = self.goneTooFarDown(i)
            agent = self.agents[i]
            if intolerable_decrease:
                # Lower the agent's resilience because of failure to climb
                agent['social_threshold'] = round(agent['social_threshold'] * agent['resilience'], 3)
                # Find out out much agent could learn (which means there must be at least one other agent)
                if len(self.agents) > 1:
                    inclines = self.checkSocialLearning(i)
                    # Check if all inclines are nan (because all other agents are below the significance threshold, and thus not worth learning from)
                    if np.isnan(inclines).all(0):
                        max_learnable = -9999
                    else:
                        max_learnable = np.nanmax(inclines)
                else:
                    max_learnable = -9999
                # Check if that amount is above threshold
                if max_learnable > agent['social_threshold']:
                    # If yes, identify best candidate to follow
                    # (choose randomly if tie)
                    maxAgent = self.agents[np.random.choice(np.flatnonzero(inclines == np.nanmax(inclines)))]
                    self.setHeadingToPatch(i, maxAgent['x_patch'],maxAgent['y_patch'])
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
