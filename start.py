import matplotlib.pyplot as plt
import tensorflow as tf

from data import Dataset

import numpy as np

# logging.basicConfig(level=logging.DEBUG)

LOG_PATH = 'logs'


def get_figure():
    fig = plt.figure(num=0, figsize=(25, 2.7), dpi=72)
    fig.clf()
    return fig


def fig2rgb_array(fig, expand=True):
    fig.canvas.draw()
    buf = fig.canvas.tostring_rgb()
    ncols, nrows = fig.canvas.get_width_height()
    shape = (nrows, ncols, 3) if not expand else (1, nrows, ncols, 3)
    return np.fromstring(buf, dtype=np.uint8).reshape(shape)


def figure_to_summary(fig):
    image = fig2rgb_array(fig)
    return image_summary.eval(feed_dict={image_placeholder: image})


# Import data
data = Dataset('./data')

PAST_SAMPLES = 1

# Create the model
x = tf.placeholder(tf.float32, [None, 88 * PAST_SAMPLES], name='input')
W = tf.Variable(tf.zeros([88 * PAST_SAMPLES, 88]))
b = tf.Variable(tf.zeros([88]))
y = tf.tanh(tf.matmul(x, W) + b)

# Define loss and optimizer
y_ = tf.placeholder(tf.float32, [None, 88])
loss = tf.reduce_mean(tf.squared_difference(y, y_))
train_step = tf.train.GradientDescentOptimizer(0.5).minimize(loss)

# error rate calculation
masked_prediction = tf.multiply(x, y)
categories = tf.sign(masked_prediction)
errors = tf.cast(tf.not_equal(categories, y_), tf.float32)
num_errors = tf.reduce_sum(errors)
num_notes = tf.reduce_sum(tf.abs(y_))
error_rate = num_errors / num_notes

# Summary
error_rate_summary = tf.summary.scalar('error rate', error_rate)
image_placeholder = tf.placeholder(tf.uint8, fig2rgb_array(get_figure()).shape)
image_summary = tf.summary.image('output', image_placeholder)

writer = tf.summary.FileWriter(LOG_PATH)

with tf.Session() as sess:
    tf.global_variables_initializer().run()

    # Train
    TRAINING_STEPS = 10000

    for i in range(TRAINING_STEPS):
        batch_xs, batch_ys = data.next_batch(1000, past_samples=PAST_SAMPLES)
        _, error_rate_val, result = sess.run([
            train_step,
            error_rate_summary,
            masked_prediction
        ], feed_dict={x: batch_xs, y_: batch_ys})

        # Write output as image to summary
        fig = get_figure()
        plt.imshow(result.T, cmap='seismic', origin='lower', vmin=-1, vmax=1)
        plt.tight_layout()
        writer.add_summary(figure_to_summary(fig), i)

        # Write other values to summary
        writer.add_summary(error_rate_val, i)
