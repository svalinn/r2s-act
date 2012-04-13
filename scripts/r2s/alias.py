import math
import random

# First we generate our alias table.  The alias table will be constructed of
#  equ-probable bins; each bin contains one or two secondary bins that are
#  created from a supplied list of discrete bins.  The secondary bins are
#  themselves lists with two values: their ?normalized? probability, and their
#  actual value of interst (e.g. energy group?)
# In the alias table, all bins have the same probability: 1/n

def gen_alias_table(bins):
    """Generates and returns an alias table of the supplied discrete bins.
    
    ACTION: Method generates an alias table from the received list bins.
    NOTE: Algorithm used is that described in Prof. Paul Wilson's NE506 lecture
    on random sampling techniques.
    RECEIVES: bins, a list of the form
    [[p1,v1],[p2,v2].... [pN,vN]]
    Where p1 is the probability of value v1 being chosen. p values must be
    already normalized.
    RETURNS: The alias list, 'pairs.'
    """

    pairs = list() # This is our Alias Table

    n = len(bins)
    n_inv = 1.0/len(bins) # self explanatory; saves time.

    # Counting variables
    cnt = 0 # keeps track of the current alias table bin that we are working with
    remainingbins = len(bins)

    bins.sort() # initial sort; sorts by probability (first value of each bin)

    # Alias table generating loop
    while remainingbins > 0:
        #bins.sort() #~ This can be optimized to sort the right end of the array
                    #~ until no more sorting is needed.  Needs custom function
                #~ OR we can simply find where the last bin needs to be moved to.
        bins = _sort_for_alias_table_gen(bins) # update bins so it is fully sorted.

        # If lowest probability bin is less than n_inv...
        if bins[0][0] < n_inv:
            # Add the bin to a new bin in alias table
            pairs.append([bins[0]]) # append the first item in bins

            # Then add the largest bin as the second part of the alias table
            #  and then reduce the largest probability bin by: x - n_inv
            #  where x is the probability of the bin added above.
            pairs[cnt].append([round(n_inv - bins[0][0],5), bins[remainingbins-1][1]])
            bins[remainingbins-1][0] -= (n_inv - bins[0][0])
            bins[remainingbins-1][0] = round(bins[remainingbins-1][0],5)

            bins = bins[1:]
            
        elif bins[0][1] > n_inv:
            pairs.append([[ n_inv,bins[0][1] ]])
            # above: we append [[1/n, bin #]] to alias table
            # then we reduce bins[0] by 1/n, and continue on
            bins[0][0] -= n_inv
            bins = bins[1:]

            pairs[cnt].append([0,0])
            
        else: #~ least probable
            pairs.append([bins[0]])
            bins = bins[1:]
            pairs[cnt].append([0,0])

        # we set the alias bin's two secondary bin probabilities to toal 1
        pairs[cnt][0][0] *= n
        pairs[cnt][1][0] *= n

        remainingbins -= 1
        cnt += 1

    return pairs


# Then we can sample using the alias table

def sample_alias_table(n, pairs):
    """Returns a list of values sampled from an alias table.

    ACTION: Method receives the number of samples to take, n,
    and then generates these using the alias table stored in
    pairs.  The list of samples is store in v, and is returned.
    RECEIVES: n, number of samples to take, and pairs, the alias table.
    RETURNS: v, a list of n samples from the alias table.
    """

    npairs = len(pairs)
    
    v = list()
    for cnt in xrange(n):
        pair = pairs[ int(random.random() * npairs) ]
        if len(pair) == 1:
            v.append(pair[0][1])
        elif random.random() < pair[0][0]:
            v.append(pair[0][1])
        else: v.append(pair[1][1])

    return v


def _sort_for_alias_table_gen(bins):
    """Alias table sorting method that sorts only the last value in a list.
    
    ACTION: Method determines where to move the last item in bins to,
    so that bins is presumably sorted properly by the first value in each
    bin.
    NOTE: This is an internal method that should not need to be call externally.
    RECEIVES: bins, a list of 2-value lists of the form
    [[p1,v1],[p2,v2].... [pN,vN]]
    The list is sorted by the p# values.
    RETURNS: Modified bin is returned.
    """
    
    cnt = len(bins) - 2
    last = len(bins) - 1

    while bins[last][0] < bins[cnt][0]:
        cnt -= 1

    # Insert the last value into the middle of bins so that bins are in order.
    newbins = bins[:cnt+1] + [bins[last]] + bins[cnt+1:last]

    return newbins

