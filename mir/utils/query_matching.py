import numpy as np


def __find_min_dist (array1: np.ndarray, array2: np.ndarray) -> np.ndarray:
    """
    find_min_dist finds the nearest in "array2" for each element
    of "array1" ; it returns a numpy array called "ret" so that ret[i] 
    contains the nearest element of array2 for array1[i]

    Disclaimer : this function assumes array1 being the Delta[i] + posting_list[i], 
    where Delta[i] is the difference, in position, between the
    i-th and (i+1)-th query term and posting_list[i] it's the posting list of
    the i-th query term

    usage example :
    assume array1 being :
    [2,5,7]
    assume array2 being :
    [3,8,9]
    the function will return :
    [3,3,8]
    as 3 is the nearest number for the first two elements of array1
    and 8 is the nearest number for the third element of array1
    """
    dig = np.digitize(array1, array2)
    ret = np.zeros(dig.shape[0])
    for idx, element in enumerate(dig) :
        if element == 0 :
            ret[idx] = array2[0]
        if element == array2.shape[0]:
            ret[idx] = array2[array2.shape[0] - 1]
        if element != 0 and element != array2.shape[0] :
            diffs = np.array([array2[element] - array1[idx], array2[element - 1] - array1[idx]]).__abs__().argsort()
            ret[idx] = array2[element - diffs[0]]
    return ret



def __select_best_path (paths: np.ndarray, position: int, delta: int) -> np.ndarray:
    """
    select_best_path discards the "unefficient" paths, meaning paths 
    ending with the same value but not having the lower difference by the last two steps.

    example: 
    let's assume that the passed value for "paths" is the following paths array
    paths = [[1,4,6],
             [0,0,0],
             [0,0,0]]

    to calculate the next step , assuming delta[0] = 1, we run "find_min_dist([2,5,7], [3,8,9])" that will return
    [3,3,8]; so we get 

    paths = [[1,4,6],
             [3,3,8],
             [0,0,0]]

    we can see that both 1 and 4 values select 3 as the next step; however , with delta[0] being +1, we prefer the path 
    [1,3] over [4,3], as the projected value of 1, being 1 + delta[0] = 2 is closer to 3 than 4 + delta[0] = 5.

    after assesing so the function will only keep the column of the preferred path, so in this case the 
    function will return

    paths = [[1,6],
             [3,8],
             [0,0]]         

    """
    values = np.unique(paths[position,:])
    for value in values :
        idxs = np.where(paths[position,:] == value)
        idxs = idxs[0]
        if len(idxs) > 1 :
            for i in range(1, idxs.shape[0]) :
                if value - (paths[position - 1,idxs[i]] + delta) > value - (paths[position -1,idxs[0]] + delta):
                    idxs[0] = idxs[i]
            paths = np.delete(paths, idxs[0], 1)       
        
    return paths

def __score_paths (path: np.ndarray, deltas: np.ndarray) -> int :
    """
    score_paths calculates the "score" of a path, meaning the
    sum of differences between consecutive paths elements minus the corresponding delta value :

    example :
    let's assume having the following path

    [1,5,8] 

    with the following delta values

    [1,2]

    we compute the score by:

    score = [5 - (1 + 1)] + [8 - (5 + 2)] = 4

    """
    score = 0
    for idx, delta in enumerate(deltas) :
        score = score + (path[idx + 1] - (path[idx] + delta)).__abs__()
    return score  


def __final_best_paths(paths, deltas) :
    """
    final_best_paths computes the score of every path in the final paths array :
    this function applies the "score_paths" function to every column of the 
    "paths" array and returns an array containg only the best paths (i.e. the ones
    with lower scores)

    example :

    let's assume having

    paths = [[1,4,6],
             [2,5,7],
             [3,7,8]]

    and 

    deltas [1,1]

    we compute the scores for the paths [1,2,3] , [4,5,7] , [6,7,8] ;
    the scores will be 0, 1 and 0 respectively, so the function will return :

    paths = [[1,6],
             [2,7],
             [3,8]]

    we can also retrieve "min_score" , that will be the final score of the selected paths,
    being 0 in this case         

    """
    n_paths = paths.shape[1]
    scores = np.zeros(n_paths)
    for i in range(n_paths) :
        scores[i] = __score_paths(paths[:,i], deltas)
    min_score = scores.min()   
    idx = np.where(scores == min_score)[0]
    return paths[:,idx] , min_score




def find_best_path (posting_lists: list, deltas: np.ndarray) :
    """
    find_best_path finds the best matching terms positions in the posting lists 
    with respect to the positions of terms in the posting lists ; this function takes as an input
    a lists of postings lists "posting_lists" and the "deltas" array, consisting of
    the difference in position (in the query) between consecutive query terms;

    The function will return an array of which every column will represent the best found
    path amongs the given posting lists with the given deltas.
    """

    #Initialization phase :
        #creation of path array with shape(n° of query terms, n° of posting for the first query term)
    paths = np.zeros((len(posting_lists),len(posting_lists[0])))
    paths[0,:] = np.array(posting_lists[0])

    for i in range(1, len(posting_lists)) :
        paths[i, :] = __find_min_dist(paths[i - 1, :] + deltas[i - 1], np.array(posting_lists[i]))
        __select_best_path(paths, i, deltas[i - 1])

    return __final_best_paths(paths, deltas)