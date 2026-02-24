Installation:

Download the installer:
`curl -O https://raw.githubusercontent.com/JSolsky/rpi-laser-sensor-main/main/install.sh`

Make it executable:
`chmod +x install.sh`

Run it:
`./install.sh`

Management Commands:
View Logs: `tail -f /home/pi/server_log.txt`
Check Status: `sudo systemctl status myserver.service`
Restart Server: `sudo systemctl restart myserver.service`

Starting in background: `nohup python server.py  >./nohup.out 2>./nohup.err &`

Kill process
1. find process using: `ps aux | grep "python server.py"`
2. find process id and kill `kill <process_id>`