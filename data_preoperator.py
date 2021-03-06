SpectralNet_MY/layer.py                                                                             0000664 0001753 0001753 00000025420 13653566050 016461  0                                                                                                    ustar   jacksonpan                      jacksonpan                                                                                                                                                                                                             #进行各个层的定义
import torch
import torch.nn as nn
import math
from data_preoperator import *
import psutil
from sklearn.cluster import SpectralClustering

class FCLear(nn.Module):
    def __init__(self):
        super(FCLear, self).__init__()

        self.fc = torch.nn.Sequential(
            torch.nn.Linear(10,1024,bias=True),
            torch.nn.Dropout(p = 0.5),
            torch.nn.ReLU(),
            torch.nn.Linear(1024,1024,bias=True),
            torch.nn.Dropout(p = 0.5),
            torch.nn.ReLU(),
            torch.nn.Linear(1024,512,bias=True),
            torch.nn.Dropout(p = 0.5),
            torch.nn.ReLU(),
            torch.nn.Linear(512,10,bias=True),
            torch.nn.Softmax()
        )


    def forward(self, x):
        x = self.fc(x)
        return x

class SelfExpressionLayer(torch.nn.Module):
    def __init__(self):
        super(SelfExpressionLayer, self).__init__()
        self.fc = torch.nn.Linear(1024,1024,bias=False)
        # self.fc.weight = torch.nn.Parameter(torch.zeros(1024,1024,dtype=torch.float32))
    def forward(self,x):
        x = self.getCoef().mm(x)
        return x
    
    def getCoef(self):
        return abs(self.fc.weight + torch.transpose(self.fc.weight,1,0))/2

class CNN(nn.Module):
    def __init__(self):
        super(CNN, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(784,500,bias=True),
            nn.ReLU(),
            nn.Linear(500,500,bias=True),
            nn.ReLU(),
            nn.Linear(500,2000,bias=True),
            nn.ReLU(),
            nn.Linear(2000,10,bias=True)
        )

        self.decoder = nn.Sequential(
            nn.Linear(10,2000,bias=True),
            nn.ReLU(),
            nn.Linear(2000,500,bias=True),
            nn.ReLU(),
            nn.Linear(500,500,bias=True),
            nn.ReLU(),
            nn.Linear(500,784,bias=True),
            nn.Sigmoid()
        )

    def forward(self, x):
        encode = self.encoder(x)
        decode = self.decoder(encode)
        return encode, decode

class CNN2(nn.Module):
    def __init__(self):
        super(CNN2, self).__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(1, 16, 3, stride=3, padding=1),  # (b, 16, 10, 10)
            nn.ReLU(True),
            nn.MaxPool2d(2, stride=2),  # (b, 16, 5, 5)
            nn.Conv2d(16, 8, 3, stride=2, padding=1),  # (b, 8, 3, 3)
            nn.ReLU(True),
            nn.MaxPool2d(2, stride=1)  # (b, 8, 2, 2)
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(8, 16, 3, stride=2),  # (b, 16, 5, 5)
            nn.ReLU(True),
            nn.ConvTranspose2d(16, 8, 5, stride=3, padding=1),  # (b, 8, 15, 15)
            nn.ReLU(True),
            nn.ConvTranspose2d(8, 1, 2, stride=2, padding=1),  # (b, 1, 28, 28)
            nn.Tanh()
        )

    def forward(self, x):
        encode = self.encoder(x)
        decode = self.decoder(encode)
        return encode, decode

#用于传统的全连层的图像分类
class DeepAutoEnCoderSelfExpress(nn.Module):
    def __init__(self, batch_size):
        super(DeepAutoEnCoderSelfExpress, self).__init__()

        self.fc = nn.Linear(batch_size, batch_size,bias=False)
        self.cnn = CNN()
        self.cnn.load_state_dict(torch.load("./module/CNN.pkl"))

    def active(self,x):
        return torch.nn.functional.softmax(x)

    def forward(self, x):
        encode = self.cnn.encoder(x)

        Z = encode.view(encode.shape[0],-1)

        # C = cosC(Z,C,30)
        # adjustMatrixC(C)

        ZC = torch.transpose(self.fc(torch.transpose(Z,1,0)),1,0)

        decode = self.cnn.decoder(ZC.view(ZC.shape[0],16,5,5))

        C = self.fc.weight
        return C,Z,ZC,encode,decode

class SiameseNetwork(nn.Module):
     def __init__(self):
         super(SiameseNetwork, self).__init__()
         self.cnn1 = nn.Sequential(
             nn.ReflectionPad2d(1),
             nn.Conv2d(1, 4, kernel_size=3),
             nn.ReLU(inplace=True),
             nn.BatchNorm2d(4),
             nn.Dropout2d(p=.2),
             
             nn.ReflectionPad2d(1),
             nn.Conv2d(4, 8, kernel_size=3),
             nn.ReLU(inplace=True),
             nn.BatchNorm2d(8),
             nn.Dropout2d(p=.2),
 
             nn.ReflectionPad2d(1),
             nn.Conv2d(8, 8, kernel_size=3),
             nn.ReLU(inplace=True),
             nn.BatchNorm2d(8),
             nn.Dropout2d(p=.2),
         )
 
         self.fc1 = nn.Sequential(
             nn.Linear(6272, 500),
             nn.ReLU(inplace=True),
 
             nn.Linear(500, 500),
             nn.ReLU(inplace=True),
 
             nn.Linear(500, 5)
         )
 
     def forward_once(self, x):
         output = self.cnn1(x)
         output = output.view(output.size()[0], -1)
         output = self.fc1(output)
         return output
 
     def forward(self, input1, input2):
         output1 = self.forward_once(input1)
         output2 = self.forward_once(input2)
         return output1, output2


def orthonorm_op(x, epsilon=1e-7):
    '''
    Computes a matrix that orthogonalizes the input matrix x

    x:      an n x d input matrix
    eps:    epsilon to prevent nonzero values in the diagonal entries of x

    returns:    a d x d matrix, ortho_weights, which orthogonalizes x by
                right multiplication
    '''
    x_2 = torch.mm(torch.transpose(x, 1, 0), x)
    x_2 += torch.eye(x.size()[1])*epsilon
    
    L = torch.cholesky(x_2)

    ortho_weights = torch.transpose(torch.inverse(L), 1, 0) * math.sqrt(x.shape[0])
    return ortho_weights

def orthonorm(x,ortho_weights=None):
    x = x.double()
    if ortho_weights == None:
        ortho_weights = orthonorm_op(x)
    return x.mm(ortho_weights).float()

def orthonorm_my(Y):
    _,outputs = torch.max(Y, 1)

    out = torch.zeros(Y.shape[0], Y.shape[1])
    labNum = list()
    for i in range(Y.shape[1]):
        k = len(outputs[outputs == i])
        k = k if k > 0 else 1
        labNum.append(1 / math.sqrt(k))
    for i in range(Y.shape[0]):
        out[i][outputs[i]] = labNum[outputs[i]]
    return Variable(out, requires_grad=True)

class SSpectralNet(torch.nn.Module):
    def __init__(self,inputSize):
        super(SSpectralNet, self).__init__()

        
        self.spectral = SpectralNetNorm(inputSize)


    def forward(self,x):
        Y = orthonorm(self.spectral(x))
        return Y


class SpectralNetNorm(torch.nn.Module):
    def __init__(self,inputSize):
        super(SpectralNetNorm, self).__init__()

        self.fc = torch.nn.Sequential(
            torch.nn.Linear(inputSize,1024,bias=True),
            torch.nn.Dropout(p = 0.3),
            torch.nn.ReLU(),
            torch.nn.Linear(1024,1024,bias=True),
            torch.nn.Dropout(p = 0.3),
            torch.nn.ReLU(),
            torch.nn.Linear(1024,512,bias=True),
            torch.nn.Dropout(p = 0.3),
            torch.nn.ReLU(),
            torch.nn.Linear(512,10,bias=True),
            torch.nn.Tanh()
        )

    def active(self, Y):
        return torch.nn.functional.softmax(Y,dim=1)



    def forward(self, X):
        X = self.fc(X)

        return X

#深度谱聚类层
class SpectralNetLayer(torch.nn.Module):
    def __init__(self,batch_size,L0,alpha,beta,layers,labSize):
        super(SpectralNetLayer, self).__init__()

        #相似度矩阵size
        self.batch_size = batch_size

        #初始化参数
        self.Y0 = 0
        self.L0 = L0
        self.Z0 = 0

        #初始化权重
        # self.W = W

        self.labSize = labSize

        #网络层数
        self.layers = layers

        self.alpha = alpha
        self.beta = beta
        self.eta = 0.01
        self.t = 0.01

        #全连接层
        self.fc = torch.nn.ModuleList()
        self.fc2 = torch.nn.ModuleList()
        for i in range(layers):
            self.fc.append(torch.nn.Linear(self.labSize, self.labSize, bias = False))
            self.fc2.append(torch.nn.Linear(self.labSize, self.labSize, bias = False))

        # #权重初始化
        # for m in self.modules():
        #     if isinstance(m, torch.nn.Linear):
        #         #nn.init.kaiming_normal_(m.weight, mode='fan_out')
        #         #m.weight.data.normal_(0, 1/20)
        #         m.weight = torch.nn.Parameter(self.W.t()) 
        #         #m.weight = torch.nn.Parameter(self.A.t())


    def self_active(self, x):
        return torch.nn.functional.softmax(x,dim=1)
    
    def dicrete(self,x):
        _,index = torch.max(x,1)
        out = torch.zeros(x.shape[0],x.shape[1])
        for i in range(x.shape[0]):
            out[i][index[i]] = 1

        return out

    def calYZL(self, A, D, Yk, Zk, Lk, t, beta):
        #Yk shape is n*c
        #A 是邻接矩阵
        #D 是度矩阵

        U = get_UMatrix(Yk, A, D)
        Yk_1 = Yk
        Zk_1 = Zk
        Lk = torch.transpose(Lk,1,0)
        Lk_1 = Lk
        loss1 = 0
        loss2 = 0
        loss3 = 0
        for i in range(Yk_1.shape[1]):
            M = U[i][i] ** 2 * D - U[i][i] * A
            Yk_1[:,i:i+1] = Yk[:,i:i+1] - t * (M.mm(Zk[:,i:i+1]) + Lk[:,i:i+1] + beta * (Yk[:,i:i+1] - Zk[:,i:i+1]))
            Zk_1[:,i:i+1] = Zk[:,i:i+1] - t * (torch.transpose(M,1,0).mm(Yk_1[:,i:i+1]) - Lk[:,i:i+1] - beta * (Yk_1[:,i:i+1] - Zk[:,i:i+1]))
            Lk_1[:,i:i+1] = Lk[:,i:i+1] + beta * (Yk_1[:,i:i+1] - Zk_1[:,i:i+1])
            
            loss1 += torch.transpose(Yk_1[:,i:i+1],1,0).mm(M).mm(Zk_1[:,i:i+1])
            loss2 += torch.transpose(Lk_1[:,i:i+1],1,0).mm(Yk_1[:,i:i+1] - Zk_1[:,i:i+1])
            loss3 += 1/2 * beta * torch.norm((Yk_1[:,i:i+1]- Zk_1[:,i:i+1]))

        return Yk_1,Zk_1,torch.transpose(Lk_1,1,0),loss1,loss2,loss3


    def changeYZ0(self, Y0):
        self.Y0 = Y0
        self.Z0 = Y0

    def forward(self, C, D):

        Y = list()
        Var = list()
        Z = list()
        L = list()
        Loss1 = list()
        Loss2 = list()
        Loss3 = list()

        for k in range(self.layers):
            info = psutil.virtual_memory()
            print("memory use :", k, info.percent)
            if k == 0 : 
                Yk,Zk,Lk,loss1,loss2,loss3 = self.calYZL(C, D, self.Y0, self.self_active(self.Z0), self.L0, self.t, self.beta)

                Y.append(self.self_active(Yk))
                Z.append(self.self_active(Zk))
                L.append(Lk)
                Loss1.append(loss1)
                Loss2.append(loss2)
                Loss3.append(loss3)
            else :
                Yk,Zk,Lk,loss1,loss2,loss3 = self.calYZL(C, D, Y[k-1], Z[k-1], L[k-1], self.t, self.beta)

                Y.append(self.self_active(Yk))
                Z.append(self.self_active(orthonorm(Zk)))
                L.append(Lk)

                Loss1.append(loss1)
                Loss2.append(loss2)
                Loss3.append(loss3)
            print(Y[k])
            print("layer %d loss1 is %.4f, loss2 is %.4f, loss3 is %.4f" %(k,loss1,loss2,loss3))
        return Y,Z,Loss1,Loss2,Loss3

                                                                                                                                                                                                                                                SpectralNet_MY/loss.py                                                                              0000664 0001753 0001753 00000003075 13654037224 016324  0                                                                                                    ustar   jacksonpan                      jacksonpan                                                                                                                                                                                                             #定义各种loss函数
import torch
import torch.nn.functional as F
from data_preoperator import *
#自我表达层loss函数
def selfExpressionLoss(alpha1,alpha2, Z, C, ZC, input,output):
    IX = input.view(input.shape[0],-1)
    OX = output.view(output.shape[0],-1)
    loss1 = 0.5 * alpha1 * torch.sum( (IX-OX) ** 2)
    loss2 = alpha2 * torch.sum(C ** 2)
    loss3 = 0.5 * torch.sum( (Z - ZC) ** 2)
    loss = loss1 + loss2 + loss3
    # print("loss1 %.4f loss2 %.4f loss3 %.4f totLoss %.4f" %(loss1, loss2,loss3,loss))
    return loss

def kmeansLoss(X,Y):
    Xt = torch.transpose(X,1,0)
    Yt = torch.transpose(Y,1,0)
    loss = torch.norm((Xt - Xt.mm(Y).mm(torch.inverse(Yt.mm(Y) + torch.eye(Y.shape[1]) * 0.0001)).mm(Yt)))
    return loss

def normalSpectralLoss(Y,A):
    loss = torch.norm(squared_distance(Y,W=A).mul(A),1)
    # D = squared_distance(Y)
    # loss = torch.sum(A.mm(D)) / (2 * A.shape[0])
    return loss

def getLoss(lossName):
    if lossName == "normal":
        return normalSpectralLoss
    elif lossName == "kmeansLoss":
        return kmeansLoss


        
class ContrastiveLoss(torch.nn.Module):

    def __init__(self, margin=16.0):
        super(ContrastiveLoss, self).__init__()
        self.margin = margin

    def forward(self, output1, output2, label):
        euclidean_distance = squared_distance(output1,Y=output2)
        loss_contrastive = torch.mean((1-label) * euclidean_distance +     # calmp夹断用法
                                      (label) * torch.clamp(self.margin - euclidean_distance, min=0.0))
        return loss_contrastive




                                                                                                                                                                                                                                                                                                                                                                                                                                                                   SpectralNet_MY/module/                                                                              0000775 0001753 0001753 00000000000 13656523134 016254  5                                                                                                    ustar   jacksonpan                      jacksonpan                                                                                                                                                                                                             SpectralNet_MY/run.py                                                                               0000664 0001753 0001753 00000051662 13654206720 016154  0                                                                                                    ustar   jacksonpan                      jacksonpan                                                                                                                                                                                                             import torch
import torch.nn as nn
from data_preoperator import *
from layer import *
from loss import *
import matplotlib
import numpy 
import time
import sys
import psutil
import random
import torch.nn.functional as F
matplotlib.use('tkagg')
from matplotlib import pyplot as plt 
from sklearn.cluster import SpectralClustering
from sklearn.metrics.pairwise import cosine_similarity
# init parameters
num_epochs = 1500
batch_size = 165
learning_rate = 0.0001
weight_decay = 1e-5
alpha = 0.1
beta = 0.01
layers = 100
labSize = 10


def TrainCNN():
    batch_size = 100
    num_epochs = 40
    train_dataset = downloadData(True)
    train_loader = loadData(train_dataset, batch_size, True)
    print("data  ok")
    module = CNN2()
    
    # 选择损失函数和优化方法
    loss_func = nn.MSELoss()
    optimizer = torch.optim.Adam(module.parameters(), lr=learning_rate, weight_decay=weight_decay)

    for epoch in range(num_epochs):
        for i, (images, labels) in enumerate(train_loader):
            images = get_variable(images)
            labels = get_variable(labels)
            images = F.normalize(images)
            
            encode,decode = module(images)

            # loss = 1/(2*batch_size) * torch.norm((images-decode),2)
            loss = loss_func(images,decode)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
    
            # if (i + 1) % 100 == 0:
            print('Epoch [%d/%d], Iter [%d/%d] Loss: %.4f'
                % (epoch + 1, num_epochs, i + 1, len(train_dataset) // batch_size, loss.item()))
    
    
    # Save the Trained Model
    torch.save(module.state_dict(), './module/CNN2.pkl')
    return module

def TrainSelfExpression(images):

    batch_size = images.shape[0]
    module = DeepAutoEnCoderSelfExpress(batch_size)
    alpha1 = 1
    alpha2 = 1.0 * 10 ** (10 / 10.0 - 3.0)
    loss_func = selfExpressionLoss
    optimizer = torch.optim.Adam(module.parameters(), lr=learning_rate, weight_decay=weight_decay)

    epochs = 1000
    x = numpy.arange(0,epochs)
    y = numpy.ones(epochs)
    for epoch in range(epochs):
        C,Z,ZC,encode,decode = module(images)
        e = 0.1

        loss = loss_func(alpha1,alpha2, Z, C, ZC, images ,decode)
        optimizer.zero_grad()
        loss.backward(retain_graph=True)
        optimizer.step()
        y[epoch] = loss.item()
        if epoch >= 200:
            print('selfExpression Epoch [%d/%d],Loss: %.4f'
                % (epoch + 1, epochs, loss.item()))

    
    # Save the Trained Model
    # torch.save(module.state_dict(), './module/SelfExpression.pkl')
    #print graph
    # plt.title("epoch_loss")
    plt.xlabel("epoch")
    plt.ylabel("loss")
    plt.plot(x,y)
    plt.show()
    return module


def TrainCSVData3(init_Y, X, A, D, labels):
    layer = 1
    batch_size = 7797
    labSize = 26


    A = torch.FloatTensor(A)
    D = torch.FloatTensor(D)
    X = torch.FloatTensor(X)
    labels = torch.FloatTensor(labels[:,0])
    Y0 = torch.FloatTensor(init_Y)
    num_epochs = 1000

    M = D - A


    # selfExpress = TrainSelfExpressionLayer(X, batch_size)
    # A = adjustMatrixC(selfExpress.fc[0].weight)
    print(X.shape)
    A = knn_affinity(X, 100)
    D = torch.triu(A) - torch.triu(A, diagonal=1)
    M = D - A

    loss1 = torch.trace(torch.transpose(Y0,1,0).mm(M).mm(Y0))
    print("initLoss is %.4f" %(loss1.item()))

    _,outputs = torch.max(Y0, 1)
    outputs = outputs + 1
    print_accuracy(outputs.numpy(), labels.numpy(), labSize)



    lossX = numpy.arange(0,num_epochs)
    lossY = numpy.zeros(num_epochs)

    accX = numpy.arange(0,num_epochs)
    accY = numpy.zeros(num_epochs)

    # for layer in range(layers):
    module = SpectralNetNorm(batch_size, labSize, layer)
    optimizer = torch.optim.Adam(module.parameters(), lr=learning_rate, weight_decay=weight_decay)
    
    for epoch in range(num_epochs):
        Yk = orthonorm(module(A, D))

        _,outputs = torch.max(Yk, 1)
        outputs = outputs + 1

        loss = torch.trace(torch.transpose(Yk,1,0).mm(M).mm(Yk))
        # for i in range(layer):
        #     totalLoss += loss[i]

        optimizer.zero_grad()
        loss.backward(retain_graph=True)
        optimizer.step()

        accY[epoch] = print_accuracy(outputs.numpy(), labels.numpy(), labSize)
        lossY[epoch] = loss
        print("layer %d epoch [%d/%d] ACC %.4f loss %.4f" %(layer,epoch,num_epochs,accY[epoch],lossY[epoch]))


    plt.subplot(2,1,1)
    plt.xlabel("layer")
    plt.ylabel("loss")
    plt.plot(lossX,lossY)

    plt.subplot(2,1,2)
    plt.xlabel("layer")
    plt.ylabel("accY")
    plt.plot(accX,accY)


    plt.show()

#单纯ADMM。没有lossBackward
def TrainCSVData2(init_Y, A, D, labels):
    layer = 200
    batch_size = 7797
    labSize = 26


    C = torch.FloatTensor(A)
    D = torch.FloatTensor(D)
    labels = torch.FloatTensor(labels[:,0])
    Y0 = torch.FloatTensor(init_Y)
    L0 = torch.zeros(labSize, batch_size, dtype=torch.float32)


    _,outputs = torch.max(Y0, 1)
    outputs = outputs + 1
    print_accuracy(outputs.numpy(), labels.numpy(), labSize)

    lossfunc = torch.nn.CrossEntropyLoss
    module = SpectralNetLayer(batch_size,L0,alpha,beta,layer+1,labSize)

    module.changeYZ0(Y0)
    Y,Z,loss1,loss2,loss3 = module(C, D)


    loss1X = numpy.arange(0,layer)
    loss1Y = numpy.zeros(layer)
    loss2X = numpy.arange(0,layer)
    loss2Y = numpy.zeros(layer)
    loss3X = numpy.arange(0,layer)
    loss3Y = numpy.zeros(layer)

    accYX = numpy.arange(0,layer)
    accYY = numpy.zeros(layer)

    accZX = numpy.arange(0,layer)
    accZY = numpy.zeros(layer)

    for layers in range(layer):
        Yk = Y[layers]
        Zk = Z[layers]

        _,outputs = torch.max(Yk, 1)
        outputs = outputs + 1

        _,outputsZ = torch.max(Zk,1)
        outputsZ = outputsZ + 1

        # y_true,_ = get_y_preds(outputs.numpy(), labels.numpy(), labSize)
        # entropy = torch.zeros(Yk.shape[0],Yk.shape[1])
        # for i in range(y_true):
        #     entropy[i][y_true[i]] = 1

        #使用公式loss
        # lastLoss = torch.trace(Yt.mm(M).mm(Zk))

        #使用交叉熵loss
        # lastLoss = lossfunc(entropy,labels)
        # print(lastLoss.item())


        # print(batch_size)
        print("layer ", layers)

        accYY[layers] = print_accuracy(outputs.numpy(), labels.numpy(), labSize)
        accZY[layers] = print_accuracy(outputsZ.numpy(), labels.numpy(), labSize)
        loss1Y[layers] = loss1[layers].item()
        loss2Y[layers] = loss2[layers].item()
        loss3Y[layers] = loss3[layers].item()

    plt.subplot(3,1,1)
    plt.title("layer_loss")
    plt.xlabel("layer")
    plt.ylabel("loss")
    plt.plot(loss1X,loss1Y)
    plt.plot(loss2X,loss2Y)
    plt.plot(loss3X,loss3Y)

    plt.subplot(3,1,2)
    plt.title("layer_accY")
    plt.xlabel("layer")
    plt.ylabel("accY")
    plt.plot(accYX,accYY)

    plt.subplot(3,1,3)
    plt.title("layer_accZ")
    plt.xlabel("layer")
    plt.ylabel("accZ")
    plt.plot(accZX,accZY)

    plt.show()

def TrainCSVData(Autoencoder, input, batch_size, labSize):
    # (Yn,Yc,Y0) = readCSV("./data/Yale_32x32_PKN_Ncut_Y_0K.csv")
    # (Md,Mw,M) = readCSV("./data/init_PKN_M.csv")

    num_epochs = 500
    layers = 5000
    eta = 0.01
    x = numpy.arange(1, layers+1)
    y = numpy.zeros(layers)
    L0 = torch.zeros(batch_size, labSize, dtype=torch.float32)

    batch = 10
    numpy.random.shuffle(input)

    Y0 = list()
    C = list()
    D = list()
    l_ture = list()

    info = psutil.virtual_memory()
    print("memory use :", info.percent)
    start = time.clock()
    for i in range(1):
        data = torch.FloatTensor([])
        label = torch.FloatTensor([])
        for k in range(i*batch_size,(i+1)*batch_size):
            data = torch.cat((data,input[k][0]),0)
            label = torch.cat((label,input[k][1]),0)

        data = get_variable(data)
        label = get_variable(label)

        Y0.append(get_Y0Matrix("kmeans", labSize, False, data))
        C.append(adjustMatrixC(TrainSelfExpressionLayer(data,batch_size).fc[0].weight, 0))
        D.append(get_DMatrix(C[i]))
        l_ture.append(label)
        # print(M[i])

        print("init %d param ok" %(i))
    end = time.clock()
    info = psutil.virtual_memory()
    print("load data ok use %ds" %(end-start))
    print("memory use :", info.percent)


    #************************带有lossBackward的**************************************************
    # for layer in range(layers):

    #     lastLoss = 0
    #     outputs = 0

    #     # data = get_variable(torch.FloatTensor(features))

    #     for i in range(num_epochs):

    #         for j in range(batch):
    #             module[layer].changeYZ0(Y0[j])
    #             start = time.clock()
    #             Y,Z = module[layer](C[j], D[j])

    #             Yk = Y[layer]
    #             Zk = Z[layer]
    #             Yt = torch.transpose(Yk, 1, 0)
    #             Zt = torch.transpose(Zk, 1, 0)

    #             lossY = torch.trace(Yt.mm(M[j]).mm(Yk))
    #             lossZ = torch.trace(Zt.mm(M[j]).mm(Zk))
                

    #             lastLoss = 1/2 * lossY + 1/2 * lossZ
    #             _,outputs = torch.max(Yk, 1)
    #             outputs = outputs + 1
    #             optimizer[layer].zero_grad()
    #             lastLoss.backward(retain_graph=True)


    #             optimizer[layer].step()
                
    #             end = time.clock()
    #             info = psutil.virtual_memory()
    #             print("%d step use %ds" %(j,end-start))
    #             print("memory use :", info.percent)

    #             print("run %d" %(j))
    #         # if i % 50 == 0:
    #             print("layer %d epoch [%d/%d] batch[%d/%d] loss %.4f" % (layer, i, num_epochs,j,batch,lastLoss.item()))
        
    #         y[layer] = lastLoss
            
    #         saveCSV("./tempData/Yk_"+str(layer+1)+".csv",numpy.array(outputs.numpy()))

    # plt.title("layer_loss")
    # plt.xlabel("layer")
    # plt.ylabel("loss")
    # plt.plot(x,y)
    # plt.show()


    #***************************不带backward************************************************************
    lossfunc = torch.nn.CrossEntropyLoss
    for layer in range(layers):
        module = SpectralNetLayer(batch_size,L0,alpha,beta,layer+1,labSize)

        module.changeYZ0(Y0[0])
        Y,Z,M = module(C[0], D[0])

        Yk = Y[layer]
        Zk = Z[layer]
        Yt = torch.transpose(Yk, 1, 0)
        Zt = torch.transpose(Zk, 1, 0)


        _,outputs = torch.max(Yk, 1)
        outputs = outputs + 1


        # print(batch_size)
        print("layer ", layer)
        print_accuracy(outputs.numpy(), l_ture[0].numpy(), labSize)
        # print("layer %d loss is %.4f" %(layer,lastLoss.item()))

def TrainSiameseNetwork():
    batch_size = 50
    labSize = 10
    positive_num = 4
    negetive_num = 10
    train_dataset = downloadData(True)
    train_loader = loadData(train_dataset, batch_size, True)
    num_epochs = 300

    module = SiameseNetwork()
    optimizer = torch.optim.Adam(module.parameters(), lr=learning_rate, weight_decay=weight_decay)
    loss_func = ContrastiveLoss()

    lossX = numpy.arange(0,num_epochs)
    lossY = numpy.zeros(num_epochs)

    for i, (images, labels) in enumerate(train_loader):
        if i == num_epochs:
            break
        images = get_variable(images)
        labels = get_variable(labels)
        totLoss = 0

        #使用真实类标初始化正负点对
        neibor = getKneibor(lables=labels)
        isLabels = True
        
        # index = getKneibor(X=data,n_nbrs=batch_size)
        
        for batch in range(batch_size):
            for j in range(batch+1,batch_size):
                label = neibor[batch][j]
                output1,output2 = module(images[batch:batch+1],images[j:j+1])
                output1 = output1.view(output1.shape[0],-1)
                output2 = output2.view(output1.shape[0],-1)
                loss = loss_func(output1,output2, label)
                optimizer.zero_grad()
                loss.backward(retain_graph=True)
                optimizer.step()
                totLoss += loss.item()


        # print("epoch [%d/%d]  loss is %.4f" %(i,len(train_loader),totLoss))
        lossY[i] = totLoss
    torch.save(module.state_dict(), './module/Siamese2.pkl')
    plt.xlabel("layer")
    plt.ylabel("loss")
    plt.plot(lossX,lossY)
    plt.show()


def TrainNumberData():
    #初始化参数
    batch_size = 1024
    tot_size = 60000
    num_epochs = 1
    num_train = 500
    num_display = 10
    labSize = 10
    layers = 3
    fcWeight = 1000
    SpWeight = 10
    useTrainData =  True
    shuffle = True
    dataMethod = "siamese"
    getAMethod = "siamese"
    spectralLossName = "normal"
    n_nbrs = 100
    learning_rate = 1e-5
    weight_decay = 1e-5
    param1 = 1
    param2 = 0
    param3 = 0
    param4 = 0
    #初始化数据
    train_dataset = downloadData(useTrainData)
    train_loader = loadData(train_dataset, tot_size, shuffle)

    #初始化模型
    module = SSpectralNet(5)
    module2 = SSpectralNet(32)
    cnn = CNN()
    cnn.load_state_dict(torch.load("./module/CNN.pkl"))
    cnn2 = CNN2()
    cnn2.load_state_dict(torch.load("./module/CNN2.pkl"))
    siamese = SiameseNetwork()
    siamese.load_state_dict(torch.load("./module/Siamese2.pkl"))

    #初始化优化器
    optimizer = torch.optim.Adam(module.parameters(), lr=learning_rate)
    optimizer2 = torch.optim.Adam(module2.parameters(), lr=learning_rate)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3*num_train, gamma=0.1)
    scheduler2 = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3*num_train, gamma=0.1)

    #初始化描点
    lossX = numpy.arange(0,num_epochs*num_train)
    lossY = numpy.zeros(num_epochs*num_train)
    lossY2 = numpy.zeros(num_epochs*num_train)
    accX = numpy.arange(0,num_epochs*num_train)
    accY = numpy.zeros(num_epochs*num_train)
    accY2 = numpy.zeros(num_epochs*num_train)

    #初始化损失函数
    spectralLossFunc = getLoss(spectralLossName)


    images,labels =  next(iter(train_loader))
    images = get_variable(images)
    images = F.normalize(images)
    labels = get_variable(labels)

    #数据变形
    # images2 = transformData(images,"Conv",cnn2)
    images = transformData(images,dataMethod,siamese)
    for epoch in range(num_epochs):
        totalAcc = 0
        totalLoss = 0
        #打乱数据顺序
        indices = torch.randperm(tot_size)
        images = images[indices]
        # images2 = images2[indices]
        labels = labels[indices]
        x_train = images[:batch_size]
        # x_train2 = images2[:batch_size]
        y_train = labels[:batch_size]

        for i in range(num_train):
            #向前传播
            Y = module(x_train)
            # Y2 = module2(x_train2)

            #计算准确率
            _,outputs = kmeans(labSize, Y.detach().numpy())
            acc = print_accuracy(outputs, y_train.numpy(), labSize)

            # _,outputs2 = kmeans(labSize, Y2.detach().numpy())
            # acc2 = print_accuracy(outputs2, y_train.numpy(), labSize)

            #计算相似度矩阵
            A = get_AMatrix(x_train,getAMethod)

            #计算loss
            spectralLoss = spectralLossFunc(Y,A)
            # spectralLoss2 = spectralLossFunc(Y2,A)

            #反响传播
            optimizer.zero_grad()
            spectralLoss.backward(retain_graph=True)
            optimizer.step()
            scheduler.step()

            # optimizer2.zero_grad()
            # spectralLoss2.backward(retain_graph=True)
            # optimizer2.step()
            # scheduler2.step()

            #打印s
            if i % num_display == 0:
                print("epcho [%d/%d] train[%d/%d] S\loss is %lf,acc is %lf" %(epoch,num_epochs,i,num_train,spectralLoss.item(),acc))
                # print("epcho [%d/%d] train[%d/%d] loss is %lf,loss2 is %lf,acc is %lf,acc2 is %lf" %(epoch,num_epochs,i,num_train,spectralLoss.item(),spectralLoss2.item(),acc,acc2))
            lossY[epoch*num_train + i] = spectralLoss.item()*100
            # lossY2[epoch*num_train + i] = spectralLoss2.item()
            accY[epoch*num_train + i] = acc
            # accY2[epoch*num_train + i] = acc2


    #保存模型    
    torch.save(module.state_dict(), './module/SpectralNetNorm_Tanh.pkl')

    #画图
    plt.subplot(2,1,1)
    plt.xlabel("epoch")
    plt.ylabel("loss")
    plt.plot(lossX,lossY)
    # plt.plot(lossX,lossY2)

    plt.subplot(2,1,2)
    plt.xlabel("epoch")
    plt.ylabel("accY")
    plt.plot(accX,accY)
    # plt.plot(accX,accY2)
    plt.show()

def Test():
    batch_size = 1024
    train_dataset = downloadData(True)
    num_epochs = 500
    train_loader = loadData(train_dataset, batch_size, True)
    num_train = 1
    cnn = CNN()
    cnn.load_state_dict(torch.load("./module/CNN.pkl"))
    sspectral = SSpectralNet()

    lossfunc1 = getLoss("normal")
    lossfunc2 = getLoss("kmeansLoss")
    lossfunc3 = torch.nn.CrossEntropyLoss()
    lossfunc4 = torch.nn.MSELoss()

    optimizer = torch.optim.Adam(sspectral.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=2*num_epochs, gamma=0.1)


    lossX = numpy.arange(0,num_epochs*num_train)
    lossY1 = numpy.zeros(num_epochs*num_train)
    lossY2 = numpy.zeros(num_epochs*num_train)
    lossY3 = numpy.zeros(num_epochs*num_train)
    lossY4 = numpy.zeros(num_epochs*num_train)

    accX = numpy.arange(0,num_epochs*num_train)
    accY = numpy.zeros(num_epochs*num_train)
    accZ = numpy.zeros(num_epochs*num_train)
    for j,(images,labels) in  enumerate(train_loader):
        if j == num_train:
            break
        images = get_variable(images)
        labels = get_variable(labels)
        images = F.normalize(images)
        images = images.view(images.shape[0],-1)
        for i in range(num_epochs):
            encode,decode,Y,Z = sspectral(images,cnn)

            A = get_AMatrix(encode.detach(),"c_k",n_nbrs=200)
            _,outputsY = kmeans(10, Y.detach().numpy())
            # _,outputsY = torch.max(Y, 1)
            # _,outputsZ = kmeans(10, Z.detach().numpy())
            _,outputsZ = torch.max(Z, 1)

            loss1 = lossfunc1(Y,A)
            loss2 = lossfunc2(encode,Z)

            # outputsZ,_ = get_y_preds(outputs,outputsY, 10)
            targetY = torch.LongTensor(outputsY)
            loss3 = lossfunc3(Z,targetY)
            loss4 = lossfunc4(images,decode)
            P1 = 1
            P2 = 1
            P3 = 0
            P4 = 0
            loss = P1*loss1 + P2*loss2 + P3*loss3 + P4*loss4


            print(loss)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            scheduler.step()

            AccY = print_accuracy(outputsY, labels.numpy(), 10)
            AccZ = print_accuracy(outputsZ, labels.numpy(), 10)
            print(j,i,loss1.item(),loss2.item(),loss3.item(),loss4.item(),AccY,AccZ)
            lossY1[j*num_epochs + i] = loss1.item()
            lossY2[j*num_epochs + i] = loss2.item()
            lossY3[j*num_epochs + i] = loss3.item()
            lossY4[j*num_epochs + i] = loss4.item()
            accY[j*num_epochs + i] = AccY
            accZ[j*num_epochs + i] = AccZ

    # show_img(images.view(images.shape[0],1,28,28),batch_size)
    #画图
    plt.subplot(5,1,1)
    plt.xlabel("layer")
    plt.ylabel("Y")
    plt.plot(lossX,lossY1)
    # plt.plot(SlossX,SlossY)

    plt.subplot(5,1,2)
    plt.xlabel("layer")
    plt.ylabel("Z")
    plt.plot(lossX,lossY2)

    plt.subplot(5,1,3)
    plt.xlabel("layer")
    plt.ylabel("cross")
    plt.plot(lossX,lossY3)

    plt.subplot(5,1,4)
    plt.xlabel("layer")
    plt.ylabel("norm")
    plt.plot(lossX,lossY4)

    plt.subplot(5,1,5)
    plt.xlabel("layer")
    plt.ylabel("accY")
    plt.plot(accX,accY)
    plt.plot(accX,accZ)
    plt.show()



if __name__ == "__main__":
    #***************文本数据训练***************************
    # features,A,D,C,init_Y,labels = readMat("./data/data/Isolet_7797.mat")
    # TrainCSVData3(init_Y, features, A, D, labels)
    # TrainCNN()
    # TrainSiameseNetwork()
    # TrainAutoEncoderLayer(features)

    #加载训练好的编码器
    # cnn = CNN()
    # cnn.load_state_dict(torch.load("./module/CNN.pkl"))
    # encode,_ = AutoEncoderLayer(torch.FloatTensor(features))

    #deepAE
    # TrainSelfExpressionLayer()

    #加载训练好的siamese
    # siamese = SiameseNetwork()
    # siamese.load_state_dict(torch.load("./module/Siamese.pkl"))

    # TrainCSVData(AutoEncoderLayer)
    TrainNumberData() 
    # Test()

    
    # print(C[0][0])
    # print(D)
    



    # eta = 0.01
    # A = torch.FloatTensor(A)
    # M = get_MMatirx(C=A, parm=eta, D=torch.FloatTensor(D))
    #离散初始化Y0
    # Y0 = torch.FloatTensor(init_Y)


    #连续初始化Y0
    # Y0 = get_Y0Matrix("kmeans", C[0][0], False, encode)


    # input = list()


    # for i in range(encode.shape[0]):
    #     input.append((encode[i:i+1,:],torch.FloatTensor(labels[i])))

    # TrainCSVData(AutoEncoderLayer, input, 700, 26)



    #*****************************画图*****************

    # x = numpy.arange(1,6)
    # y = numpy.array([0.03091,0.02988,0.03001,0.05592,0.03912])
    # graph(x,y,"layer","ACC","ACC_layer")



                                                                                  SpectralNet_MY/Siamese.py                                                                           0000664 0001753 0001753 00000001464 13646263261 016735  0                                                                                                    ustar   jacksonpan                      jacksonpan                                                                                                                                                                                                             import torch.utils.data as data
import torch
import h5py

class DataFromH5File(data.Dataset):
    def __init__(self, filepath):
        h5File = h5py.File(filepath, 'r')
        self.hr = h5File['hr']
        self.lr = h5File['lr']
        
    def __getitem__(self, idx):
        label = torch.from_numpy(self.hr[idx]).float()
        data = torch.from_numpy(self.lr[idx]).float()
        return data, label
    
    def __len__(self):
        assert self.hr.shape[0] == self.lr.shape[0], "Wrong data length"
        return self.hr.shape[0]

trainset = DataFromH5File("./pretrain_weight/ae_mnist_weights.h5")
train_loader = data.DataLoader(dataset=trainset, batch_size=1024, shuffle=True,  num_workers=8, pin_memory=True)

for step, (lr, hr) in enumerate(train_loader):
    print(lr.shape)
    print(hr.shape)
    break                                                                                                                                                                                                            SpectralNet_MY/test.py                                                                              0000664 0001753 0001753 00000020744 13654164625 016333  0                                                                                                    ustar   jacksonpan                      jacksonpan                                                                                                                                                                                                             from data_preoperator import *
from layer import *
from run import *
import torch.nn.functional as F
from sklearn.metrics.pairwise import cosine_similarity
def testAcc():
    a = numpy.array([2,2,1,1,3,3])
    b = numpy.array([3,3,2,2,1,1])
    labSize = 3
    print_accuracy(a,b,labSize)

def testCNN():
    module = CNN()
    module.load_state_dict(torch.load("./module/CNN.pkl"))

    batch_size = 100
    train_dataset = downloadData(True)
    train_loader = loadData(train_dataset, batch_size, True)

    for i, (images, labels) in enumerate(train_loader):
        images = get_variable(images)
        labels = get_variable(labels)
        images = F.normalize(images)
        images = images.view(images.shape[0],-1)
        if i == 0:
            encoder,decoder = module(images)
            decoder = decoder.view(decoder.shape[0],1,28,28)
            show_img(decoder,batch_size)
            break

def testGetAMatrix():
    a = torch.FloatTensor([[1,2,3],[2,3,4],[3,4,5]])
    print("input is ")
    print(a)
    print("output is")
    out = get_AMatrix(a, "fc")
    print(out)

def testSelfExpression():
    batch_size = 100
    train_dataset = downloadData(True)
    train_loader = loadData(train_dataset, batch_size, True)

    cnn = CNN()
    cnn.load_state_dict(torch.load("./module/CNN.pkl"))


    for i, (images, labels) in enumerate(train_loader):
        images = get_variable(images)
        labels = get_variable(labels)
        if i == 0:
            encoder,decoder = cnn(images)
            # show_img(encoder,batch_size)

            Z = images.view(images.size(0), -1)
    
            module = TrainSelfExpressionLayer(Z,batch_size)

            images = images.view(images.size(0),-1)

            C = adjustMatrixC(module.fc[0].weight)

            ZC = C.mm(images)

            ZC = ZC.view(ZC.size(0),1,28,28)
            images = images.view(images.size(0),1,28,28)
            show_img(images, batch_size)
            show_img(ZC, batch_size)
            break

def testKnn():
    a = torch.FloatTensor([[1,2,3],[2,3,4],[4,5,6]])
    print("input X is")
    print(a)
    b = knn_affinity(a,2)
    print("output is")
    print(b)

def testGetKneibor():
    isLabels = True
    if isLabels:
        print("labels")
        labels = torch.FloatTensor([1,1,2,3,2,1])
        print("input is")
        print(labels)
        b = getKneibor(lables=labels)
        print("outputs")
        print(b)

        print("1 and 0 is neibor?")
        print(isNeibor(b,isLabels,1,0))
        print("2 and 1 is neibor?")
        print(isNeibor(b,isLabels,2,1))
        print("2 and 0 is neibor?")
        print(isNeibor(b,isLabels,2,4))
    else:
        print("unlabels")
        a = torch.FloatTensor([[1,2,3],[2,3,4],[4,5,6]])
        print("input X is")
        print(a)
        b = getKneibor(a,2)
        print("output is")
        print(b)
        print("1 and 0 is neibor?")
        print(isNeibor(b,1,0))
        print("2 and 1 is neibor?")
        print(isNeibor(b,2,1))
        print("2 and 0 is neibor?")
        print(isNeibor(b,2,0))

def testSiamese():
    batch_size = 10
    train_dataset = downloadData(True)
    train_loader = loadData(train_dataset, batch_size, True)

    siamese = SiameseNetwork()
    siamese.load_state_dict(torch.load("./module/Siamese2.pkl"))
    loss_func = ContrastiveLoss()
    images, labels = next(iter(train_loader))
    images = get_variable(images)
    labels = get_variable(labels)

    # kneibor = getKneibor(X=images.view(images.shape[0],-1),n_nbrs=batch_size)
    # print(kneibor)
    neibor = getKneibor(lables=labels)
    input = torch.FloatTensor([])
    for n in range(images.shape[0]):
        input = torch.cat((input,siamese.forward_once(images[n:n+1])),0)

    A = torch.zeros(images.shape[0],images.shape[0])
    for n in range(images.shape[0]):
        for m in range(images.shape[0]):
            A[n][m] = loss_func(input[n:n+1],input[m:m+1],1)
    print(A)
    A = torch.clamp(16 - squared_distance(input), min=0.0)
    print(A)
    show_img(images,batch_size)

def testsquared_distance():
    a = torch.FloatTensor([[1,2,3],[2,3,4],[3,4,5]])
    print(a)
    print("test loss")
    a1 = a[0:1,:]
    a2 = a[2:3,:]
    print("input1 is", a1)
    print("input2 is", a2)
    loss_func = ContrastiveLoss()
    print("ContrastiveLoss label 1 is", loss_func(a1,a2,1))
    print("ContrastiveLoss label 0 is", loss_func(a1,a2,0))
    print("totalLoss is")
    W = SiameseLoss(a,1)
    print("label 1 is")
    print(W)
    print("label 0 is")
    W = SiameseLoss(a,1)
    print(W)

def test():
    # Y = torch.FloatTensor([[1,2,3],[2,3,4],[3,4,5]]).numpy()
    # W = cosine_similarity(Y,Y)
    # print(W)
    # Y = torch.FloatTensor([[1,2,3],[2,3,4],[3,4,5]])
    Y = torch.rand(3,3)
    print(Y)
    # W = torch.sort(-Y,dim=1)
    # indices = torch.randperm(2)
    # print(indices)
    # print(Y[indices])
    # print(Y)
    # print(W)
    print(thrC(Y,0.5))


def testOrthonorm():
    a = torch.randn(5,4)
    print("print input")
    print(a)
    print("w")
    w = orthonorm(a)
    print(w)
    print("wt*w")
    print(torch.transpose(w,1,0).mm(w))

def testKmeans():
    input = torch.FloatTensor([[1,2,3],[2,3,4],[3,4,5]])
    k = 2
    cluster_center,labels = kmeans(k, input)
    print(labels)

def testTorchKtop():
    batch_size = 20
    train_dataset = downloadData(True)
    train_loader = loadData(train_dataset, batch_size, True)
    images,labels = next(iter(train_loader))
    data = images.view(images.shape[0],-1)
    D = data.numpy()
    W = cosine_similarity(D,D)
    print(W)
    W = torch.FloatTensor(W)
    nn = torch.topk(W,batch_size)
    qq = torch.randn(batch_size,batch_size)
    nnInd = nn[1]
    qq[nnInd] = 0
    # nn = getKneibor(X=data,n_nbrs=batch_size)
    print(nnInd)
    print(qq)
    show_img(images,batch_size)

def testSelfExpress():
    batch_size = 100
    train_dataset = downloadData(True)
    train_loader = loadData(train_dataset, batch_size, True)

    images, labels = next(iter(train_loader))
    images = get_variable(images)
    images = F.normalize(images)
    labels = get_variable(labels)
    
    module = TrainSelfExpression(images)
    C,Z,ZC,encode,decode = module(images)
    C = thrC(C,0.3)
    print("len C!=0")
    print(len(C[C!=0]))
    C[C > 0] = 1
    C = C.int()
    print("len C > 0")
    print(len(C[C>0]))
    R = getKneibor(lables=labels)
    R[R == 0] = -1
    Dif = C - R
    print("len R>0")
    print(len(R[R>0]))
    err1 = len(Dif[Dif==2])
    print("C is 1 R is 0")
    print(err1)
    err2 = len(Dif[Dif==-1])
    print("C is 0 R is 1")
    print(err2)
    err = err1 + err2

    succ = len(Dif[Dif==0])
    print("R is 1")
    print(len(R[R==1]))
    print("C == R")
    print(succ)

    rate = float(succ) / (err + succ)
    print(rate)
    show_img(decode,batch_size)

def Test():
    batch_size = 100
    labSize = 10
    layers = 3
    num_epochs = 30
    test_dataset = downloadData(True)
    test_loader = loadData(test_dataset, batch_size, True)
    cnn = CNN2()
    cnn.load_state_dict(torch.load("./module/CNN2.pkl"))
    # norm_k_os = SpectralNetNorm()
    # norm_k_os.load_state_dict(torch.load("./module/SpectralNetNorm_Tanh.pkl"))

    totAcc = 0
    for i,(images,labels) in enumerate(test_loader):
        images = get_variable(images)
        labels = get_variable(labels)
        images = F.normalize(images)
        show_img(images,batch_size)
        encode,decode = cnn(images)
        show_img(decode,batch_size)
        
def Test():
    batch_size = 100
    labSize = 10
    layers = 3
    num_epochs = 30
    test_dataset = downloadData(True)
    test_loader = loadData(test_dataset, batch_size, True)

    totAcc = 0
    for i,(images,labels) in enumerate(test_loader):
        images = get_variable(images)
        labels = get_variable(labels)
        images = F.normalize(images)
        show_img(images,batch_size)
        encode,decode = cnn(images)
        show_img(decode,batch_size)

def TestEmbed():
    # batch_size = 1024
    # labSize = 10
    # layers = 3
    # num_epochs = 30
    # test_dataset = downloadData(True)
    # test_loader = loadData(test_dataset, batch_size, True)
    # images,labels = next(iter(test_loader))
    # x = embed_data(images.numpy())
    cnn = CNN()
    cnn.load_state_dict(torch.load('./pretrain_weight/ae_mnist_weights.h5'))
if __name__ == "__main__":
    # testAcc()
    # testCNN()
    # testGetAMatrix()
    # testSelfExpression()
    # testKnn()
    # testGetKneibor()
    testSiamese()
    # testsquared_distance()
    # testOrthonorm()
    # test()
    # testKmeans()
    # testTorchKtop()
    # testSelfExpress()
    # Test()
    # TestEmbed()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            