# hx-scripts
This script restores the networking settings for a storage controller virtual machine on a Hyperflex ESXi host. 

This script should be applied if: 
  1. ESXi was re-imaged on a 240 M5 UCS HX node. 
  2. Something or someone accidentally changed the ESXi host network settings and it needs to be restored.
  
How to use:
  1. Put the script on the affected host fia FTP/SCP 
  2. Run the command, "py esxi-resore.py"
  3. Input all of the IP addresses that is requested for that host. 
