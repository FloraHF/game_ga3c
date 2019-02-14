from Config import Config
import numpy as np
import math

class GuardingTerritoryGame(self):
    """This is the game environment for the guarding territory game"""
    def __init__(self):

        # environment parameters
        self.x_bound = Config.WORLD_X_BOUND
        self.y_bound = Config.WORLD_Y_BOUND

        # number of defenders and intruders
        self.dcount = Config.DEFENDER_COUNT
        self.icound = Config.INTRUDER_COUNT

        # defenders and intruders
        self.defenders = []
        self.intruders = []
        self.captured = []
        self.entered = []

        # states
        self.previous_state = None
        self.current_state = None
        self.total_reward = 0

        self.reset()

    def state_update(self):
        for d in self.defenders:
            self.current_state[d,1] = d.current_x
            self.current_state[d,2] = d.current_y
        for i in self.active_intruders:
            self.current_state[i+self.dcount,1] = i.current_x
            self.cuurent_state[i+self.dcount,2] = i.current_y

    def _get_current_state(self):
        x_ = self.current_state
        return x_

    def _update_intruders(self):
        # captured
        for i in self.intruders:
            if i.captured == True:
                self.captured.append(i)
                self.intruders.pop(i)
        # entered
        for i in self.intruders:
            if i.entered == True:
                self.entered.append(i)
                self.intruders.pop(i)
        # if no active intruders, done
        if not len(self.intruders):
            for d in self.defenders:
                d.done = True

    def defender_step(self, id, action):

        # if done, return
        if self.defenders[id].done == True:
            return reward=0, done=True

        # try to take an action, but can't enter the target
        new_x, new_y = self.defenders[id].try_step(action)
        if not self.target.is_in_target(new_x, new_y): # not enter
            self.defenders[id].previous_x = self.defenders[id].current_x
            self.defenders[id].previous_y = self.defenders[id].current_y
            self.defenders[id].current_x = new_x
            self.defenders[id].current_y = new_y
        else: # if enterd, try other actions. TODO: random selection
            for a in np.arange(len(self.defenders[id].action_space)):
                new_x, new_y = self.try_step(a)
                if not self.target.is_in_target(new_x, new_y):
                    self.defenders[id].previous_x = self.defenders[id].current_x
                    self.defenders[id].previous_y = self.defenders[id].current_y
                    self.defenders[id].current_x = new_x
                    self.defenders[id].current_y = new_y
                    break
        reward = Config.PENALTY_TIME_PASS

        # check if any intruder is captured or enters target area
        for i in self.intruders:
            if self.is_captured(self.defenders[id], i):
                i.captured = True
                self.onetime_capture += 1
                reward += Config.REWARD_CAPTURE
            if  i.entered = True
                reward -= Config.REWARD_ENTER

        self._update_intruders()
        done = self.defenders[id].done
        return reward, done

    def intruder_step(self, id, action):

        for d in self.defenders:
            if self.is_captured(d, self.intruders[id]):
                self.intruders[id].captured = True
                return reward=0, done=True

        # take an action
        self.intruders[id].previous_x = self.intruders[id].current_x
        self.intruders[id].previous_y = self.intruders[id].current_y
        self.intruders[id].current_x, self.intruders[id].current_y = \
        self.intruders[id].try_step(action)
        reward = -Config.PENALTY_TIME_PASS

        # check if get captured
        for d in self.defenders:
            if self.is_captured(d, self.intruders[id]):
                self.intruders[id].captured = True
                reward -= Config.REWARD_CAPTURE
                done = True

        # check if enters
        if self.target.is_in_target(new_x, new_y):
            self.intruders[id].entered = True
            reward += Config.REWARD_ENTER
            done = True

        return reward, done

    def is_captured(self, d, i):
        return not np.sqrt((d.current_x - i.current_x)^2 + \
                        (d.current_y - i.current_y)^2) - \
                        d.capture_range) > 0

    def check_capture(self):
        for i in self.intruders:
            if i.captured == True:
                self.captured.append(i)
                self.intruders.pop(i)
            else:
                for d in self.defenders:
                    isfree = ( (np.sqrt((d.current_x - i.current_x)^2 + \
                                    (d.current_y - i.current_y)^2) - \
                                    d.capture_range) > 0 )
                    if isfree != True:
                        i.captured = True
                        d.immediate_reward = Config.REWARD_CAPTURE
                    if i.captured = True
                        self.captured.append(i)
                        self.intruders.pop(i)
                        i.immediate_reward = -Config.REWARD_CAPTURE

    def reset(self):
        self.x_bound = Config.WORLD_X_BOUND
        self.y_bound = Config.WORLD_Y_BOUND
        self.dcount = Config.DEFENDER_COUNT
        self.icound = Config.INTRUDER_COUNT
        self.target = Target()
        self.defenders = []
        self.intruders = []
        self.captured = []
        for d in np.arange(self.dcount):
            self.defenders.append(Defender(id=d))
        for i in np.arrange(self.icount):
            self.intruders.append(Intruder(id=i+self.dcount))
        self.previous_state = None
        self.current_state = None

class Target(self):
    """This is a for Target."""
    def __init__(self):
        self.type = Config.TARGET_TYPE
        if self.type = 'circle':
            self.r = Config.TARGET_RADIUS
            self.c = Config.TARGET_CENTER

    def contour(x, y):
        if self.type = 'circle':
            level = np.sqrt((x - self.c[1])^2 + (y - self.c[2])^2) - self.r
        return level

    def is_in_target(x, y):
        return (contour(x, y) < 0)


class Player(self):
    """I am a player"""
    def __init__(self, id, type):
        self.id = id
        self.type = type
        self.vmax = None
        self.previous_x = None
        self.previous_y = None
        self.current_x = -Config.WORLD_X_BOUND
        self.current_y =  Config.WORLD_Y_BOUND
        self.heading = None
        self.target = Target()

        self.done = False
        self.total_reward = 0

    def try_step(action):
        if self.type = 'simple_motion':
            x = self.current_x + Config.TIME_STEP * self.vmax * cos(action)
            y = self.current_y + Config.TIME_STEP * self.vmax * sin(action)
        return x, y

    def reset(self):
        self.previous_x = None
        self.previous_y = None
        self.heading = None
        self.current_x = - Config.WORLD_X_BOUND
        self.current_y =   Config.WORLD_Y_BOUND

class Defender(Player):
    """I am a defender."""
    def __init__(self):
        super(Player, self).__init__(id, type=Config.DEFENDER_DYNAMIC)
        self.vmax = Config.DEFENDER_MAX_VELOCITY
        self.action_space = np.arange(-math.pi, math.pi, 10)
        self.capture_range = Config.CAPTURE_RANGE
        self.total_capture = 0
        self.onetime_capture = 0

class Intruder(Player):
    """I am an intruder."""
    def __init__(self):
        super(Player, self).__init__(id, type=Config.INTRUDER_DYNAMIC)
        self.vmax = Config.INTRUDER_MAX_VELOCITY
        self.action_space = np.arange(-math.pi, math.pi, 10)
        self.captured = False
        self.entered = False
