import numpy as np, strategies
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
    'threshold': 11,
    'status': 12,
    'tolerance': 13,
    'resilience': 14,
    'highest_point': 15,
    'anticonformity': 16,
    'depletion_rate': 17}

# todo def setSocialLearningThreshold():

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
                                                  ('threshold','f4'),
                                                  ('status', 'i4'),
                                                  ('tolerance', 'i4'),
                                                  ('resilience', 'f4'),
                                                  ('highest_point', 'f4'),
                                                  ('anticonformity', 'f4'),
                                                  ('depletion_rate', 'f4'),
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

        # for tracking *unique* patches visited by each agent (uniqueness handled by type "set")
        self.patches_visited = defaultdict(set)

        # Set the search strategies
        self.agents['velocity'] = strategies.set_velocity(params)
        self.agents['threshold'] = strategies.set_thresholds(params)
        self.agents['anticonformity'] = strategies.set_anticonformity(params)
        self.agents['resilience'] = strategies.set_resilience(params)
        self.agents['tolerance'] = strategies.set_tolerance(params)
        self.agents['depletion_rate'] = strategies.set_depletion_rate(params)

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
        # Needed for the node app.js visualization
        # the javascript library "3d-d3" uses y as height, hence switching z and y here
        # Offset by half mapsize
        agents = [{'x': agent[key_dict['x']]-self.landscape.x_size/2,
            'z': agent[key_dict['y']]-self.landscape.y_size/2,
            'y': self.landscape.getSig(agent[key_dict['x_patch']], agent[key_dict['y_patch']]),
            'status': agent[key_dict['status']]} for agent in self.agents.tolist()]
        return(agents)

    def reportSuccess(self):
        # nothing calls this?!?!
        keys = ['id', 'highest_point', 'threshold', 'consumed']
        data = {x['id']: {key: x[key] for key in keys} for x in self.agents[keys]}
        for id in self.patches_visited:
            data[id]['patches_visited'] = len(self.patches_visited[id])
            # add more here: highest point, cumulative value, distance travelled, etc.
        return(data)

    def storePreviousPatch(self):
        # Update to reflect their previous patch
        self.agents['previous_x_patch'] = self.agents['x_patch']
        self.agents['previous_y_patch'] = self.agents['y_patch']
        self.agents['previous_height'] = self.agents['height']

    def updateNewPatch(self):
        # Reflect current position
        self.agents['x_patch'] = np.floor(self.agents['x'])
        self.agents['y_patch'] = np.floor(self.agents['y'])
        self.agents['height'] = self.landscape.getSig(self.agents['x_patch'], self.agents['y_patch'])

        # Track if patch is new
        same_patch = np.logical_and(self.agents['x_patch'] == self.agents['previous_x_patch'], self.agents['y_patch'] == self.agents['previous_y_patch'])
        # If so, add it to set of patches visited by agents
        for i, same in enumerate(same_patch):
            if not same:
                patch = (self.agents[i]['x_patch'], self.agents[i]['y_patch'])
                # track which patches this agent has visited
                self.patches_visited[i].add(patch)
                # track which agents have visited each patch
                self.landscape.incrementVisit(patch, i)

        # Track if patch represents a new personal best
        self.agents['highest_point'] = np.where(
            self.agents['previous_height']>self.agents['highest_point'],
            self.agents['previous_height'],
            self.agents['highest_point']
        )

    def move(self):
        # Before moving, track info from the previous patch
        self.storePreviousPatch()
        # Move all agents
        self.agents['x'] += np.cos(self.agents['heading']) * self.agents['velocity']
        self.agents['y'] += np.sin(self.agents['heading']) * self.agents['velocity']
        # Wrap around
        self.agents['x'] = np.round(self.agents['x'], 4) % self.landscape.x_size
        self.agents['y'] = np.round(self.agents['y'], 4) % self.landscape.y_size
        # After moving, update info from current patch
        self.updateNewPatch()

    def work(self):
        for agent in self.agents:
            # get the height each time, otherwise agents with higher indexes will have out-of-date info
            height = self.landscape.getSig(agent['x_patch'], agent['y_patch'])
            if height >= agent['depletion_rate'] + self.landscape.sig_threshold:
                self.landscape.setSig(agent['x_patch'], agent['y_patch'], height - agent['depletion_rate'])
            elif height > self.landscape.sig_threshold:
                self.landscape.setSig(agent['x_patch'], agent['y_patch'], self.landscape.sig_threshold)
            agent['consumed'] += height


    def checkSocialLearning(self, i):
        # Find out the amounts that could be learned (height/distance, i.e. as slopes) from all other agents

        # First, find out where focal agent is
        agent = self.agents[i]
        agentX = agent['x']
        agentY = agent['y']

        # Calculate distance to all agents
        # (bearing in mind that the shortest distance could be over the toroidal wraparound)
        distX1 = self.agents['x']-agentX
        distX2 = self.landscape.x_size - distX1 #WRAPPED DISTANCE
        distY1 = self.agents['y']-agentY
        distY2 = self.landscape.y_size - distY1 #WRAPPED DISTANCE
        distX = np.minimum(distX2,distX1)
        distY = np.minimum(distY2,distY1)

        # Rule out anyone not worth following
        too_close = np.logical_and(self.agents['x'] == agent['x'],self.agents['y'] == agent['y'])
        below_significance = self.agents['height'] <= self.landscape.sig_threshold
        dont_follow = np.logical_or(too_close, below_significance)

        # Calculate how high others were at the end of the previous time step
        # if dont_follow, set np.nan else set height
        othersHeights = np.where(dont_follow, np.nan, self.agents['height'])
        # Difference in height from focal agent
        heightDeltas = othersHeights - self.landscape.getSig(agent['x_patch'],agent['y_patch'])
        # Calculate distance
        distances = np.sqrt(distX**2 + distY**2)
        # Calculate value as change in height / distance
        inclines = heightDeltas / distances
        return(inclines)

    def goneTooFarDown(self, i):
        # See if the agent is doing uphill or downhill.
        # And if downhill, if it's too far downhill to be acceptable given the agents tolerance value
        agent = self.agents[i]
        current_height = self.landscape.getSig(agent['x_patch'],agent['y_patch'])
        # Is the agent going downhill? Allow them to continue if random p < tolerance
        change_in_height = agent['previous_height'] - self.landscape.getSig(agent['x_patch'],agent['y_patch'])
        if current_height < agent['previous_height'] - agent['tolerance']:
            return True
        else:
            return False

    def decide(self):
        # Keep on same heading or look around?
        # If too far downhill, make a decision about learning strategy
        for i, agent in enumerate(self.agents):
            intolerable_decrease = self.goneTooFarDown(i)
            if intolerable_decrease:
                # Lower the agent's resilience because of failure to climb
                agent['threshold'] = round(agent['threshold'] * agent['resilience'], 3)
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
                if max_learnable > agent['threshold']:
                    # If yes, identify best candidate to follow
                    # (choose randomly if tie)
                    maxAgent = self.agents[np.random.choice(np.flatnonzero(inclines == np.nanmax(inclines)))]
                    self.setHeading(i, maxAgent['x_patch'],maxAgent['y_patch'])
                    agent['status'] = 1 # social learning
                else:
                    self.exploreLocalArea(i)
            else:
                # Keep going
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
            self.setHeading(i,chosenPatch['x'],chosenPatch['y'])
            agent['status'] = 4 # exploring-local
        else:
            # If no patches are higher, pick a completely random direction
            agent['heading'] = np.random.uniform(0,2*np.pi)
            agent['status'] = 3 # completely lost


    def setHeading(self,i,xTarg,yTarg):
        """
        Sets agent's heading towards the target position
        Takes fastest route, i.e. takes toroidal wrapping of landscape into account
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
