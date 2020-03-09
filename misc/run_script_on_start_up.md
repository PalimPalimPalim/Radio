## Step 1

Make script executable

`chmod a+x any_script.py`


## Step 2

Add to rc.local

`sudo nano /etc/rc.local`

Add before `Exit=0`

`python3 /home/pi/Documents/[...]/any_script.py`

## Stopping

`killall python3`