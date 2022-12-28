import numpy as np


def plot_map(plt, sf, x_lim=None, y_lim=None):
    """
    Plot map with lim coordinates
    """
    _id = 0
    for shape in sf.shapeRecords():
        x = [i[0] for i in shape.shape.points[:]]
        y = [i[1] for i in shape.shape.points[:]]
        plt.plot(x, y, 'k')

        if (x_lim is None) & (y_lim is None):
            x0 = np.mean(x)
            y0 = np.mean(y)
            # plt.text(x0, y0, _id, fontsize=10)
        _id += 1

    if (x_lim is not None) & (y_lim is not None):
        plt.xlim(x_lim)
        plt.ylim(y_lim)
