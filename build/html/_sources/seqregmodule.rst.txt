SeqReg Module
=============
.. role:: red

**function** :red:`LoadDataFromFolder(...)`

    Parameters:
        * folderpath: path to location of saved data (in specified csv format)
        * xname: name of the csv column with xdata
        * yname: name of the csv column with ydata
        * tname: name of the csv column with time data (defaults to Time)
        * datatype: type of data in the x column (either Value, txtFilePath, PCAnpy) (defaults to Value)
        * pcskeep: amount of pcs to keep if using data from PCA data reduction (either and interger or "ALL") (defaults to ALL)

    Output:
        * xds: list of all loaded x data of shape (# of experiments, -)
        * yds: list of all loaded y data of shape (# of experiments, -)
        * timeds: list of all loaded time data of shape (# of experiments, -)

**function** :red:`PrepareData(...)`

    Parameters:
        * x: list of all loaded x data (xds output from LoadDataFromFolder function)
        * y: list of all loaded y data (yds output from LoadDataFromFolder function)
        * time: list of all loaded time data (timeds output from LoadDataFromFolder function)
        * seqlen: length of sequences to generate using a rolling sampling method
        * stride: stride to use for generating sequences using a rolling sampling method
        * dt: timestep between each data point. This is only relevant if using the FFT
        * fft: a boolean defining whether to use the fft to transform x data sequences to the frequency domain (defaults to False)
        * seqout: a boolean defining whether the y data should be a single value or sequence for outputs

    Output:
        * x1: numpy array of transformed x data
        * y1: numpy array of transformed y data
        * t1: numpy array of transformed time data

**function** :red:`Model(...)`

    Parameters:
        * modelname: the name of the model architecture to be used (HydReg, Hit2Flux, ImgReg)
        * savemodelpath: either the path to the location of saved weights if train=False or path to location where weights will be saved if train=True
        * train: boolean specifying whether a model is to be trained or using a pretrained model (defaults to False)
        * xtrain: numpy array containing training x data prepared based on PrepareData function (defaults to None)
        * ytrain: numpy array containing training y data prepared based on PrepareData function (defaults to None)

    Output:
        * model: a tensorflow or sklearn model
        * if train=True saved weigths or model to specified path

**function** :red:`Analyze(...)`

    Parameters:
        * model: tensorflow or sklearn model
        * savepath: path to location where metrics and plots should be saved
        * xtest: numpy array of x test data generated from PrepareData function
        * ytest: numpy array of y test data generated from PrepareData function
        * time: numpy array of time test data generated from PrepareData function
        * xname: name of x data (defaults to X Data)
        * yname: name of y data to appear on plots (defaults to Y Data)
        * seqout: boolean to specify if y data is single values or sequences. If True, the last value in each sequence is used for plotting and metrics (defaults to False)
        * showplot: boolean to specify if the plots should be displayed or only saved (defaults to True)

    Output:
        * Two plots are saved to the savepath showing predicted vs true value comparision
        * A text file with error metrics is saved to savepath
