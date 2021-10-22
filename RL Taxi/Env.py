# Import routines

import numpy as np
import math
import random

# Defining hyperparameters
m = 5 # number of cities, ranges from 1 ..... m
t = 24 # number of hours, ranges from 0 .... t-1
d = 7  # number of days, ranges from 0 ... d-1
C = 5 # Per hour fuel and other costs
R = 9 # per hour revenue from a passenger


class CabDriver():

	def __init__(self):
		"""initialise your state and define your action space and state space"""
		self.action_space = [[i,j] for i in range(m) for j in range(m)]
		self.state_space = [[i,j,k] for i in range(m) for j in range(t) for k in range(d)]
		self.state_init = [np.random.randint(0,m-1), np.random.randint(0,t-1), np.random.randint(0,d-1)]

		# Start the first round
		self.reset()

		self.tot_day = 30
		self.max_time = 24 * 30
		self.size = (m+1) * m-1
		self.tot_time = 0



	## Encoding state (or state-action) for NN input

	def state_encod_arch1(self, state):
		"""convert the state into a vector so that it can be fed to the NN. This method converts a given state into a vector format. Hint: The vector is of size m + t + d."""

		return np.reshape(state,-1)


	# Use this function if you are using architecture-2 
	# def state_encod_arch2(self, state, action):
	#     """convert the (state-action) into a vector so that it can be fed to the NN. This method converts a given state-action pair into a vector format. Hint: The vector is of size m + t + d + m + m."""

		
	#     return state_encod


	## Getting number of requests

	def requests(self, state):
		"""Determining the number of requests basis the location. 
		Use the table specified in the MDP and complete for rest of the locations"""
		location = state[0]
		if location == 0:
			requests = np.random.poisson(2)
		if location == 1:
			requests = np.random.poisson(12)
		if location == 2:
			requests = np.random.poisson(4)
		if location == 3:
			requests = np.random.poisson(7)
		if location == 4:
			requests = np.random.poisson(8)




		if requests >15:
			requests =15

		possible_actions_index = random.sample(range(1, (m-1)*m +1), requests) # (0,0) is not considered as customer request
		actions = [self.action_space[i] for i in possible_actions_index]

		
		actions.append([0,0])

		return possible_actions_index,actions   



	def reward_func(self, state, action, Time_matrix):
		"""Takes in state, action and Time-matrix and returns the reward"""

		(start, time, day ) = state
		(pickup, drop) = action

		if action == [0,0]:
			return - C

		else:
			time_elapsed = Time_matrix[start,pickup, time, day]
			next_t = np.int((time + time_elapsed) % t)
			next_d = np.int((day+ (time_elapsed + time) //t) %d)
			time_drop = Time_matrix[pickup, drop, int(next_t), int(next_d)]
			rev_cost = time_drop * R
			bat_cost = (time_drop + time_elapsed) * C
			reward = rev_cost - bat_cost

			return reward


	def get_next_state(self, time, day,tt=False,Time_matrix=None, pickup=None, drop=None):
		time_elapse = 1

		if tt:
			time_elapse = Time_matrix[pickup, drop, int(time), int(day)]
		total_time = time_elapse
		next_time = np.int((time + time_elapse)%t)
		next_day = np.int((day + (time + time_elapse)//t) % d)

		return time_elapse, total_time, next_time, next_day


	def next_state_func(self, state, action, Time_matrix):
		"""Takes state and action as input and returns next state"""
		(start, time, day) = state
		(pickup, drop) = action

		if action == [0,0]:

			time_elapsed, t_time, get_next_time, get_next_day = self.get_next_state(time, day)
			self.tot_time+= t_time
		else:
			if start == pickup:
				time_elapsed, t_time, get_next_time, get_next_day = self.get_next_state(time, day, tt=True, Time_matrix=Time_matrix,pickup=pickup, drop=drop)
				self.tot_time+=t_time
			else:
				time_to_pickup = Time_matrix[start, pickup, time, day]
				time_next = (time + time_to_pickup) % t
				day_next = ( day + (time+time_to_pickup) //t ) % d
				time = time_next
				day = day_next
				time_elapsed, t_time, get_next_time, get_next_day = self.get_next_state(time, day,tt=True, Time_matrix=Time_matrix, pickup=pickup, drop=drop)
				self.tot_time += time_to_pickup + time_elapsed


		if self.max_time<= self.tot_time: # check for terminal state
			terminal = True
			self.tot_time = 0
		else:
			terminal = False

		next_state = (drop,get_next_time, get_next_day)

		return next_state, terminal

	
	def reset(self):
		return self.action_space, self.state_space, self.state_init
