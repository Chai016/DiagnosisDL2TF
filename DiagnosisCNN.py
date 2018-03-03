# -*- coding: utf-8 -*-
"""
Created on Thu Dec  7 20:21:03 2017

@author: shanpo
"""

import numpy as np
import tensorflow as tf

nSampleSize = 24000     # ��������
nSig_dim = 576          # ��������ά��
nLab_dim = 4            # ���ά��

def getdata(nSampSize=24000):
    # ��ȡfloat�Ͷ���������
    signal = np.fromfile('DLdata90singal.raw', dtype=np.float32) 
    labels = np.fromfile('DLdata90labels.raw', dtype=np.float32)
    mat_sig = np.reshape(signal,[-1, nSampSize]) #����matlab ����д���ļ��ǰ��ա��С�����, ��Ҫ���ж�ȡ
    mat_lab = np.reshape(labels,[-1, nSampSize])
    mat_sig = mat_sig.T # ת����������ʽ ��������ţ�����ά�ȡ�
    mat_lab = mat_lab.T
    return mat_sig, mat_lab

def zscore(xx):
    # ������һ������-1��1����������ÿ�����������Թ�һ������
    max1 = np.max(xx,axis=1)    #���л���ÿ��������������������������ֵ
    max1 = np.reshape(max1,[-1,1])  # ������ ->> ������
    min1 = np.min(xx,axis=1)    #���л���ÿ�������������������������Сֵ
    min1 = np.reshape(min1,[-1,1])  # ������ ->> ������
    xx = (xx-min1)/(max1-min1)*2-1
    return xx

def NextBatch(iLen, n_batchsize):
    # iLen: ��������
    # n_batchsize: �������С
    # ����n_batchsize�������������ţ�
    ar = np.arange(iLen)    # ����0��iLen-1������Ϊ1������
    np.random.shuffle(ar)   # ���˳��
    return ar[0:n_batchsize]

def weight_variable(shape):
    # ����Ȩ��
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial)

def bias_variable(shape):
    # ����ƫ��
    initial = tf.constant(0.1, shape=shape)
    return tf.Variable(initial)

def conv2d(x, W):
    # �����
    # stride [1, x_movement:1, y_movement:1, 1]
    return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')

def max_pool_2x2(x):
    # �ػ���
    # stride [1, x_movement:2, y_movement:2, 1]
    return tf.nn.max_pool(x, ksize=[1,2,2,1], strides=[1,2,2,1], padding='SAME')

# ΪNN����placeholder
xs = tf.placeholder(tf.float32,[None,nSig_dim])
ys = tf.placeholder(tf.float32,[None,nLab_dim])
keep_prob = tf.placeholder(tf.float32)

x_image = tf.reshape(xs, [-1, 24, 24, 1])   # 24*24

W_conv1 = weight_variable([5, 5, 1, 32]) # patch 5x5, in size 1, out size 32
b_conv1 = bias_variable([32])
h_conv1 = tf.nn.relu(conv2d(x_image, W_conv1) + b_conv1) # output size 32@24*24
h_pool1 = max_pool_2x2(h_conv1)  # size 32@12*12

## conv2 layer ##
W_conv2 = weight_variable([5,5, 32, 64]) # patch 5x5, in size 32, out size 64 
b_conv2 = bias_variable([64])
h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2) # output size 64@12*12
h_pool2 = max_pool_2x2(h_conv2)     # output size 64@6*6

## fc1 layer ##
W_fc1 = weight_variable([6*6*64, 1024])
b_fc1 = bias_variable([1024])
# [n_samples, 6, 6, 64] ->> [n_samples, 6*6*64]
h_pool2_flat = tf.reshape(h_pool2, [-1, 6*6*64])
h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)
h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)

## fc2 layer ##
W_fc2 = weight_variable([1024, nLab_dim])
b_fc2 = bias_variable([nLab_dim])
y_pre = tf.nn.softmax(tf.matmul(h_fc1_drop, W_fc2) + b_fc2)

# ������
cross_entropy = tf.reduce_mean(-tf.reduce_sum(ys * tf.log(y_pre),
                                              reduction_indices=[1]))       # loss
train_step = tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)

# ��ȷ��
correct_pred = tf.equal(tf.argmax(y_pre, 1), tf.argmax(ys, 1))
accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

mydata = getdata()
iTrainSetSize =  np.floor(nSampleSize*3/4).astype(int) # ѵ����������
iIndex = np.arange(nSampleSize) # ����˳��Ȼ�󻮷�ѵ����������������
train_index = iIndex[0:iTrainSetSize]
test_index = iIndex[iTrainSetSize:nSampleSize]

train_data = mydata[0][train_index]     # ѵ������
train_y = mydata[1][train_index]        # ѵ����ǩ
test_data = mydata[0][test_index]       # ��������
test_y = mydata[1][test_index]          # ���Ա�ǩ

train_x = zscore(train_data)        # ��ѵ�����ݽ��й�һ��
test_x = zscore(test_data)          # �Բ������ݽ��й�һ��

init = tf.global_variables_initializer()

with tf.Session() as sess:
    sess.run(init)
    for step in range(2000):
        intervals = NextBatch(iTrainSetSize, 100) # ÿ�δ��������������ȡ100����������ţ�
        xx = train_x[intervals]
        yy = train_y[intervals]
        sess.run(train_step, feed_dict={xs:xx, ys:yy, keep_prob:0.9})
        if step%100 == 0:
            acc = sess.run(accuracy,feed_dict={xs:xx, ys:yy, keep_prob:1.0})
            print("step: " + "{0:4d}".format(step) + ",  train acc:" + "{:.4f}".format(acc))
    test_acc = sess.run(accuracy,feed_dict={xs:test_x, ys:test_y, keep_prob:1.0})
    print("test acc:" + "{:.4f}".format(test_acc))

# ���   ���98.4%
