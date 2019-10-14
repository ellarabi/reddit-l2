import math
import numpy as np
from sklearn import preprocessing
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import dendrogram, linkage
import matplotlib.pyplot as plt
from pylab import rcParams


def verify_symmetric(X):
    for i in range(0, X.shape[0]):
        for j in range(0, X.shape[1]):
            if X[i][j] != X[j][i]: print('very very bad...')
        # end for
    # end for
# end def


def flat_distances(X):
    flat_dist_vec = []
    for i in range(0, X.shape[0]):
        for j in range(i + 1, X.shape[1]):
            flat_dist_vec.append(X[i][j])
        # end for
    # end for

    if len(flat_dist_vec) != (X.shape[0] * (X.shape[1] - 1) / 2): print('wrong flat vector size...')

    return flat_dist_vec
# end def


def distance_matrix(filename):
    names = list()
    distances = list()

    # too little data or non-IE languages
    ignore_countries = [
        'Estonia', 'Georgia', 'Armenia', 'Hungary', 'Moldova', 'Malta', 'Turkey', 'China',
        'Cyprus', 'India', 'Israel', 'Belgium', 'Greece', 'Switzerland', 'Finland',
        'Albania', 'Macedonia', 'Montenegro']

    with open(filename) as fin:
        for line in fin:
            split_line = line.strip().split()
            orig_name = split_line[0]
            targ_name = split_line[1]

            if orig_name in ignore_countries or targ_name in ignore_countries: continue

            distances.append(float(split_line[3]))  # *100)
            names.append(orig_name)
        # end for
    # end with

    # print(len(similarity))
    dim = int(math.sqrt(len(distances)))
    distance_matrix = np.reshape(np.array(distances), (dim, dim))
    verify_symmetric(distance_matrix)

    flat_distances_vec = flat_distances(distance_matrix)
    return flat_distances_vec, sorted(list(set(names)))

# end def


rcParams['figure.figsize'] = 10, 5

if __name__ == '__main__':

    filename = 'pairwise.distance.out'
    dist, names = distance_matrix(filename)

    lm = linkage(dist, method='ward', metric='euclidean')
    dn = dendrogram(lm, leaf_rotation=90, leaf_font_size=10, labels=names, color_threshold=0.65*max(lm[:, 2]))
    #print(len(names))
    plt.show()

# end if



