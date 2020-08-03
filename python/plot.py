# print("Loading plotting...")
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np


def format_data(grid):
    """
    INPUT: a landscape grid
    OUTPUT: a dataframe of x,y,height coordinates
    """
    df = pd.DataFrame(grid.ravel(), columns=["x", "y", "height"], dtype="float64")
    return(df)

def plot3d(landscape):
    data = format_data(landscape.grid)
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.plot_trisurf(data['x'], data['y'], data['height'], cmap=plt.cm.viridis, linewidth=0.2)
    plt.show()



#
# # to Add a color bar which maps values to colors.
# surf=ax.plot_trisurf(df['Y'], df['X'], df['Z'], cmap=plt.cm.viridis, linewidth=0.2)
# fig.colorbar( surf, shrink=0.5, aspect=5)
# plt.show()
#
# # Rotate it
# ax.view_init(30, 45)
# plt.show()
#
# # Other palette
# ax.plot_trisurf(df['Y'], df['X'], df['Z'], cmap=plt.cm.jet, linewidth=0.01)
# plt.show()
