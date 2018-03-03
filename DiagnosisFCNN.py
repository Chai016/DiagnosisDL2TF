# -*- coding: utf-8 -*-
"""
Created on Sat Dec 16 15:09:43 2017
 
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
    mat_sig = np.reshape(signal,[-1, nSampSize]) #����matlab ����д���ļ��ǰ���������,
    mat_lab = np.reshape(labels,[-1, nSampSize])
    mat_sig = mat_sig.T # ת����������ʽ ��������ţ�����ά�ȡ�
    mat_lab = mat_lab.T
    return mat_sig, mat_lab
 
def layer(inputs, in_size, out_size, keep_prob, activation_function=None):
    # ����ȫ�����������
    # inputs������
    # in_size������ά��
    # out_size�����ά��
    # keep_prob��dropout�ı�����
    # activation_function �����
    weights = tf.Variable(tf.random_normal([in_size,out_size],stddev=0.1))
    biases = tf.Variable(tf.zeros([1,out_size]) + 0.01)
    WxPb = tf.matmul(inputs,weights) + biases
    WxPb = tf.nn.dropout(WxPb,keep_prob)
    if activation_function==None:
        outputs = WxPb
    else:
        outputs = activation_function(WxPb)
    return outputs
 
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
   
xs = tf.placeholder(tf.float32,[None, nSig_dim])        # ��������
ys = tf.placeholder(tf.float32,[None, nLab_dim])        # ������ǩ
keep_pro = tf.placeholder(tf.float32)                   # 1-dropout����
 
#FCN ģ�� [nSig_dim:576, 200, 50, nLab_dim:10]
Layer1 = layer(xs, nSig_dim, 200, keep_pro, activation_function=tf.nn.relu)
hiddenL = layer(Layer1, 200, 50, keep_pro, activation_function=tf.nn.relu)
y_pre  = layer(hiddenL, 50, nLab_dim, keep_pro, activation_function=tf.nn.softmax)
 
loss = tf.reduce_mean(tf.reduce_sum(-ys*tf.log(y_pre),reduction_indices=[1]))
train_step = tf.train.AdamOptimizer(1e-4).minimize(loss)
 
correct_pred = tf.equal(tf.argmax(y_pre,1),tf.argmax(ys,1))
accuracy = tf.reduce_mean(tf.cast(correct_pred,tf.float32)) #������ȷ��
 
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
    for step in range(10000):
        intervals = NextBatch(iTrainSetSize, 100) # ÿ�δ��������������ȡ100����������ţ�
        xx = train_x[intervals]
        yy = train_y[intervals]
        sess.run(train_step, feed_dict={xs:xx, ys:yy, keep_pro:0.95})
        if step%100 == 0:
            acc = sess.run(accuracy,feed_dict={xs:xx, ys:yy, keep_pro:1.0})
            print("step: " + "{0:4d}".format(step) + ",  train acc:" + "{:.4f}".format(acc))
    print(sess.run(accuracy,feed_dict={xs:test_x, ys:test_y, keep_pro:1.0}))    