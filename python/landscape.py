from perlin import PerlinNoiseFactory
import numpy as np
from scipy.stats import multivariate_normal

class Landscape():
    """
    Class describing the epistemic landscape consisting of a number of grid 'patches'
    """

    def __init__(self,params):
        """
        Required params: x_size,y_size,depletion,hills,hill_width,noise,smoothing
        """
        # x_size, y_size (int): size of grid FROM ORIGIN IN CENTER
        # depletion (float in [0,1]): depletion rate
        self.x_size = params.map_size
        self.y_size = params.map_size
        self.depletion = params.depletion

        # GRID
        # Each patch in grid is defined by:
        # x, y (int): coordinates
        # height (float): epistemic value of the patch
        # visited (int): number of times visited
        self.grid = np.zeros((self.x_size,self.y_size),dtype = [
            ('x', np.int8),
            ('y', np.int8),
            ('height', np.float64),
            ('visited', np.int8)
            ]
        )

        # COORDINATES
        self.grid['x'] = np.indices(self.grid.shape)[0]
        self.grid['y'] = np.indices(self.grid.shape)[1]

        # MOORE NEIGHBORHOOD
        # data needed by getMooreNeighborhood to find the 8 patches surrounding a given patch
        self.mooreArray = np.zeros(8,dtype =[('x','i4'),('y','i4'),("height", 'f4'),("visited", 'i4')])
        self.mooreIndList = ((-1,-1),(-1,0),(-1,+1),(0,-1),(0,+1),(+1,-1),(+1,0),(+1,+1))

        # HILLS
        for i in range(params.hill_number):
            hill_center_x = i*params.map_size/params.hill_number
            hill_center_y = i*params.map_size/params.hill_number
            self.addGaussian(hill_center_x,hill_center_y,params.hill_width/params.noise*1000,params.hill_width)

        # NOISE
        self.addPerlin(params.noise, params.smoothing, params.octaves)

        # LANDSCAPE GLOBAL PROPERTIES
        # epistemic mass: total amount of epistemic value at start of simulation
        self.total_epistemic_mass = self.epistemicMass()
        # max height: value of tallest peak
        self.max_height = np.max([self.getSig(x, y) for x in range(self.x_size) for y in range(self.y_size)])
        # for i in range(11):
        #     print(np.percentile([self.getSig(x, y) for x in range(self.x_size) for y in range(self.y_size)], i*10))

    def reportGrid(self):
        """
        Format grid data as {x,y,z} dictionary for plotting
        """
        # Stupidly, 3d_d3 takes y to be height
        # make center of grid (0,0) by offsetting half of map size
        return([{'x': point[0]-self.x_size/2, 'z': point[1]-self.y_size/2, 'y': point[2]} for point in self.grid.flatten().tolist()])

    def getSig(self,x,y):
        """
        INPUT: coordinate
        OUTPUT: epistemic value
        """
        return self.grid[x,y]['height']

    def setSig(self,x,y,newSig):
        self.grid[x,y]['height'] = newSig

    def incrementHeight(self,x,y,amount):
        self.grid[x,y]['height'] += amount

    def incVisit(self,x,y):
        """
        INPUT: coordinate
        """
        self.grid[x,y]['visited'] = 1  #if value is 1, the patch has been visited

    def getPatch(self,x,y):
        """
        INPUT: coordinate
        OUTPUT: reference to the patch object at coordinates (x,y)
        """
        return self.grid[x,y]

    def getMooreNeighborhood(self,x,y):
        """
        Provide info on the 8 patches around a given patch
        INPUT: coordinate
        OUTPUT: Moore neigborhood for that patch
        """
        for ind in range(8):
            x_wrap = (x + self.mooreIndList[ind][0]) % self.x_size
            y_wrap = (y + self.mooreIndList[ind][1]) % self.y_size
            self.mooreArray[ind] = self.grid[x_wrap,y_wrap]
        return self.mooreArray

    def addPerlin(self, noise, smoothing, octaves):
        """
        Add Perlin noise
        INPUT: noise (int): amplitude of noise; smoothing (int): randomness of noise
        """
        pnf = PerlinNoiseFactory(2, octaves=octaves, tile=(self.x_size, self.y_size))
        for x, y in [[x,y] for x in range(self.x_size) for y in range(self.x_size)]:
            # adding noise/x at the end because otherwise 50% of landscape is below 0
            self.incrementHeight(x, y, round(noise*pnf(x/smoothing, y/smoothing), 4))

    def addGaussian(self,x_center,y_center,amplitude,sd):
        """
        Generate some hills (from random normal distribution) at specified location
        """
        gaussian = multivariate_normal(mean=[x_center,y_center], cov=[[sd,0],[0,sd]])
        for x, y in [[x,y] for x in range(self.x_size) for y in range(self.x_size)]:
            # allow wrap around
            height = max([gaussian.pdf([x,y]),gaussian.pdf([x-self.x_size,y]),gaussian.pdf([x,y-self.y_size]),gaussian.pdf([x-self.x_size,y-self.y_size])])
            self.incrementHeight(x,y,round(amplitude*height,4))

    def epistemicMass(self):
        # Current epistemic mass remaining
        return(np.sum(self.grid['height'][self.grid['height']>0]))

    def epistemicMassDiscovered(self):
        return(round(1 - self.epistemicMass()/self.total_epistemic_mass, 4))
