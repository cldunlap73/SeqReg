import numpy as np
import pandas as pd

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