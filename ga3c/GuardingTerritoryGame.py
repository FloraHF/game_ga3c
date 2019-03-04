import sys
if sys.version_info >= (3,0):
    from queue import Queue
else:
    from Queue import Queue

from Config import Config

import numpy as np
import random as rd
import math

import time

from threading import Thread

class GuardingTerritoryGame:
    """This is the game environment for the guarding territory game"""
    def __init__(self):

        # environment parameters
        self.world = WorldMap()
        # number of defenders and intruders
        self.dcount = Config.DEFENDER_COUNT
        self.icount = Config.INTRUDER_COUNT

        self.done_to_int_dic = {True: 0, False: 1}
        self.reset()

    def get_state(self):
        x_ = np.array([[self.defenders[0].x], [self.defenders[0].y],  \
                       [self.done_to_int_dic[self.defenders[0].done]]])
        for d in np.arange(1, self.dcount):
            x_ = np.hstack((x_, np.array([[self.defenders[d].x], [self.defenders[d].y], \
                                          [self.done_to_int_dic[self.defenders[d].done]]])))
        for i in np.arange(0, self.icount):
            x_ = np.hstack((x_, np.array([[self.intruders[i].x], [self.intruders[i].y], \
                                          [self.done_to_int_dic[self.intruders[i].done]]])))
        return x_

    def is_game_done(self):
        # game is over when all players are done
        done = True
        for i in self.intruders:
            done = done and i.done
        for d in self.defenders:
            done = done and d.done
        return done

    def _update_intruders(self):

        # captured
        # print('active intruders: ', self.active)
        new_captured = []
        for i in range(len(self.active)):
            if self.intruders[self.active[i]].captured == True:
                self.captured.append(self.active[i])
                new_captured.append(i)
        if len(new_captured):
            # print('new captured', new_captured)
            for cap in reversed(new_captured):
                self.active.pop(cap)
                # print('remaining intruders:', self.active)
        # entered
        new_entered = []
        for i in range(len(self.active)):
            if self.intruders[self.active[i]].entered == True:
                self.entered.append(self.active[i])
                new_entered.append(i)
        if len(new_entered):
            # print('new entered', new_entered)
            for ent in reversed(new_entered):
                self.active.pop(ent)
                # print('remaining intruders:', self.active)
        # if no active intruders, done
        if not len(self.active):
            for d in self.defenders:
                d.done = True

    def defender_step(self, id, action):

        # settle up reward of the former action
        for i in [self.intruders[active] for active in self.active]:
            self.defenders[id].capture_level_buffer += \
            self.defenders[id].capture_level(i.x, i.y)
            self.defenders[id].intruder_target_level_buffer += \
            self.world.target.contour(i.x, i.y)
        reward = self.defenders[id].clearup_reward()

        # if not done yet, make move
        if not self.defenders[id].done:
            # have to take some actions
            self.defenders[id].time_buffer = 1
            # try to take an action, but can't enter the target
            new_x, new_y = self.defenders[id].try_step(action)
            num_trial = 0
            while (self.world.target.is_in_target(new_x, new_y) or \
                  (not self.world.is_in_world(new_x, new_y))) and \
                    num_trial < 2*self.defenders[id].get_num_actions():
                new_x, new_y = self.defenders[id].try_step(self.defenders[id].random_move())
                num_trial += 1
            if num_trial < 2*self.defenders[id].get_num_actions():
                self.defenders[id].x = new_x
                self.defenders[id].y = new_y
            # check if any active intruder is captured
            new_captured = 0
            for i in [self.intruders[active] for active in self.active]:
                if self._is_captured(self.defenders[id], i) and (not i.captured):
                    new_captured += 1
                    i.captured = True
                    i.done = True
                    self.defenders[id].capture_buffer += 1
            if new_captured > 0:
                self._update_intruders()
        # print('defender', id, 'done:', self.defenders[id].done)
        return reward, self.defenders[id].done

    def intruder_step(self, id, action):

        # settle up reward of the former action
        reward = self.intruders[id].clearup_reward()

        # if not done yet, make move
        if not self.intruders[id].done:
            self.intruders[id].time_buffer = 1
            self.intruders[id].target_level_old = self.intruders[id].target_level_new
            new_x, new_y = self.intruders[id].try_step(action)
            num_trial = 0
            # move, but can't get outside the world map
            while not self.world.is_in_world(new_x, new_y) and \
                    num_trial < 2 * self.intruders[id].get_num_actions():
                new_x, new_y = self.intruders[id].try_step(self.intruders[id].random_move())
                num_trial += 1
            if num_trial < 2*self.intruders[id].get_num_actions():
                self.intruders[id].x = new_x
                self.intruders[id].y = new_y
            # identify how close it is from target
            self.intruders[id].target_level_new = self.world.target.contour(self.intruders[id].x, self.intruders[id].y)
            for d in self.defenders:
                if self._is_captured(d, self.intruders[id]):
                    self.intruders[id].captured = True
                    self.intruders[id].captured_mem = True
                    self.intruders[id].done = True
                    d.capture_buffer += 1
            if self.world.target.is_in_target(self.intruders[id].x, \
                                        self.intruders[id].y):
                self.intruders[id].entered = True
                self.intruders[id].done = True
                # every defender gets penalized
                for d in self.defenders:
                    d.enter_buffer += 1
            if self.intruders[id].done == True:
                self._update_intruders()

        # print('intruder', id, 'capture:', self.intruders[id].captured, 'entered:', self.intruders[id].entered, 'active intrusers', len(self.active))
        return reward, self.intruders[id].done

    def _is_captured(self, d, i):
        return not (np.sqrt((d.x - i.x)**2 + (d.y - i.y)**2) - d.capture_range) > 0

    def reset(self):
        # defenders and intruders
        self.defenders = [] # all the defender objectives
        self.intruders = [] # all the intruder objectives
        self.active = []    # indices of active intruders
                            # (self.active = intruders[self.active].id)
        self.captured = []  # indices of captured intruders
                            # (self.captured = intruders[self.captured].id)
        self.entered = []   # indicesof entered intruders
                            # (self.entered = intruders[self.entered].id)

        # for d in np.arange(self.dcount):
        #     self.defenders.append(Defender(id=d))
        # just for 2DSI for now
        self.defenders.append(Defender(id=0, world=self.world, x=-5, y=7))
        self.defenders.append(Defender(id=1, world=self.world, x= 8, y=4))
        for i in np.arange(self.icount):
            self.intruders.append(Intruder(id=i, world=self.world, x=5, y=10))
        for a in range(self.icount):
            self.active.append(a)
        print('game reset,', len(self.intruders), 'active intruders:', self.active,)

#################################################################################
################################# CLASS WORLDMAP ################################
#################################################################################

class Target:
    """This is a for Target."""
    def __init__(self):
        self.shape = Config.TARGET_TYPE
        if self.shape == 'circle':
            self.r = Config.TARGET_RADIUS
            self.c = Config.TARGET_CENTER

    def contour(self, x, y):
        if self.shape == 'circle':
            level = np.sqrt((x - self.c[0])**2 + (y - self.c[1])**2) - self.r
        return level

    def is_in_target(self, x, y):
        return (self.contour(x, y) < 0)

class WorldMap():
    """docstring for WorldMap."""
    def __init__(self, target=Target()):
        self.x_bound = Config.WORLD_X_BOUND
        self.y_bound = Config.WORLD_Y_BOUND
        self.shape = 'Square'
        self.target = target
        self.max_target_level = self._get_max_target_level()

    def is_in_world(self, x, y):
        if self.shape == 'Square':
            return abs(x)<self.x_bound and abs(y)<self.y_bound

    def _get_max_target_level(self):
        return self.target.contour(self.x_bound, self.y_bound)

#################################################################################
################################## CLASS PLAYER #################################
#################################################################################

class Player:
    """I am a player"""
    def __init__(self, id, dynamic, world, x=-Config.WORLD_X_BOUND, y=Config.WORLD_Y_BOUND):
        self.world = world
        self.id = id
        self.dynamic = dynamic
        self.vmax = None
        self.x = x
        self.y = y
        self.heading = None
        self.action_space = None
        if self.dynamic == 'simple_motion':
            self.accmax = None

        self.time_buffer = 0

        self.done = False

    def try_step(self, action):
        if self.dynamic == 'simple_motion':
            x = self.x + Config.TIME_STEP * self.vmax * math.cos(action)
            y = self.y + Config.TIME_STEP * self.vmax * math.sin(action)
        return x, y

    def get_num_actions(self):
        return len(self.action_space)

    def random_move(self):
        return self.action_space[rd.randint(0, self.get_num_actions()-1)]

    def reset(self, x=-Config.WORLD_X_BOUND, y=Config.WORLD_Y_BOUND):
        self.heading = None
        self.x = x
        self.y = y

################################## CLASS DEFENDER #################################
class Defender(Player):
    """I am a defender."""
    def __init__(self, id, world, x=-Config.WORLD_X_BOUND, y=Config.WORLD_Y_BOUND):
        super().__init__(id, Config.DEFENDER_DYNAMIC, world, x, y)
        self.vmax = Config.DEFENDER_MAX_VELOCITY
        self.action_space = Config.DEFENDER_ACTION_SPACE
        self.capture_range = Config.CAPTURE_RANGE

        self.capture_level_buffer = 0
        self.enter_buffer = 0
        self.capture_buffer = 0
        self.intruder_target_level_buffer = 0

        self.intruder_max_target_level_buffer = self.capture_level(self.world.x_bound, self.world.y_bound)

    def capture_level(self, x, y):
        return np.sqrt((x - self.x)**2 + (y - self.y)**2) - self.capture_range

    def clearup_reward(self):
        # reward for no entering during this step
        # reward = self.time_buffer * Config.PENALTY_TIME_PASS * Config.TIME_STEP
        reward = 0
        # self.time_buffer = 0

        # running reward, for closer to capture, further to target
        reward -= self.capture_level_buffer/self.intruder_max_target_level_buffer
        reward += self.intruder_target_level_buffer/self.world.max_target_level
        self.capture_level_buffer = 0
        self.intruder_target_level_buffer = 0

        # terminal: reward for capture, penalty for entering
        reward += Config.REWARD_CAPTURE * self.capture_buffer
        reward -= Config.REWARD_ENTER * self.enter_buffer
        self.capture_buffer = 0
        self.enter_buffer = 0

        # return
        return reward

    def reset(self, x=-Config.WORLD_X_BOUND, y=Config.WORLD_Y_BOUND):
        super().reset(x, y)
        self.total_capture = 0

################################## CLASS INTRUDER #################################
class Intruder(Player):
    """I am an intruder."""
    def __init__(self, id, world, x=-Config.WORLD_X_BOUND, y=Config.WORLD_Y_BOUND):
        super().__init__(id, Config.INTRUDER_DYNAMIC, world, x, y)
        self.vmax = Config.INTRUDER_MAX_VELOCITY
        self.action_space = Config.INTRUDER_ACTION_SPACE

        self.captured = False
        self.captured_mem = False

        self.entered = False
        self.entered_mem = False

        self.target_level_old = 0
        self.target_level_new = self.world.target.contour(self.x, self.y)

    def clearup_reward(self):
        # penalty for spending the time
        # reward = - self.time_buffer * Config.PENALTY_TIME_PASS * Config.TIME_STEP
        reward = 0
        self.time_buffer = 0
        # reward for entering
        if self.entered and not self.entered_mem:
            reward +=  Config.REWARD_ENTER
            self.entered_mem = True
        # penalty for capture
        if self.captured and not self.captured_mem:
            reward -= Config.REWARD_CAPTURE
        # reward for getting closer to target
        # reward += (self.target_level_old - self.target_level_new)/self.world.max_target_level
        reward -= 3*self.target_level_new/self.world.max_target_level

        return reward

    def reset(self, x=-Config.WORLD_X_BOUND, y=Config.WORLD_Y_BOUND):
        super().reset(x, y)
        self.captured = False
        self.captured_mem = False
        self.entered = False

# #################################################################################
# ################################## CLASS UPDATE #################################
# #################################################################################
# class ThreadIntruderUpdater(Thread):
#     """docstring for ThreadIntruderUpdate."""
#     def __init__(self, game):
#         super(ThreadIntruderUpdater, self).__init__()
#         self.setDaemon(True)
#
#         self.game = game
#         self.intruder_update_q = game.intruder_update_q
#         self.exit_flag = False
#
#     def run(self):
#         while not self.exit_flag:
#             if not self.intruder_update_q.empty():
#                 self.game._update_intruders()
#                 self.intruder_update_q.get()
