<h1>Installation:</h1>

Download the installer:
`curl -O https://raw.githubusercontent.com/JSolsky/rpi-laser-sensor-main/main/setup.sh`
<br></br>
Make it executable:
`chmod +x setup.sh`
<br></br>
Run package install, venv creation:
`./setup.sh`
<br></br>

<h1>Management Commands:</h1>

View Logs: `tail -f /home/pi/server_log.txt`
Check Status: `sudo systemctl status myserver.service`
Restart Server: `sudo systemctl restart myserver.service`
<br></br>

Start venv for script (can only be done after running `./setup.sh`): `source venv/bin/activate`
If issues persist with packages:
1. Delete venv: `rm -rf /home/pi/rpi-laser-sensor-main/venv`
2. run `./setup.sh` again to create a fresh venv
<br></br>

Starting in background: `nohup python server.py  >./nohup.out 2>./nohup.err &`
<br></br>

To Kill process
1. find process using: `ps aux | grep "python server.py"`
2. find process id and kill `kill <process_id>`