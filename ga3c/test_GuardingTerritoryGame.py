
import GuardingTerritoryGame as GTG
import numpy as np
import math
import csv
from Environment import Environment

gtenv = Environment()

def defender_policy_0(state):
    return -(3/4)*math.pi

def defender_policy_1(state):
    return -(1/4)*math.pi

def intruder_policy(state):
    return -(1/2)*math.pi

# while True:
#     rd0, dd0 = gtenv.defender_step(0, defender_policy_0(gtenv._get_current_state()))
#     rd1, dd1 = gtenv.defender_step(1, defender_policy_1(gtenv._get_current_state()))
#     ri0, di0 = gtenv.intruder_step(0, intruder_policy(gtenv._get_current_state()))
#     # with open("my_output_file.csv",'wb') as f:
#     #     np.savetxt(f, gtenv._get_current_state(), delimiter=",")
#     print("current state: ", type(gtenv._get_current_state()))
#     print(gtenv._get_current_state())
#     if di0:
#         break
# print(gtenv.frame_q.queue)
# print(gtenv._get_current_state())

for i in np.arange(5):
    print(gtenv.step('defender', 0, defender_policy_0(1)))
    gtenv.step('defender', 1, defender_policy_1(1))
    gtenv.step('intruder', 0, intruder_policy(1))

    # print("state: \n", gtenv._get_current_state())
    # print("reward: ", ri0, "done: ", di0)

# rd1, dd1 = gtenv.defender_step(1, defender_policy_1(gtenv._get_current_state()))
# print(gtenv._get_current_state())
#
# ri0, di0 = gtenv.intruder_step(0, intruder_policy(gtenv._get_current_state()))
# print(gtenv._get_current_state())


# print("----------------test class defender-----------------")
# print("initiate a defender with id=3:")
# d = GTG.Defender(3)
# print("id: ", d.id, "x: ", d.current_x, "# cap: ", d.total_capture)
# d.total_capture = 5
# print("set # cap to 5:")
# print("id: ", d.id, "x: ", d.current_x, "# cap: ", d.total_capture)
# d.reset( -9, 8)
# print("reset x to -9:")
# print("id: ", d.id, "x: ", d.current_x, "# cap: ", d.total_capture)

# print("----------------------test class target---------------------")
# t = GTG.Target()
# print("shape: ", t.shape, "radius: ", t.r, "center: ", t.c)
# print(t.contour(2, 1))
# print(t.is_in_target(2, 1))

# print("----------------test class GuardingTerritoryGame--------------")
# g = GTG.GuardingTerritoryGame()
# print("there are", len(g.defenders), "defneders: ", g.defenders[0].id, g.defenders[1].id)
# print("there are", len(g.intruders), "intruders: ", g.intruders[0].id)
#
# print("First defender: id: ", g.defenders[0].id, "done? ", g.defenders[0].done, \
#     "x: ", g.defenders[0].current_x, "# cap: ", g.defenders[0].total_capture)
# g.defender_step(0, 0.4)
# print("First defender moves")
# print("First defender: id: ", g.defenders[0].id, "done? ", g.defenders[0].done, \
#     "x: ", g.defenders[0].current_x, "# cap: ", g.defenders[0].total_capture)
#
# g.intruder_step(0, 0.4)
# print("First intruder moves")
# if not
# print("First intruder: id: ", g.intruders[0].id, "done? ", g.intruders[0].done, \
#     "x: ", g.intruders[0].current_x, "# cap: ", g.intruders[0].captured)
