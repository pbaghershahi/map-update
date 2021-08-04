from viterbi import Viterbi
from rtree import index
from spatialfunclib import *

class GPSMatcher:
    def __init__(self, hmm, emission_probability, constraint_length=10, MAX_DIST=500, priors=None, smallV=0.00000000001):                
        # initialize spatial index
        self.previous_obs = None

        if priors is None:
            priors = dict([(state, 1.0/len(hmm)) for state in hmm])

        # note: creates an Rtree object to compute all the candidates of one node projection
        #  on different edges based threshold bounds of the rtree window
        state_spatial_index = index.Index()
        unlocated_states = []
        id_to_state = {}
        id = 0
        for state in hmm:
            # note: geom is of type edge which is has form ((start_lat, start_lon), (end_lat, end_lon))
            geom = self.geometry_of_state(state)
            if not geom:
                unlocated_states.append(state)
            else:
                ((lat1, lon1), (lat2, lon2)) = geom
                # note: inserts each edge into the Rtree by specific window
                #  consists of the edge start and end coordinates
                state_spatial_index.insert(
                    id,
                    (min(lon1, lon2), min(lat1, lat2), max(lon1, lon2), max(lat1, lat2))
                )
                id_to_state[id] = state
                id += 1
            
        def candidate_states(obs):

            #todo: geometry_of_observation is an ineffetive function which can be ommited
            geom = self.geometry_of_observation(obs)
            if geom == None:
                return list(hmm.keys())
            else:
                lat, lon = geom
                # note: returns set of edge ids which are the candidates of a point selected from specific window
                nearby_states = state_spatial_index.intersection((lon-MAX_DIST/METERS_PER_DEGREE_LONGITUDE,
                                                                  lat-MAX_DIST/METERS_PER_DEGREE_LATITUDE,
                                                                  lon+MAX_DIST/METERS_PER_DEGREE_LONGITUDE,
                                                                  lat+MAX_DIST/METERS_PER_DEGREE_LATITUDE))
                # note: candidate are of the form [edge1, edge2, ...]
                candidates = [id_to_state[id] for id in nearby_states]+unlocated_states
                return candidates

        self.viterbi = Viterbi(hmm, emission_probability,
                               constraint_length=constraint_length,
                               priors=priors,
                               candidate_states=candidate_states,
                               smallV=smallV)

    def step(self, obs, V, p):
        if self.previous_obs != None:
            # todo: interpolated_obs is an ineffetive function which can be ommited
            for int_obs in self.interpolated_obs(self.previous_obs, obs):
                V, p = self.viterbi.step(int_obs, V, p)
        V, p = self.viterbi.step(obs, V, p)
        self.previous_obs = obs
        return V,p

    def interpolated_obs(self, prev, obs):
        return []

    def geometry_of_observation(self, obs):
        return obs

    def geometry_of_state(self, state):
        """ Subclasses should override this method to return the geometry of a given state, typically an edge."""
        if state == 'unknown':
            return None
        else:
            return state
