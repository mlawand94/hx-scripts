import os
import sys
import subprocess
import re
import getpass
import string
import time
from itertools import islice
import json
from pprint import pprint


def getPythonVersion():
    print("Checking version info....")
    print(sys.version_info[0])

def relinquishSCVM():
    if(getPythonVersion() == 2):
        # Python 2 function
        print("Python 2 command")
    elif(getPythonVersion() == 3):
        # Python 3 function
        print("Python 3 command")

def sshIntoSCVM():    
    # Getting IP address of the Storage Controller VM
    output = os.popen('/opt/springpath/support/getstctlvmip.sh "Storage Controller Management Network"').readlines()
    output = re.finditer(r'[0-9.]',str(output), re.MULTILINE)
    ip = ''
    for matchNum, match in enumerate(output):        
        ip += match.group()
    
    # Check for VM's other than the storage controller VM on the node.
    command = "vim-cmd vmsvc/getallvms | sed -n '1!p' | wc -l"
    output = os.popen(command)
    numberOfLines = int(output.read())
    output.close()

    command = "vim-cmd vmsvc/getallvms | sed -n '1!p'"
    output = os.popen(command)
    vm_list = output.read()    
    output.close()

    if numberOfLines == 1:
        vm_list = vm_list.split(" ")
        vm_id = vm_list[0]
        vm_name = vm_list[6]        
        # Check to see if the VM is powered off    
        command = 'vim-cmd vmsvc/power.get ' + vm_id + " | sed -n '1!p'"
        output = os.popen(command)
        power_state = output.read()
        power_state = str(power_state.split(" ")[1].strip())
        output.close()
        
        if power_state == "on":
            print("Has the SCVM been relinquished? Input 1 for yes and 0 for no")
            scvm_relinquished = input()
            if scvm_relinquished == "1":            
                powerOffSCVM(vm_id)
            elif scvm_relinquished == "0":
                print("Please relinquish the SCVM from the cluster before proceeding.")
                print("SSH into the storage controller VM as root. ssh root@" + ip)
                print("Issue the command: python /usr/share/springpath/storfs-misc/relinquish_node.py ")
        
    else:
        print("Please migrate all of the VM's off of the node before continuing. Do not migrate the SCVM")
    
    
    
def powerOffSCVM(vm_id):
    vm_id = vm_id
    print("powering off SCVM ...")
    command = 'vim-cmd vmsvc/power.off ' + str(vm_id)
    output = os.popen(command)
    result = output.read()
    time.sleep(15)
    
    command = "vim-cmd vmsvc/power.get " + str(vm_id) + " | sed -n '1!p'"
    output = os.popen(command)
    result = str(output.read()).split(" ")[1].strip()
    if result == "off":
        destroySCVM(vm_id)
    
def destroySCVM(vm_id):
    command = 'vim-cmd vmsvc/destroy 1'

portgroup_list = []

def deletePortGroups():
    command = "esxcli network vswitch standard portgroup list | sed -n '2!p' | sed -n '1!p'"
    output = os.popen(command)
    result = output.readlines()
    listCounter = 0
    for line in result:
        line = line.split("  ")
        listCounter = listCounter + 1        
        counter = 0
        vswitch_port_group_list = {}
        for index in line:            
            if (index is not ''):
                counter = counter + 1
                if counter == 1:
                    vswitch_port_group_list["name"] = index.strip()
                if counter == 2:
                    vswitch_port_group_list["Virtual Switch"] = index.strip()
                if counter == 3:
                    vswitch_port_group_list["Active Clients"] = index.strip()
                if counter == 4: 
                    vswitch_port_group_list["VLAN ID"] = index.strip()
        portgroup_list.insert(listCounter, vswitch_port_group_list)
    for index in portgroup_list:
        print(index["name"])
        print(index["Virtual Switch"])
        command = 'esxcli network vswitch standard portgroup remove -v '+index['Virtual Switch']+' -p "'+index['name']+'"'
        print(command)
        print("\n")
    # pprint(len(portgroup_list))
                

    # result = result.split("  ")
    # print(result)

def main():
    # Get Python version of the ESXi host
    # getPythonVersion()
    # SSH into the VM and relinquish from cluster
        # https://techzone.cisco.com/t5/HyperFlex/Password-Recovery-for-STCTLVM/ta-p/988028
    # sshIntoSCVM()
    # Power off the SCVM
    # Delete the SCVM
        # Destroy the SCVM
        # Make sure the /vmfs/volumes/StCtlVm dir is empty
    # Get all port groups and remove them
        # Do NOT remove vswitch-hx-inband-mgmt    
    deletePortGroups()
    # Remove the vswitches
        # List them all and remove them all
            # esxcli network vswitch standard list | grep -i name
    # Remove the vmotion vmkernel interface (vmk2)
    # Prompt user to delete the orphaned vm's from vc inventory - proceed when done
    # List all datastores and delete them from the host
        # grep -i nas /etc/vmware/esx.conf
            # Delete them all until we only have the below outputs: 
                # /firewall/services/STFSNasPlugin/enabled = "false"
                # /firewall/services/STFSNasPlugin/allowedall = "true"
    # restart hostd
    # stop scvmclient  
    # Clean up SSD's
    # Uninstall HX Vibs
    # Reboot

if __name__ == "__main__":
    main()