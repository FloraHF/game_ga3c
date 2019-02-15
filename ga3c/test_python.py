import numpy as np
a = np.zeros((2,3))
print(type(a))
print(a)
a = np.hstack((a, [3, 4].reshape(2, 1)))
print(a)
a[:,1] = [1, 2]
print(a)
