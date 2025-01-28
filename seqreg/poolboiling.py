import numpy as np
import pandas as pd
import os
import pickle
from PIL import Image

def PrepareHydrophone(tempfilepath,soundfilepath, savepath, extracttime=True,tempstart=None,soundstart=None):
    # Load temperature and choose proper order of thermocouples
    temp_data=np.loadtxt(tempfilepath, skiprows=23)
    temptime=temp_data[:,0]

    index_=np.argmin(temp_data[:,1])+(np.argmax(temp_data[:,1])-np.argmin(temp_data[:,1]))//2
    referencetemp=[temp_data[index_,i+1]for i in range(4)]
    sorted=np.argsort(referencetemp)[::-1]

    temp1=temp_data[:,sorted[0]+1]
    temp2=temp_data[:,sorted[1]+1]
    temp3=temp_data[:,sorted[2]+1]
    temp4=temp_data[:,sorted[3]+1]

    temp=np.transpose(np.array([temp1,temp2,temp3,temp4]))

    # Calculate heat flux
    tc_loc=np.array([0, 2.54, 5.08, 7.62])
    tc_loc=tc_loc*.001
    n=4
    k=392
    slope_d=n*np.sum(np.power(tc_loc,2))-np.sum(tc_loc)**2
    slope=(n*np.dot(temp,tc_loc)-np.sum(tc_loc)*np.sum(temp,axis=1))/slope_d
    hf=-k*slope/10000


    # Load sound data
    sounddata=np.loadtxt(soundfilepath, skiprows=23)
    soundtime=sounddata[:,0]
    sound=sounddata[:,1]

    # Find start times of sound and temperature
    if extracttime:
        with open(tempfilepath,"r") as file:
            for num, line in enumerate(file, start=1):
                if num == 11:
                    if "Time" in line:
                        time_value=line.split()[1]
                        break
        tempstart=int(time_value.split(":")[0]) * 3600 + int(time_value.split(":")[1]) * 60 + float(time_value.split(":")[2])

        with open(soundfilepath,"r") as file:
            for num, line in enumerate(file, start=1):
                if num == 11:
                    if "Time" in line:
                        time_value=line.split()[1]
                        break
        soundstart=int(time_value.split(":")[0]) * 3600 + int(time_value.split(":")[1]) * 60 + float(time_value.split(":")[2])

    # Match heat flux to sound
    temptimeadj=temptime+tempstart
    soundtimeadj=soundtime+soundstart
    hfmatch=np.interp(soundtimeadj,temptimeadj,hf)


    # Save to csvfile
    data={"Time": soundtime,
          "Sound": sound,
          "Heat Flux": hfmatch}
    df=pd.DataFrame(data)
    df.to_csv(savepath,index=False)

def PrepareAE(aedata, aewaveforms, tempfilepath, output, name, extracttime=True, aestart=None, tempstart=None):
    temp_data=np.loadtxt(tempfilepath, skiprows=23)
    temptime=temp_data[:,0]

    index_=np.argmin(temp_data[:,1])+(np.argmax(temp_data[:,1])-np.argmin(temp_data[:,1]))//2
    referencetemp=[temp_data[index_,i+1]for i in range(4)]
    sorted=np.argsort(referencetemp)[::-1]

    temp1=temp_data[:,sorted[0]+1]
    temp2=temp_data[:,sorted[1]+1]
    temp3=temp_data[:,sorted[2]+1]
    temp4=temp_data[:,sorted[3]+1]

    temp=np.transpose(np.array([temp1,temp2,temp3,temp4]))

    # Calculate heat flux
    tc_loc=np.array([0, 2.54, 5.08, 7.62])
    tc_loc=tc_loc*.001
    n=4
    k=392
    slope_d=n*np.sum(np.power(tc_loc,2))-np.sum(tc_loc)**2
    slope=(n*np.dot(temp,tc_loc)-np.sum(tc_loc)*np.sum(temp,axis=1))/slope_d
    hf=-k*slope/10000

    csv_files=[file for file in os.listdir(aewaveforms) if file.endswith(".csv")]
    csv_files.sort(key=lambda x: int(x.split("_")[3]))

    # make folder for saving data
    if not os.path.exists(output):
        os.makedirs(output)
    if not os.path.exists(output+"Data"):
        os.makedirs(output+"Data")

    # Load each csv, save to txt file and save location and time to lists
    aetimes=[file.split("_")[4].split(".")[0] for file in csv_files]
    aetimes=[float(s[:-6]+'.'+s[-6:]) for s in aetimes]

    filepath=aewaveforms+csv_files[0]
    addtime=np.genfromtxt(filepath, delimiter=",",skip_header=12)[-1,0]
    txtpaths=[]
    for i in range(len(csv_files)):
        filepath=aewaveforms+csv_files[i]
        aewave=np.genfromtxt(filepath, delimiter=",",skip_header=12)[:,1]
        savepath=output+"Data/"+name+"_"+str(i)+".txt"
        txtpaths.append("./Data/"+name+"_"+str(i)+".txt")
        np.savetxt(savepath,aewave,fmt='%s')

    # Load in start times for ae sensor and thermocouples
    if extracttime:
        with open(tempfilepath,"r") as file:
            for num, line in enumerate(file, start=1):
                if num == 11:
                    if "Time" in line:
                        time_value=line.split()[1]
                        break
        tempstart=int(time_value.split(":")[0]) * 3600 + int(time_value.split(":")[1]) * 60 + float(time_value.split(":")[2])

        with open(aedata,"r") as file:
            for num,line in enumerate(file):
                if num == 5:
                    time_value=line.split()[3]
                    break
        aestart=int(time_value.split(":")[0]) * 3600 + int(time_value.split(":")[1]) * 60 + float(time_value.split(":")[2])

    # Interpolate heat flux
    temptimeadj=temptime+tempstart
    aetimeadj=np.array(aetimes)+aestart
    hfmatch=np.interp(aetimeadj+addtime,temptimeadj,hf)

    data={"Time": aetimes,
          "Sound Paths": txtpaths,
          "Heat Flux": hfmatch}
    df=pd.DataFrame(data)
    savepath=output+name+".csv"
    df.to_csv(savepath,index=False)

def PrepareImages(imagepathfolder,tempfilepath,savepath,framerate, vidstart,extracttime=True):
    temp_data = np.loadtxt(tempfilepath, skiprows=23)
    temptime = temp_data[:, 0]

    index_ = np.argmin(temp_data[:, 1]) + (np.argmax(temp_data[:, 1]) - np.argmin(temp_data[:, 1])) // 2
    referencetemp = [temp_data[index_, i + 1] for i in range(4)]
    sorted = np.argsort(referencetemp)[::-1]

    temp1 = temp_data[:, sorted[0] + 1]
    temp2 = temp_data[:, sorted[1] + 1]
    temp3 = temp_data[:, sorted[2] + 1]
    temp4 = temp_data[:, sorted[3] + 1]

    temp = np.transpose(np.array([temp1, temp2, temp3, temp4]))

    # Calculate heat flux
    tc_loc = np.array([0, 2.54, 5.08, 7.62])
    tc_loc = tc_loc * .001
    n = 4
    k = 392
    slope_d = n * np.sum(np.power(tc_loc, 2)) - np.sum(tc_loc) ** 2
    slope = (n * np.dot(temp, tc_loc) - np.sum(tc_loc) * np.sum(temp, axis=1)) / slope_d
    hf = -k * slope / 10000

    files = [imagepathfolder+f for f in os.listdir(imagepathfolder) if f.endswith(".jpg")]
    files=files.sort()
    if extracttime:
        with open(tempfilepath,"r") as file:
            for num, line in enumerate(file, start=1):
                if num == 11:
                    if "Time" in line:
                        time_value=line.split()[1]
                        break
        tempstart=int(time_value.split(":")[0]) * 3600 + int(time_value.split(":")[1]) * 60 + float(time_value.split(":")[2])

    temptimeadj = temptime + tempstart
    imgtime=np.array([i/framerate for i in range(len(files))])
    imgtimeadj=imgtime+vidstart
    hfmatch = np.interp(imgtimeadj, temptimeadj, hf)
    data = {"Time": imgtime,
            "Image Paths": files,
            "Heat Flux": hfmatch}
    df = pd.DataFrame(data)
    df.to_csv(savepath, index=False)

def PreparePCAImages(pcamodelpath, imagecsvfile,imgw,imgh, pcas):
    # Save images as pca's
    # Load images
    df =pd.read_csv(imagecsvfile)
    image_locs=df['Image Paths'].tolist()

    # Load pca model path

    with open(pcamodelpath,'rb') as file:
        pca=pickle.load(file)

    # Transform images
    pca_transformed=np.empty((len(image_locs),pcas))
    for i, imagefile in enumerate(image_locs):
        image=Image.open(imagefile)
        image=image.resize((imgw,imgh))
        image=np.reshape(np.array(image), (imgw*imgh))/255
        pca_transformed[i]=np.squeeze(pca.transform(np.expand_dims(image, axis=0)), axis=0)[:pcas]
    savepath=imagecsvfile.split(".csv")[0]+".npy"
    np.save(savepath,pca_transformed)

