################################################################################
#
# FILE
#
#    EfficientNetStyle02
#
# DESCRIPTION
#
#    Image classification in PyTorch for ImageNet reduced to 100 classes and
#    down sampled such that the short side is 64 pixels and the long side is
#    >= 64 pixels
#
#    This script achieved a best accuracy of ??.??% on epoch ?? (out of ??) with
#    a learning rate at that epoch of ?.?????? and time required for each epoch
#    of ~ ??? s
#
# INSTRUCTIONS
#
#    1. Go to Google Colaboratory: https://colab.research.google.com/notebooks/welcome.ipynb
#    2. File - New Python 3 notebook
#    3. Cut and paste this file into the cell (feel free to divide into multiple cells)
#    4. Runtime - Change runtime type - Hardware accelerator - GPU
#    5. Runtime - Run all
#
# NOTES
#
#    0. For a mapping of category names to directory names see:
#       https://gist.github.com/aaronpolhamus/964a4411c0906315deb9f4a3723aac57
#
#    1. The original 2012 ImageNet images are down sampled such that their short
#       side is 64 pixels (the other side is >= 64 pixels) and only 100 of the
#       original 1000 classes are kept
#
#    2. A training log is included at the bottom of this file showing training
#       set loss and test set accuracy per epoch
#
#    3. The choice of weight decay scale may be too high, in the future think
#       about reducing and re running the experiment
#
################################################################################

################################################################################
#
# IMPORT
#
################################################################################

# torch
import torch
import torch.nn       as     nn
import torch.optim    as     optim
from   torch.autograd import Function

# torch utils
import torchvision
import torchvision.transforms as transforms

# additional libraries
import os
import urllib.request
import zipfile
import time
import math
import numpy             as np
import matplotlib.pyplot as plt

################################################################################
#
# PARAMETERS
#
################################################################################

# data
DATA_DIR_1        = 'data'
DATA_DIR_2        = 'data/imagenet64'
DATA_DIR_TRAIN    = 'data/imagenet64/train'
DATA_DIR_TEST     = 'data/imagenet64/val'
DATA_FILE_TRAIN_1 = 'Train1.zip'
DATA_FILE_TRAIN_2 = 'Train2.zip'
DATA_FILE_TRAIN_3 = 'Train3.zip'
DATA_FILE_TRAIN_4 = 'Train4.zip'
DATA_FILE_TRAIN_5 = 'Train5.zip'
DATA_FILE_TEST_1  = 'Val1.zip'
DATA_URL_TRAIN_1  = 'https://github.com/arthurredfern/UT-Dallas-CS-6301-CNNs/raw/master/Data/Train1.zip'
DATA_URL_TRAIN_2  = 'https://github.com/arthurredfern/UT-Dallas-CS-6301-CNNs/raw/master/Data/Train2.zip'
DATA_URL_TRAIN_3  = 'https://github.com/arthurredfern/UT-Dallas-CS-6301-CNNs/raw/master/Data/Train3.zip'
DATA_URL_TRAIN_4  = 'https://github.com/arthurredfern/UT-Dallas-CS-6301-CNNs/raw/master/Data/Train4.zip'
DATA_URL_TRAIN_5  = 'https://github.com/arthurredfern/UT-Dallas-CS-6301-CNNs/raw/master/Data/Train5.zip'
DATA_URL_TEST_1   = 'https://github.com/arthurredfern/UT-Dallas-CS-6301-CNNs/raw/master/Data/Val1.zip'
DATA_BATCH_SIZE   = 256
DATA_NUM_WORKERS  = 4
DATA_NUM_CHANNELS = 3
DATA_NUM_CLASSES  = 100
DATA_RESIZE       = 64
DATA_CROP         = 56
DATA_MEAN         = (0.485, 0.456, 0.406)
DATA_STD_DEV      = (0.229, 0.224, 0.225)

# model
MODEL_LEVEL_1_BLOCKS     = 1
MODEL_LEVEL_2_BLOCKS     = 2
MODEL_LEVEL_3_BLOCKS     = 3
MODEL_LEVEL_4_BLOCKS     = 4
MODEL_LEVEL_5A_BLOCKS    = 5
MODEL_LEVEL_5B_BLOCKS    = 1
MODEL_LEVEL_1_CHANNELS   = 16
MODEL_LEVEL_2_CHANNELS   = 24
MODEL_LEVEL_3_CHANNELS   = 40
MODEL_LEVEL_4_CHANNELS   = 80
MODEL_LEVEL_5A_CHANNELS  = 160
MODEL_LEVEL_5B_CHANNELS  = 320
MODEL_LEVEL_DEC_CHANNELS = 1280
MODEL_LEVEL_1_RE         = 4
MODEL_LEVEL_2_RE         = 4
MODEL_LEVEL_3_RE         = 4
MODEL_LEVEL_4_RE         = 4
MODEL_LEVEL_5A_RE        = 4
MODEL_LEVEL_5B_RE        = 4
MODEL_LEVEL_1_F          = 3
MODEL_LEVEL_2_F          = 3
MODEL_LEVEL_3_F          = 3
MODEL_LEVEL_4_F          = 3
MODEL_LEVEL_5A_F         = 3
MODEL_LEVEL_5B_F         = 3
MODEL_LEVEL_1_SE_RATIO   = 4
MODEL_LEVEL_2_SE_RATIO   = 4
MODEL_LEVEL_3_SE_RATIO   = 4
MODEL_LEVEL_4_SE_RATIO   = 4
MODEL_LEVEL_5A_SE_RATIO  = 4
MODEL_LEVEL_5B_SE_RATIO  = 4

# training
TRAIN_LR_MAX              = 0.15 # 0.2
TRAIN_LR_INIT_SCALE       = 0.01
TRAIN_LR_FINAL_SCALE      = 0.001
TRAIN_LR_INIT_EPOCHS      = 5
TRAIN_LR_FINAL_EPOCHS     = 50 # 100
TRAIN_NUM_EPOCHS          = TRAIN_LR_INIT_EPOCHS + TRAIN_LR_FINAL_EPOCHS
TRAIN_LR_INIT             = TRAIN_LR_MAX*TRAIN_LR_INIT_SCALE
TRAIN_LR_FINAL            = TRAIN_LR_MAX*TRAIN_LR_FINAL_SCALE
TRAIN_INTRA_EPOCH_DISPLAY = 10000

# file
FILE_NAME_CHECK      = 'EffNetStyleCheck.pt'
FILE_NAME_BEST       = 'EffNetStyleBest.pt'
FILE_SAVE            = True
FILE_LOAD            = False
FILE_EXTEND_TRAINING = False
FILE_NEW_OPTIMIZER   = False

################################################################################
#
# DATA
#
################################################################################

# create a local directory structure for data storage
if (os.path.exists(DATA_DIR_1) == False):
    os.mkdir(DATA_DIR_1)
if (os.path.exists(DATA_DIR_2) == False):
    os.mkdir(DATA_DIR_2)
if (os.path.exists(DATA_DIR_TRAIN) == False):
    os.mkdir(DATA_DIR_TRAIN)
if (os.path.exists(DATA_DIR_TEST) == False):
    os.mkdir(DATA_DIR_TEST)

# download data
if (os.path.exists(DATA_FILE_TRAIN_1) == False):
    urllib.request.urlretrieve(DATA_URL_TRAIN_1, DATA_FILE_TRAIN_1)
if (os.path.exists(DATA_FILE_TRAIN_2) == False):
    urllib.request.urlretrieve(DATA_URL_TRAIN_2, DATA_FILE_TRAIN_2)
if (os.path.exists(DATA_FILE_TRAIN_3) == False):
    urllib.request.urlretrieve(DATA_URL_TRAIN_3, DATA_FILE_TRAIN_3)
if (os.path.exists(DATA_FILE_TRAIN_4) == False):
    urllib.request.urlretrieve(DATA_URL_TRAIN_4, DATA_FILE_TRAIN_4)
if (os.path.exists(DATA_FILE_TRAIN_5) == False):
    urllib.request.urlretrieve(DATA_URL_TRAIN_5, DATA_FILE_TRAIN_5)
if (os.path.exists(DATA_FILE_TEST_1) == False):
    urllib.request.urlretrieve(DATA_URL_TEST_1, DATA_FILE_TEST_1)

# extract data
with zipfile.ZipFile(DATA_FILE_TRAIN_1, 'r') as zip_ref:
    zip_ref.extractall(DATA_DIR_TRAIN)
with zipfile.ZipFile(DATA_FILE_TRAIN_2, 'r') as zip_ref:
    zip_ref.extractall(DATA_DIR_TRAIN)
with zipfile.ZipFile(DATA_FILE_TRAIN_3, 'r') as zip_ref:
    zip_ref.extractall(DATA_DIR_TRAIN)
with zipfile.ZipFile(DATA_FILE_TRAIN_4, 'r') as zip_ref:
    zip_ref.extractall(DATA_DIR_TRAIN)
with zipfile.ZipFile(DATA_FILE_TRAIN_5, 'r') as zip_ref:
    zip_ref.extractall(DATA_DIR_TRAIN)
with zipfile.ZipFile(DATA_FILE_TEST_1, 'r') as zip_ref:
    zip_ref.extractall(DATA_DIR_TEST)

# transforms
transform_train = transforms.Compose([transforms.RandomResizedCrop(DATA_CROP), transforms.RandomHorizontalFlip(p=0.5), transforms.ToTensor(), transforms.Normalize(DATA_MEAN, DATA_STD_DEV)])
transform_test  = transforms.Compose([transforms.Resize(DATA_RESIZE), transforms.CenterCrop(DATA_CROP), transforms.ToTensor(), transforms.Normalize(DATA_MEAN, DATA_STD_DEV)])

# data sets
dataset_train = torchvision.datasets.ImageFolder(DATA_DIR_TRAIN, transform=transform_train)
dataset_test  = torchvision.datasets.ImageFolder(DATA_DIR_TEST,  transform=transform_test)

# data loader
# dataloader_train = torch.utils.data.DataLoader(dataset_train, batch_size=DATA_BATCH_SIZE, shuffle=True,  num_workers=DATA_NUM_WORKERS, pin_memory=True, drop_last=True)
# dataloader_test  = torch.utils.data.DataLoader(dataset_test,  batch_size=DATA_BATCH_SIZE, shuffle=False, num_workers=DATA_NUM_WORKERS, pin_memory=True, drop_last=False)
dataloader_train = torch.utils.data.DataLoader(dataset_train, batch_size=DATA_BATCH_SIZE, shuffle=True)
dataloader_test  = torch.utils.data.DataLoader(dataset_test,  batch_size=DATA_BATCH_SIZE, shuffle=False)

################################################################################
#
# NETWORK BUILDING BLOCKS
#
################################################################################

# squeeze and excite block
class SEBlock(nn.Module):

    # initialization
    def __init__(self, Ne, Nse):

        # parent initialization
        super(SEBlock, self).__init__()

        # squeeze and excite
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.lin1 = nn.Linear(Ne, Nse, bias=False)
        self.relu = nn.ReLU()
        self.lin2 = nn.Linear(Nse, Ne, bias=False)
        self.sig  = nn.Sigmoid()

    # forward path
    def forward(self, x):

        # batch and channel size
        b, c, _, _ = x.size()

        # squeeze and excite
        y = self.pool(x).view(b, c)
        y = self.lin1(y)
        y = self.relu(y)
        y = self.lin2(y)
        y = self.sig(y).view(b, c, 1, 1)
        return x * y.expand_as(x)

# inverted residual block
class InvResBlock(nn.Module):

    # initialization
    def __init__(self, Ni, Ne, Nse, No, F, S):

        # parent initialization
        super(InvResBlock, self).__init__()

        # identity
        if ((Ni != No) or (S > 1)):
            self.id = False
        else:
            self.id = True

        # residual
        P          = np.floor(F/2).astype(int)
        self.conv1 = nn.Conv2d(Ni, Ne, (1, 1), stride=(1, 1), padding=(0, 0), dilation=(1, 1), groups=1, bias=False, padding_mode='zeros')
        self.bn1   = nn.BatchNorm2d(Ne, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True)
        self.relu1 = nn.ReLU()
        self.conv2 = nn.Conv2d(Ne, Ne, (F, F), stride=(S, S), padding=(P, P), dilation=(1, 1), groups=Ne, bias=False, padding_mode='zeros')
        self.bn2   = nn.BatchNorm2d(Ne, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True)
        self.relu2 = nn.ReLU()
        self.se    = SEBlock(Ne, Nse)
        self.conv3 = nn.Conv2d(Ne, No, (1, 1), stride=(1, 1), padding=(0, 0), dilation=(1, 1), groups=1, bias=False, padding_mode='zeros')
        self.bn3   = nn.BatchNorm2d(No, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True)

    # forward path
    def forward(self, x):

        # residual
        y = self.conv1(x)
        y = self.bn1(y)
        y = self.relu1(y)
        y = self.conv2(y)
        y = self.bn2(y)
        y = self.relu2(y)
        y = self.se(y)
        y = self.conv3(y)
        y = self.bn3(y)

        # identity
        if (self.id == True):
            y = x + y

        # return
        return y

################################################################################
#
# NETWORK
#
################################################################################

# define
class Model(nn.Module):

    # initialization
    def __init__(self,
                 data_num_channels,
                 model_level_1_blocks,  model_level_1_channels,  model_level_1_Re,  model_level_1_F,  model_level_1_se_ratio,
                 model_level_2_blocks,  model_level_2_channels,  model_level_2_Re,  model_level_2_F,  model_level_2_se_ratio,
                 model_level_3_blocks,  model_level_3_channels,  model_level_3_Re,  model_level_3_F,  model_level_3_se_ratio,
                 model_level_4_blocks,  model_level_4_channels,  model_level_4_Re,  model_level_4_F,  model_level_4_se_ratio,
                 model_level_5a_blocks, model_level_5a_channels, model_level_5a_Re, model_level_5a_F, model_level_5a_se_ratio,
                 model_level_5b_blocks, model_level_5b_channels, model_level_5b_Re, model_level_5b_F, model_level_5b_se_ratio,
                 model_level_dec_channels,
                 data_num_classes):

        # parent initialization
        super(Model, self).__init__()

        # stride
        stride1 = 1 # set to 2 for ImageNet
        stride2 = 1 # set to 2 for ImageNet
        stride3 = 2
        stride4 = 2
        stride5 = 2

        # encoder level 1
        self.enc_1 = nn.ModuleList()
        self.enc_1.append(nn.Conv2d(data_num_channels, model_level_1_channels, (3, 3), stride=(stride1, stride1), padding=(1, 1), dilation=(1, 1), groups=1, bias=False, padding_mode='zeros'))
        self.enc_1.append(nn.BatchNorm2d(model_level_1_channels, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True))
        self.enc_1.append(nn.ReLU())
        for n in range(model_level_1_blocks):
            self.enc_1.append(InvResBlock(model_level_1_channels, (model_level_1_channels*model_level_1_Re), (model_level_1_channels*model_level_1_Re//model_level_1_se_ratio), model_level_1_channels, model_level_1_F, 1))

        # encoder level 2
        self.enc_2 = nn.ModuleList()
        self.enc_2.append(InvResBlock(model_level_1_channels, (model_level_1_channels*model_level_2_Re), (model_level_1_channels*model_level_2_Re//model_level_2_se_ratio), model_level_2_channels, model_level_2_F, stride2))
        for n in range(model_level_2_blocks - 1):
            self.enc_2.append(InvResBlock(model_level_2_channels, (model_level_2_channels*model_level_2_Re), (model_level_2_channels*model_level_2_Re//model_level_2_se_ratio), model_level_2_channels, model_level_2_F, 1))

        # encoder level 3
        self.enc_3 = nn.ModuleList()
        self.enc_3.append(InvResBlock(model_level_2_channels, (model_level_2_channels*model_level_3_Re), (model_level_2_channels*model_level_3_Re//model_level_3_se_ratio), model_level_3_channels, model_level_3_F, stride3))
        for n in range(model_level_3_blocks - 1):
            self.enc_3.append(InvResBlock(model_level_3_channels, (model_level_3_channels*model_level_3_Re), (model_level_3_channels*model_level_3_Re//model_level_3_se_ratio), model_level_3_channels, model_level_3_F, 1))

        # encoder level 4
        self.enc_4 = nn.ModuleList()
        self.enc_4.append(InvResBlock(model_level_3_channels, (model_level_3_channels*model_level_4_Re), (model_level_3_channels*model_level_4_Re//model_level_4_se_ratio), model_level_4_channels, model_level_4_F, stride4))
        for n in range(model_level_4_blocks - 1):
            self.enc_4.append(InvResBlock(model_level_4_channels, (model_level_4_channels*model_level_4_Re), (model_level_4_channels*model_level_4_Re//model_level_4_se_ratio), model_level_4_channels, model_level_4_F, 1))

        # encoder level 5
        self.enc_5 = nn.ModuleList()
        self.enc_5.append(InvResBlock(model_level_4_channels, (model_level_4_channels*model_level_5a_Re), (model_level_4_channels*model_level_5a_Re//model_level_5a_se_ratio), model_level_5a_channels, model_level_5a_F, stride5))
        for n in range(model_level_5a_blocks - 1):
            self.enc_5.append(InvResBlock(model_level_5a_channels, (model_level_5a_channels*model_level_5a_Re), (model_level_5a_channels*model_level_5a_Re//model_level_5a_se_ratio), model_level_5a_channels, model_level_5a_F, 1))
        self.enc_5.append(InvResBlock(model_level_5a_channels, (model_level_5a_channels*model_level_5b_Re), (model_level_5a_channels*model_level_5b_Re//model_level_5b_se_ratio), model_level_5b_channels, model_level_5b_F, 1))
        for n in range(model_level_5b_blocks - 1):
            self.enc_5.append(InvResBlock(model_level_5b_channels, (model_level_5b_channels*model_level_5b_Re), (model_level_5b_channels*model_level_5b_Re//model_level_5b_se_ratio), model_level_5b_channels, model_level_5b_F, 1))

        # decoder
        self.dec = nn.ModuleList()
        self.dec.append(nn.Conv2d(model_level_5b_channels, model_level_dec_channels, (1, 1), stride=(1, 1), padding=(0, 0), dilation=(1, 1), groups=1, bias=False, padding_mode='zeros'))
        self.dec.append(nn.BatchNorm2d(model_level_dec_channels, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True))
        self.dec.append(nn.ReLU())
        self.dec.append(nn.AdaptiveAvgPool2d((1, 1)))
        self.dec.append(nn.Flatten())
        self.dec.append(nn.Linear(model_level_dec_channels, data_num_classes, bias=True))

    # forward path
    def forward(self, x):

        # encoder level 1
        for layer in self.enc_1:
            x = layer(x)

        # encoder level 2
        for layer in self.enc_2:
            x = layer(x)

        # encoder level 3
        for layer in self.enc_3:
            x = layer(x)

        # encoder level 4
        for layer in self.enc_4:
            x = layer(x)

        # encoder level 5
        for layer in self.enc_5:
            x = layer(x)

        # decoder
        for layer in self.dec:
            x = layer(x)

        # return
        return x

# create
model = Model(DATA_NUM_CHANNELS,
              MODEL_LEVEL_1_BLOCKS,  MODEL_LEVEL_1_CHANNELS,  MODEL_LEVEL_1_RE,  MODEL_LEVEL_1_F,  MODEL_LEVEL_1_SE_RATIO,
              MODEL_LEVEL_2_BLOCKS,  MODEL_LEVEL_2_CHANNELS,  MODEL_LEVEL_2_RE,  MODEL_LEVEL_2_F,  MODEL_LEVEL_2_SE_RATIO,
              MODEL_LEVEL_3_BLOCKS,  MODEL_LEVEL_3_CHANNELS,  MODEL_LEVEL_3_RE,  MODEL_LEVEL_3_F,  MODEL_LEVEL_3_SE_RATIO,
              MODEL_LEVEL_4_BLOCKS,  MODEL_LEVEL_4_CHANNELS,  MODEL_LEVEL_4_RE,  MODEL_LEVEL_4_F,  MODEL_LEVEL_4_SE_RATIO,
              MODEL_LEVEL_5A_BLOCKS, MODEL_LEVEL_5A_CHANNELS, MODEL_LEVEL_5A_RE, MODEL_LEVEL_5A_F, MODEL_LEVEL_5A_SE_RATIO,
              MODEL_LEVEL_5B_BLOCKS, MODEL_LEVEL_5B_CHANNELS, MODEL_LEVEL_5B_RE, MODEL_LEVEL_5B_F, MODEL_LEVEL_5B_SE_RATIO,
              MODEL_LEVEL_DEC_CHANNELS,
              DATA_NUM_CLASSES)

# enable data parallelization for multi GPU systems
if (torch.cuda.device_count() > 1):
    model = nn.DataParallel(model)
print('Using {0:d} GPU(s)'.format(torch.cuda.device_count()), flush=True)

################################################################################
#
# ERROR AND OPTIMIZER
#
################################################################################

# error (softmax cross entropy)
criterion = nn.CrossEntropyLoss()

# learning rate schedule
def lr_schedule(epoch):

    # linear warmup followed by 1/2 wave cosine decay
    if epoch < TRAIN_LR_INIT_EPOCHS:
        lr = (TRAIN_LR_MAX - TRAIN_LR_INIT)*(float(epoch)/TRAIN_LR_INIT_EPOCHS) + TRAIN_LR_INIT
    else:
        lr = TRAIN_LR_FINAL + 0.5*(TRAIN_LR_MAX - TRAIN_LR_FINAL)*(1.0 + math.cos(((float(epoch) - TRAIN_LR_INIT_EPOCHS)/(TRAIN_LR_FINAL_EPOCHS - 1.0))*math.pi))

    return lr

# optimizer
optimizer = optim.SGD(model.parameters(), lr=0.1, momentum=0.9, dampening=0.0, weight_decay=5e-5, nesterov=True)

################################################################################
#
# TRAINING
#
################################################################################

# start epoch
start_epoch = 0

# specify the device as the GPU if present with fallback to the CPU
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# transfer the network to the device
model.to(device)

# load the last checkpoint
if (FILE_LOAD == True):
    checkpoint = torch.load(FILE_NAME_CHECK)
    model.load_state_dict(checkpoint['model_state_dict'])
    if (FILE_NEW_OPTIMIZER == False):
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    if (FILE_EXTEND_TRAINING == False):
        start_epoch = checkpoint['epoch'] + 1

# initialize the epoch
accuracy_best      = 0
start_time_display = time.time()
start_time_epoch   = time.time()

# cycle through the epochs
for epoch in range(start_epoch, TRAIN_NUM_EPOCHS):

    # initialize epoch training
    model.train()
    training_loss = 0.0
    num_batches   = 0
    num_display   = 0

    # set the learning rate for the epoch
    for g in optimizer.param_groups:
        g['lr'] = lr_schedule(epoch)

    # cycle through the training data set
    for data in dataloader_train:

        # extract a batch of data and move it to the appropriate device
        inputs, labels = data
        inputs, labels = inputs.to(device), labels.to(device)

        # zero the parameter gradients
        optimizer.zero_grad()

        # forward pass, loss, backward pass and weight update
        outputs = model(inputs)
        loss    = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        # update statistics
        training_loss = training_loss + loss.item()
        num_batches   = num_batches + 1
        num_display   = num_display + DATA_BATCH_SIZE

        # display intra epoch results
        if (num_display > TRAIN_INTRA_EPOCH_DISPLAY):
            num_display          = 0
            elapsed_time_display = time.time() - start_time_display
            start_time_display   = time.time()
            print('Epoch {0:3d} Time {1:8.1f} lr = {2:8.6f} avg loss = {3:8.6f}'.format(epoch, elapsed_time_display, lr_schedule(epoch), (training_loss / num_batches) / DATA_BATCH_SIZE), flush=True)

    # initialize epoch testing
    model.eval()
    test_correct = 0
    test_total   = 0

    # no weight update / no gradient needed
    with torch.no_grad():

        # cycle through the testing data set
        for data in dataloader_test:

            # extract a batch of data and move it to the appropriate device
            inputs, labels = data
            inputs, labels = inputs.to(device), labels.to(device)

            # forward pass and prediction
            outputs      = model(inputs)
            _, predicted = torch.max(outputs.data, 1)

            # update test set statistics
            test_total   = test_total + labels.size(0)
            test_correct = test_correct + (predicted == labels).sum().item()

    # epoch statistics
    elapsed_time_epoch = time.time() - start_time_epoch
    start_time_epoch   = time.time()
    print('Epoch {0:3d} Time {1:8.1f} lr = {2:8.6f} avg loss = {3:8.6f} accuracy = {4:5.2f}'.format(epoch, elapsed_time_epoch, lr_schedule(epoch), (training_loss/num_batches)/DATA_BATCH_SIZE, (100.0*test_correct/test_total)), flush=True)

    # save a checkpoint
    if (FILE_SAVE == True):
        torch.save({'epoch': epoch, 'model_state_dict': model.state_dict(), 'optimizer_state_dict': optimizer.state_dict()}, FILE_NAME_CHECK)

    # save the best model
    accuracy_epoch = 100.0 * test_correct / test_total
    if ((FILE_SAVE == True) and (accuracy_epoch >= accuracy_best)):
        torch.save({'epoch': epoch, 'model_state_dict': model.state_dict(), 'optimizer_state_dict': optimizer.state_dict()}, FILE_NAME_BEST)

################################################################################
#
# RESULTS
#
################################################################################
