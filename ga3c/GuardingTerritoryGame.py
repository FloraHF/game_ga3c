from Config import Config
import numpy as np
import math
import random as rd

class GuardingTerritoryGame:
    """This is the game environment for the guarding territory game"""
    def __init__(self):

        # environment parameters
        self.world = WorldMap()
        # number of defenders and intruders
        self.dcount = Config.DEFENDER_COUNT
        self.icount = Config.INTRUDER_COUNT

        # default_actions
        self.defender_default_action = -3
        self.intruder_default_action = -3 # TODO randomize func, in Player

        # target
        self.target = Target()

        # defenders and intruders
        self.defenders = [] # all the defender objectives
        self.intruders = [] # all the intruder objectives
        self.active = []    # indices of active intruders
                            # (self.active = intruders[self.active].id)
        self.captured = []  # indices of captured intruders
                            # (self.captured = intruders[self.captured].id)
        self.entered = []   # indicesof entered intruders
                            # (self.entered = intruders[self.entered].id)

        self.reset()

    def get_state(self):
        x_ = np.array([[self.defenders[0].x], \
                       [self.defenders[0].y]])
        for d in np.arange(1, self.dcount):
            x_ = np.hstack((x_, np.array([[self.defenders[d].x], \
                                          [self.defenders[d].y]])))
        for i in self.active:
            x_ = np.hstack((x_, np.array([[self.intruders[i].x], \
                                          [self.intruders[i].y]])))
        return x_

    def _update_intruders(self):
        # captured
        new_captured = []
        for i in range(len(self.active)):
            if self.intruders[self.active[i]].captured == True:
                self.captured.append(self.active[i])
                new_captured.append(i)
        if not len(new_captured):
            for cap in reversed(new_captured):
                self.active.pop(cap)
        # entered
        new_entered = []
        for i in range(len(self.active)):
            if self.intruders[self.active[i]].entered == True:
                self.entered.append(self.active[i])
                new_entered.append(i)
        if not len(new_entered):
            for ent in reversed(new_entered):
                self.active.pop(ent)
        # if no active intruders, done
        if not len(self.active):
            for d in self.defenders:
                d.done = True

    def defender_clearup_reward(self, id):
        # penalty for spending the time
        reward = self.defenders[id].time_buffer * Config.PENALTY_TIME_PASS
        # reward of capture and breaking in
        reward += Config.REWARD_CAPTURE * self.defenders[id].capture_buffer
        reward -= Config.REWARD_ENTER * self.defenders[id].enter_buffer
        # clear up reward buffers
        self.defenders[id].capture_buffer = 0
        self.defenders[id].enter_buffer = 0
        self.defenders[id].time_buffer = 0
        # return
        return reward

    def intruder_clearup_reward(self, id):
        # penalty for spending the time
        reward = - self.intruders[id].time_buffer * Config.PENALTY_TIME_PASS
        # reward for entering
        if self.intruders[id].entered and not self.intruders[id].entered_mem:
            reward +=  Config.REWARD_ENTER
            self.intruders[id].entered_mem = True
        # penalty for capture
        if self.intruders[id].captured and not self.intruders[id].captured_mem:
            reward -= Config.REWARD_CAPTURE
        self.intruders[id].time_buffer = 0
        return reward

    def defender_step(self, id, action):
        # settle up reward of the last action
        reward = self.defender_clearup_reward(id)

        # if done, return
        if not self.defenders[id].done:
            # have to take some actions
            self.defenders[id].time_buffer = 1
            # try to take an action, but can't enter the target
            new_x, new_y = self.defenders[id].try_step(action)
            num_trial = 0
            while self.target.is_in_target(new_x, new_y) and \
                    num_trial < 2*self.defenders[id].get_num_actions():
                new_x, new_y = self.defenders[id].try_step(self.defenders[id].random_move())
                num_trial += 1
            if num_trial < 2*self.defenders[id].get_num_actions():
                self.defenders[id].x = new_x
                self.defenders[id].y = new_y
            # check if any active intruder is captured
            for i in [self.intruders[act] for act in self.active]:
                if self._is_captured(self.defenders[id], i) and (not i.captured):
                    i.captured = True
                    i.done = True
                    self.defenders[id].capture_buffer += 1
            self._update_intruders()

        return reward, self.defenders[id].done

    def intruder_step(self, id, action):

        reward = self.intruder_clearup_reward(id)

        if not self.intruders[id].done:
            self.defenders[id].time_buffer = 1
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

            for d in self.defenders:
                if self._is_captured(d, self.intruders[id]):
                    self.intruders[id].captured = True
                    self.intruders[id].captured_mem = True
                    self.intruders[id].done = True
                    d.capture_buffer += 1
            if self.target.is_in_target(self.intruders[id].x, \
                                        self.intruders[id].y):
                self.intruders[id].entered = True
                self.intruders[id].done = True
                # every defender gets penalized
                for d in self.defenders:
                    d.enter_buffer += 1

        return reward, self.intruders[id].done

    def _is_captured(self, d, i):
        return not np.sqrt((d.x - i.x)**2 + \
                        (d.y - i.y)**2) - \
                        d.capture_range > 0

    def reset(self):
        self.defenders = []
        self.intruders = []
        # for d in np.arange(self.dcount):
        #     self.defenders.append(Defender(id=d))
        # just for 2DSI for now
        self.defenders.append(Defender(id=0, x=-5, y=4))
        self.defenders.append(Defender(id=1, x= 5, y=4))
        for i in np.arange(self.icount):
            self.intruders.append(Intruder(id=i, x=0, y=7))
        self.active = np.arange(self.icount)
        self.captured = []
        self.entered = []

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
    def __init__(self):
        self.x_bound = Config.WORLD_X_BOUND
        self.y_bound = Config.WORLD_Y_BOUND
        self.shape = 'Square'

    def is_in_world(self, x, y):
        if self.shape == 'Square':
            return abs(x)<self.x_bound and abs(y)<self.y_bound

class Player:
    """I am a player"""
    def __init__(self, id, dynamic, x=-Config.WORLD_X_BOUND, y=Config.WORLD_Y_BOUND):
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

class Defender(Player):
    """I am a defender."""
    def __init__(self, id, x=-Config.WORLD_X_BOUND, y=Config.WORLD_Y_BOUND):
        super().__init__(id, Config.DEFENDER_DYNAMIC, x, y)
        self.vmax = Config.DEFENDER_MAX_VELOCITY
        self.action_space = Config.DEFENDER_ACTION_SPACE
        self.capture_range = Config.CAPTURE_RANGE
        self.enter_buffer = 0
        self.capture_buffer = 0

    def reset(self, x=-Config.WORLD_X_BOUND, y=Config.WORLD_Y_BOUND):
        super().reset(x, y)
        self.total_capture = 0

class Intruder(Player):
    """I am an intruder."""
    def __init__(self, id, x=-Config.WORLD_X_BOUND, y=Config.WORLD_Y_BOUND):
        super().__init__(id, Config.INTRUDER_DYNAMIC, x, y)
        self.vmax = Config.INTRUDER_MAX_VELOCITY
        self.action_space = Config.INTRUDER_ACTION_SPACE
        self.captured = False
        self.captured_mem = False
        self.entered = False
        self.entered_mem = False

    def reset(self, x=-Config.WORLD_X_BOUND, y=Config.WORLD_Y_BOUND):
        super().reset(x, y)
        self.captured = False
        self.captured_mem = False
        self.entered = False
