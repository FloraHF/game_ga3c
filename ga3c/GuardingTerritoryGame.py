from Config import Config
import numpy as np
import math

class GuardingTerritoryGame:
    """This is the game environment for the guarding territory game"""
    def __init__(self):

        # environment parameters
        self.x_bound = Config.WORLD_X_BOUND
        self.y_bound = Config.WORLD_Y_BOUND

        # number of defenders and intruders
        self.dcount = Config.DEFENDER_COUNT
        self.icount = Config.INTRUDER_COUNT

        # target
        self.target = Target()

        # defenders and intruders
        self.defenders = []
        self.intruders = []
        self.active = []
        self.captured = []
        self.entered = []

        # states
        self.previous_state = None
        self.current_state = None

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

        # if no active intruders, done
        if not len(self.active):
            for d in self.defenders:
                d.done = True
            return
        else:
            # captured
            new_captured = []
            for i in self.active:
                if self.intruders[i].captured == True:
                    self.captured.append(i)
                    new_captured.append(i)
            if not len(new_captured):
                for cap in new_captured:
                    self.active.pop(cap)

            # entered
            new_entered = []
            for i in self.active:
                if self.intruders[i].entered == True:
                    self.entered.append(i)
                    new_entered.append(i)
            if not len(new_entered):
                for ent in new_entered:
                    self.active.pop(ent)

            # if no active intruders, done
            if not len(self.active):
                for d in self.defenders:
                    d.done = True


    def defender_step(self, id, action):

        # if done, return
        if self.defenders[id].done == True:
            reward = None
            done = True
            return reward, done

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
        for i in [self.intruders[act] for act in self.active]:
            if self.is_captured(self.defenders[id], i):
                i.captured = True
                reward += Config.REWARD_CAPTURE * (1 + self.capture_buffer)
                self.defenders[id].capture_buffer = 0
            if  i.entered == True:
                reward -= Config.REWARD_ENTER * (1 + self.enter_buffer)
                self.defenders[id].enter_buffer = 0

        self._update_intruders()
        done = self.defenders[id].done
        return reward, done

    def intruder_step(self, id, action):

        if self.intruders[id].captured_mem or self.intruders[id].entered:
            reward = None
            done = True
            # self._update_intruders()
            return reward, done
        else:
            if self.intruders[id].captured:
                reward = -Config.REWARD_CAPTURE
                done = True
                # self._update_intruders()
                return reward, done
            else:
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
                        self.intruders[id].captured_mem = True
                        reward -= Config.REWARD_CAPTURE
                        done = True
                        # for the defender's reward calculation
                        # only the capturing defender gets reward
                        d.capture_buffer += 1

                # check if enters
                if self.target.is_in_target(new_x, new_y):
                    self.intruders[id].entered = True
                    reward += Config.REWARD_ENTER
                    done = True
                    # for the defender's reward calculation
                    # every defender gets penalized
                    for d in self.defenders:
                        d.enter_buffer += 1

                self._update_intruders()
                return reward, done

    def is_captured(self, d, i):
        return not np.sqrt((d.current_x - i.current_x)**2 + \
                        (d.current_y - i.current_y)**2) - \
                        d.capture_range > 0

    def reset(self):
        self.defenders = []
        self.intruders = []
        for d in np.arange(self.dcount):
            self.defenders.append(Defender(id=d))
        for i in np.arange(self.icount):
            self.intruders.append(Intruder(id=i))
        self.active = np.arange(self.icount)
        self.captured = []
        self.entered = []

        self.previous_state = None
        self.current_state = None

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


class Player:
    """I am a player"""
    def __init__(self, id, dynamic, x=-Config.WORLD_X_BOUND, y=Config.WORLD_Y_BOUND):
        self.id = id
        self.dynamic = dynamic
        self.vmax = None
        self.previous_x = None
        self.previous_y = None
        self.current_x = x
        self.current_y = y
        self.heading = None
        if self.dynamic == 'simple_motion':
            self.accmax = None

        self.done = False
        self.total_reward = 0

    def try_step(self, action):
        if self.dynamic == 'simple_motion':
            x = self.current_x + Config.TIME_STEP * self.vmax * math.cos(action)
            y = self.current_y + Config.TIME_STEP * self.vmax * math.sin(action)
        return x, y

    def reset(self, x=-Config.WORLD_X_BOUND, y=Config.WORLD_Y_BOUND):
        self.previous_x = None
        self.previous_y = None
        self.heading = None
        self.current_x = x
        self.current_y = y
        self.total_reward = 0

class Defender(Player):
    """I am a defender."""
    def __init__(self, id, x=-Config.WORLD_X_BOUND, y=Config.WORLD_Y_BOUND):
        super().__init__(id, Config.DEFENDER_DYNAMIC, x, y)
        self.vmax = Config.DEFENDER_MAX_VELOCITY
        self.action_space = np.arange(-math.pi, math.pi, .6)
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
        self.action_space = np.arange(-math.pi, math.pi, .6)
        self.captured = False
        self.captured_mem = False
        self.entered = False

    def reset(self, x=-Config.WORLD_X_BOUND, y=Config.WORLD_Y_BOUND):
        super().reset(x, y)
        self.captured = False
        self.captured_mem = False
        self.entered = False
