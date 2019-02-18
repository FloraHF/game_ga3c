import tensorflow as tf
import numpy as np


x = tf.Variable(tf.random_normal([1,2,6,1]))
y = tf.squeeze(x, axis=[0])

init = tf.global_variables_initializer()

with tf.Session() as sess:
    sess.run(init)

    print("x shape", x.get_shape().as_list())
    print("y shape", y.get_shape().as_list())
