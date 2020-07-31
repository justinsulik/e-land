from perlin import PerlinNoiseFactory
import numpy as np
from scipy.stats import multivariate_normal

print("Loading landscape...")

class Landscape():
    """
    Class describing the epistemic landscape consisting of a number of grid 'patches'
    """

    def __init__(self,Sim):
        """
        Required params: x_size,y_size,depletion,hills,hill_width,noise,smoothing
        """
        # x_size, y_size (int): size of grid FROM ORIGIN IN CENTER
        # depletion (float in [0,1]): depletion rate
        self.x_size = Sim.map_size
        self.y_size = Sim.map_size
        self.depletion = Sim.depletion
        self.res = 10

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
        # centre of the landscape is (0,0)
        self.grid['x'] = np.indices(self.grid.shape)[0]
        self.grid['y'] = np.indices(self.grid.shape)[1]

        # MOORE NEIGHBORHOOD
        # data needed by getMooreNeighborhood to find the 8 patches surrounding a given patch
        self.mooreArray = np.zeros(8,dtype =[('x','i4'),('y','i4'),("height", 'f4'),("visited", 'i4')])
        self.mooreIndList = ((-1,-1),(-1,0),(-1,+1),(0,-1),(0,+1),(+1,-1),(+1,0),(+1,+1))

        # DATA SAVING
        self.archive = []

        # HILLS
        self.addGaussian(10,10,1000,10)
        self.addGaussian(40,50,500,5)

        # NOISE
        self.addPerlin(Sim.noise, Sim.smoothing)

        # EPISTEMIC MASS
        # total amount of epistemic value at start of sim
        self.eMassTotal = np.sum(self.grid['height'])

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
        coord = self.intI(x,y)
        for ind in range(8):
            x_wrap = (x + self.mooreIndList[ind][0]) % self.x_size
            y_wrap = (y + self.mooreIndList[ind][1]) % self.y_size
            self.mooreArray[ind] = self.grid[x_wrap,y_wrap]
        return self.mooreArray

    def addPerlin(self, noise, smoothing):
        """
        Add Perlin noise
        INPUT: noise (int): amplitude of noise; smoothing (int): randomness of noise
        """
        pnf = PerlinNoiseFactory(2, octaves=2, tile=(self.x_size, self.y_size))
        for x, y in [[x,y] for x in range(self.x_size) for y in range(self.x_size)]:
            self.incrementHeight(x,y, round(noise*pnf(x/smoothing, y/smoothing), 4))

    def addGaussian(self,x_center,y_center,amplitude,sd):
        gaussian = multivariate_normal(mean=[x_center,y_center], cov=[[sd,0],[0,sd]])
        for x, y in [[x,y] for x in range(self.x_size) for y in range(self.x_size)]:
            self.incrementHeight(x,y,round(amplitude*gaussian.pdf([x,y]),4))
        #draws = [[int(round(x,0)), int(round(y,0))] for (x,y) in np.random.multivariate_normal([x_center, y_center], [[sd,0],[0,sd]], amplitude)]
        #for x, y in draws:
    #        x_grid = x % self.x_size
    #        y_grid = y % self.y_size
    #        print(x_grid, y_grid)
            # todo: add amounts smaller than 1 depending on just how far from 0?
    #        self.incrementHeight(x_grid,y_grid)



        #self.grid['height'] += amp * np.exp(-1*(s1*deltaX**2 +s2*prod + s3*deltaY**2)) #without the rounding, there's gradient all over the terrain
        #self.grid['height'] += np.round(amp * np.exp(-1*(s1*deltaX**2 +s2*prod + s3*deltaY**2))) + 0.5
        # print(np.round(amp * np.exp(-1*(s1*deltaX**2 +s2*prod + s3*deltaY**2))))
