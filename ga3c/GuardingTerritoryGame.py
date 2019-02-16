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

        # default_actions
        self.defender_default_action = -math.pi
        self.intruder_default_action = -math.pi # TODO randomize func, in Player

        # target
        self.target = Target()

        # defenders and intruders
        self.defenders = []
        self.intruders = []
        self.active = []
        self.captured = []
        self.entered = []

        self.reset()

    def get_state(self):
        x_ = np.array([self.defenders[0].current_x, \
                       self.defenders[0].current_y]).reshape(2, 1)
        for d in np.arange(1, self.dcount):
            x_ = np.hstack((x_, np.array([self.defenders[d].current_x, \
                                          self.defenders[d].current_y]).reshape(2,1)))
        for i in self.active:
            x_ = np.hstack((x_, np.array([self.intruders[i].current_x, \
                                          self.intruders[i].current_y]).reshape(2,1)))
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


    def defender_step(self, id, action=self.defender_default_action):

        # if done, return
        if self.defenders[id].done == True:
            reward = 0
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
            if self._is_captured(self.defenders[id], i):
                i.captured = True
                reward += Config.REWARD_CAPTURE * (1 + self.defenders[id].capture_buffer)
                self.defenders[id].capture_buffer = 0
            if  i.entered == True:
                reward -= Config.REWARD_ENTER * (1 + self.defenders[id].enter_buffer)
                self.defenders[id].enter_buffer = 0

        self._update_intruders()
        done = self.defenders[id].done
        return reward, done

    def intruder_step(self, id, action=self.intruder_default_action):
        done = self.intruders[id].done
        if self.intruders[id].captured_mem or self.intruders[id].entered:
            reward = 0
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
                    if self._is_captured(d, self.intruders[id]):
                        self.intruders[id].captured = True
                        self.intruders[id].captured_mem = True
                        reward -= Config.REWARD_CAPTURE
                        done = True
                        # for the defender's reward calculation
                        # only the capturing defender gets reward
                        d.capture_buffer += 1

                # check if enters
                if self.target.is_in_target(self.intruders[id].current_x, \
                                            self.intruders[id].current_y):
                    self.intruders[id].entered = True
                    reward += Config.REWARD_ENTER
                    done = True
                    # for the defender's reward calculation
                    # every defender gets penalized
                    for d in self.defenders:
                        d.enter_buffer += 1

                self._update_intruders()
                return reward, done

    def _is_captured(self, d, i):
        return not np.sqrt((d.current_x - i.current_x)**2 + \
                        (d.current_y - i.current_y)**2) - \
                        d.capture_range > 0

    def reset(self):
        self.defenders = []
        self.intruders = []
        # for d in np.arange(self.dcount):
        #     self.defenders.append(Defender(id=d))
        # just for 2DSI for now
        self.defenders.append(Defender(id=0, x=-2, y=4))
        self.defenders.append(Defender(id=0, x= 2, y=4))
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

    def get_num_actions(self):
        return len(self.action_space)

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

    def reset(self, x=-Config.WORLD_X_BOUND, y=Config.WORLD_Y_BOUND):
        super().reset(x, y)
        self.captured = False
        self.captured_mem = False
        self.entered = False
