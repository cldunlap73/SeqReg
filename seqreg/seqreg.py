from tensorflow.keras.models import model_from_json
from matplotlib import pyplot as plt
import pandas as pd
import os
import numpy as np
import json
import joblib
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import DotProduct, WhiteKernel
import tensorflow as tf
from sklearn.metrics import r2_score, mean_squared_error
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
import pkg_resources

def create_data(x,y,t, sl, stride,seqout=False):
    flag=0
    if len(x.shape)< 2:
        flag=1
        x=np.expand_dims(x,axis=-1)
    N, feat = x.shape
    num_sequences = (N - sl) // stride + 1
    xnew = np.empty((num_sequences, sl, feat))
    if seqout==False:
        ynew = np.empty((num_sequences))
    elif seqout:
        y=np.expand_dims(y,axis=-1)
        ynew=np.empty((num_sequences,sl,1))
    time=np.empty((num_sequences))
    for i in range(num_sequences):
        start_idx = i * stride
        xnew[i] = x[start_idx:start_idx + sl]
        if seqout==False:
            ynew[i]=y[start_idx+sl-1]
        elif seqout:
            ynew[i]=y[start_idx:start_idx+sl]
        time[i]=t[start_idx+sl-1]
    if flag==1:
        xnew=xnew.squeeze(-1)
    return xnew,ynew,time

def compute_fft(signal, dx):
    N=len(signal) # subtract mean
    time=np.array([i*dx for i in range(N)])
    y_f=np.fft.fft(signal-np.mean(signal))
    x_f=np.linspace(0.0, 1.0/(2.0*dx), N//2)
    y_f=2.0/N *np.abs(y_f[:N//2])
    return x_f,y_f

def LoadDataFromFolder(folderpath, xname, yname,tname="Time", datatype="Value"):
    files=[f for f in os.listdir(folderpath) if f.endswith(".csv")]
    xds,yds,timeds=[],[],[]
    for i in range(len(files)):
        df=pd.read_csv(folderpath+'/'+files[i], header=0)
        if datatype =="Value":
            xds.append(df[xname].tolist())
        elif datatype =="txtFilePath":
            xds.append([np.loadtxt(folderpath+file_path) for file_path in df[xname]])
        yds.append(df[yname].tolist())
        timeds.append(df[tname].tolist())
    return xds,yds,timeds

def TranformImages(xds):
    #load images perform pca transformation
    # return new sequence
    return 1

def PrepareData(x,y,time,seqlen,stride,dt,fft=False,seqout=False):
    # Perform rolling sampling
    x1,y1,t1=create_data(np.array(x[0]), np.array(y[0]), np.array(time[0]), seqlen, stride,seqout=seqout)
    for i in range(len(x)-1):
        x2,y2,t2=create_data(np.array(x[i+1]),np.array(y[i+1]),np.array(time[i+1]), seqlen,stride,seqout=seqout)
        x1=np.vstack((np.array(x1),np.array(x2)))
        if seqout==False:
            y1=np.concatenate((y1,y2))
        elif seqout:
            y1=np.vstack((np.array(y1),np.array(y2)))
        t1=np.concatenate((t1,t2))

    if fft:
        N=x1.shape[-1]
        mean_=x1-np.mean(x1, axis=-1,keepdims=True)
        freqs=np.fft.fft(mean_,axis=-1)
        freqs=2.0 / N * np.abs(freqs[...,:N // 2])
        x1=freqs
    return x1,y1,t1


def Model(modelname, savemodelpath,train=False, xtrain=None,ytrain=None):

    # Load json file containing all models
    modelspathname=pkg_resources.resource_filename('seqreg','Models/models.json')
    with open(modelspathname,"r") as f:
        config=json.load(f)

    if modelname not in config:
        raise ValueError(f"Model {modelname} not found in {config_path}.")

    # Specify which model and load parameters
    model_config=config[modelname]
    model_type=model_config["framework"]

    if model_type == "tensorflow":
        # Load model from JSON File
        modelpathname=pkg_resources.resource_filename('seqreg',model_config["path"])
        with open(modelpathname,"r") as json_file:
            tf_model_json=json_file.read()
        model=model_from_json(tf_model_json)

        if train==True:
            train_params = model_config["train_params"]
            # train model and save weights based on name
            model.compile(
                optimizer=train_params["optimizer"],
                loss=train_params["loss"],
            )

            checkpoint = ModelCheckpoint(savemodelpath, monitor='val_loss', verbose=1, save_best_only=True,
                                         mode='min', save_weights_only=True)
            early_stop = EarlyStopping(monitor='val_loss', patience=100, verbose=3)
            callbacks=[checkpoint,early_stop]
            model.fit(xtrain,ytrain,validation_split=0.1,epochs=train_params["epochs"],callbacks=callbacks)
            return model
        elif train ==False:
            model.load_weights(savemodelpath)
            return model
            # Load weights already defined
    elif model_type == "sklearn":
        # Load and train scikit-learn model
        if train ==True:
            model_class = globals().get(model_config["type"])
            if model_class is None:
                raise ValueError(f"Unknown scikit-learn model class: {model_config['type']}")

            params=model_config.get("params",{})

            if isinstance(params.get("kernel"),str):
                kernel_expression=params["kernel"]
                params["kernel"]=eval(kernel_expression)

            model = model_class(**params)
            model.fit(xtrain, ytrain)
            # Save model
            joblib.dump(model,savemodelpath)
            return model
        elif train ==False:
            model=joblib.load(savemodelpath)
            return model

def Analyze(model, savepath, xtest,ytest, time, xname="X Data", yname="Y Data",seqout=False,showplot=True):
    # Plots (predicted vs true) (predicted & true vs time)
    if not os.path.exists(savepath):
        os.makedirs(savepath)

    pred=model.predict(xtest)
    if seqout:
        pred=pred[:,-1,0]
        ytest=ytest[:,-1,0]
    min_val,max_val=np.amin(ytest), np.amax(ytest)
    plt.plot(ytest,pred,'o', color="green", markersize=6, markeredgewidth=.3,markeredgecolor='black')
    plt.plot([min_val,max_val],[min_val,max_val], color='black')
    plt.xlabel("True "+ yname)
    plt.ylabel("Predicted "+yname)
    plt.savefig(f"{savepath}/true_vs_pred.png", bbox_inches='tight',transparent=False)
    if showplot:
        plt.show()
    plt.clf()

    plt.plot(time, ytest, color='black', label="True "+yname)
    plt.plot(time,pred,'o', color='green', markersize=6, markeredgewidth=.3, markeredgecolor='black',label="Predicted "+yname)
    plt.xlabel("Time")
    plt.ylabel(yname)
    plt.legend()
    plt.savefig(f"{savepath}/pred_vs_time.png", bbox_inches='tight',transparent=False)
    if showplot:
        plt.show()
    plt.clf()

    epsilon = 1e-10
    metrics ={"r2": r2_score(ytest, pred),
              "mse": mean_squared_error(ytest,pred),
              "mape": np.mean(np.abs((ytest - pred) / (ytest + epsilon))) * 100}

    file_path=f"{savepath}/metrics.txt"
    with open(file_path,"w") as file:
        for key, value in metrics.items():
            file.write(f"{key}:{value}\n")

    return metrics




