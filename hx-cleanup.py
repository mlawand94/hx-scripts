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
    # command = '/opt/springpath/support/getstctlvmip.sh "Storage Controller Management Network"'
    # output = executeFunctionWithReadlines(command)
    # output = os.popen('/opt/springpath/support/getstctlvmip.sh "Storage Controller Management Network"').readlines()
    # output = re.finditer(r'[0-9.]',str(output), re.MULTILINE)
    # ip = ''
    # for matchNum, match in enumerate(output):        
    #     ip += match.group()
    
    # Check for VM's other than the storage controller VM on the node.
    # executeFunction(command)

    command = "vim-cmd vmsvc/getallvms | sed -n '1!p' | wc -l"
    numberOfLines = int(executeFunctionWithRead(command))

    command = "vim-cmd vmsvc/getallvms | sed -n '1!p'"
    vm_list = executeFunctionWithRead(command)

    if numberOfLines == 1:
        vm_list = vm_list.split(" ")
        vm_id = vm_list[0]
        vm_name = vm_list[6]        
        # Check to see if the VM is powered off    
        command = 'vim-cmd vmsvc/power.get ' + vm_id + " | sed -n '1!p'"
        power_state = executeFunctionWithRead(command)        
        power_state = str(power_state.split(" ")[1].strip())
        
        
        if power_state == "on":
            print("Has the SCVM been relinquished? Input 1 for yes and 0 for no")
            scvm_relinquished = input()
            if scvm_relinquished == "1":            
                powerOffSCVM(vm_id)
            elif scvm_relinquished == "0":
                print("Please relinquish the SCVM from the cluster before proceeding.")
                print("SSH into the storage controller VM as root. ssh root@" + ip)
                print("Issue the command: python /usr/share/springpath/storfs-misc/relinquish_node.py ")
        elif power_state == "off":
            print("SCVM is powered off")
            destroySCVM(vm_id)
    elif(numberOfLines == 0):
        print("There are no SCVM's.. Proceeding to deleting networking")
        deletePortGroups()
    else:
        print("Please migrate all of the VM's off of the node before continuing. Do not migrate the SCVM")
        
    
def powerOffSCVM(vm_id):
    vm_id = vm_id
    print("powering off SCVM ...")
    command = 'vim-cmd vmsvc/power.off ' + str(vm_id)
    result = executeFunctionWithRead(command)    
    
    command = "vim-cmd vmsvc/power.get " + str(vm_id) + " | sed -n '1!p'"
    result = str(executeFunctionWithRead(command)).split(" ")[1].strip()
    print(result)
    if result == "off":
        print("SCVM is off")
        destroySCVM(vm_id)
    
def destroySCVM(vm_id):
    print("Time to destroy the scvm")
    command = 'vim-cmd vmsvc/destroy ' + str(vm_id)
    result = executeFunctionWithReadlines(command)
    print(len(result))
    if len(result) == 0:
        print("SCVM has been destroyed. Proceeding to clean up the networking")
        deletePortGroups()
    elif(len(result) > 0 and 'vim.fault.NotFound' in result[0]):
        print("The vm doesnt exist.. Proceeding to clean up the networking")
        deletePortGroups()
    # print(command)
    #Implement actually executing the function

portgroup_list = []
def deletePortGroups():
    command = "esxcli network vswitch standard portgroup list | sed -n '2!p' | sed -n '1!p'"
    result = executeFunctionWithReadlines(command)    
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
        # print(index["name"])
        # print(index["Virtual Switch"])
        if(index["name"] == "Management Network" or index["name"] == "Storage Hypervisor Data Network"):
            print("Skipping deletion of " + index["name"])
        else:
            command = 'esxcli network vswitch standard portgroup remove -v '+index['Virtual Switch']+' -p "'+index['name']+'"'
            output = executeFunctionWithReadlines(command)
            print(output)
    
    command = "esxcli network vswitch standard portgroup list | sed -n '2!p' | sed -n '1!p' | wc -l"
    # output = os.popen(command)
    # result = output.read()
    result = executeFunctionWithRead(command)
    result = str(result).strip()    
    print("Length of port group list: " + str(result))
    if int(result) == 2:
        print("All necessary port groups have been deleted.. Moving on to delete the VMK's")
        deleteVMKs()
        # deleteVswitches(portgroup_list)
        # output.close()
    else:
        print("There was a problem with deleting the port groups from the vswitches. Please delete the port groups from the vswitches and try again.")

    
    # pprint(len(portgroup_list))
                

    # result = result.split("  ")
    # print(result)
def deleteVMKs():
    print("In the delete vmk's function")
    command = 'esxcli network ip interface list | grep "Name: vmk*"'
    # output = os.popen(command)
    # result = output.readlines()
    result = executeFunctionWithReadlines(command)
    for line in result:
        line = line.split(" ")
        for index in line:
            if index != '':
                if "vmk" in str(index):
                    index = str(index).strip()
                    print("index: " + index[3])
                    if int(index[3]) >= 1:
                        command = "esxcli network ip interface remove -i " + index
                        # print(command)
                        output = executeFunctionWithReadlines(command)
                        print(output)
                        verification_command = 'esxcli network ip interface list | grep "Name: vmk*" | wc -l'
                        result = executeFunctionWithRead(verification_command)
                        # output = os.popen(verification_command)
                        # result = output.read()                        
                        result = str(result).strip()
                        print("Number of VMK's : " + str(result))
                        if int(result) == 1:
                            # output.close()                            
                            print("All necessary VMK's have been deleted. Proceeding with deleting vswitches...")
                            deleteVswitches()
                            # deleteOrphanedSCVM()
                        else:
                            print("There was a problem with deleting the necessary VMK's. Please delete all the VMK's except vmk0 and run this script again.")
                    else:
                        if(int(executeFunctionWithRead("esxcli network ip interface list | grep -i 'Name: vmk*' | wc -l")) == 1):
                            print("Only 1 vmk... proceed to delete vswitches")

def deleteVswitches(portgroup_list):
    print("Deleting the vswitches")
    for index in portgroup_list:
        print(index["Virtual Switch"])
        if index["Virtual Switch"] == "vswitch-hx-inband-mgmt":
            print("Skipping: " + index["Virtual Switch"])
        else:
            vswitch = str(index["Virtual Switch"]).strip()
            print(type(vswitch))
            print("The vswitch: " + vswitch)
            command = 'esxcli network vswitch standard remove -v "'+vswitch+'"'
            output = executeFunctionWithReadlines(command)
            print("Deleted vswitch: " + str(output))

    # Verify that vswitches have been deleted
    verification_command = 'esxcli network vswitch standard list | grep -i Name | wc -l'
    result = executeFunctionWithRead(verification_command)
    # output = os.popen(verification_command)
    # result = output.read()
    result = str(result).strip()
    print("Vswitch length result: " + result)
    if int(result) == 5:
        print("All vswitches have been deleted. Proceed to delete orphaned SCVM")
        deleteOrphanedSCVM()
        # deleteVMKs()


def deleteOrphanedSCVM():
    print("Please delete the orphaned SCVM from VCenter... Press 1 when this has been complete")
    deletedOrphanVm = input()
    if int(deletedOrphanVm) == 1:
        deleteDataStores()
    else:
        print("Please remove the orphaned VM and run this script again")

listOfDataStores = []
setOfDataStores = {}
def deleteDataStores():
    print("Starting datastore deletion")
    command = "grep -i nas /etc/vmware/esx.conf"
    result = executeFunctionWithReadlines(command)
    # output = os.popen(command)
    # result = output.readlines()
    for line in result:
        if "STFSNasPlugin" in line:
            print("Not deleting " + line)
        else:
            line = line.split("/")
            # print(line[2])
            listOfDataStores.append(str(line[2]))
    setOfDataStores = set(listOfDataStores)
    if len(setOfDataStores) >= 1:
        for ds in setOfDataStores:
            command = "esxcfg-nas -d " + ds
            print(command)
        cleanInternalSSD()

filesystem_list = []
ssd_cleanup_commands = ['esxcli system coredump file remove --force', 'esxcfg-dumppart -d', 'rm /scratch', ]
def cleanInternalSSD():
    counter = 0
    command = 'esxcli storage filesystem list'
    result = executeFunctionWithReadlines(command)
    # output = os.popen(command)
    # result = output.readlines()
    for line in result:
        # print(line)
        if('SpringpathDS' in line):
            line = line.split(" ")
            for index in line:
                if index is not '':
                    counter = counter+1
                    filesystem_list.insert(counter, index)
            uuid = filesystem_list[2]
            print(uuid)
    command2 = 'esxcli system coredump file remove --force'
    command3 = 'esxcfg-dumppart -d'
    command4 = 'rm /scratch'
    command5 = 'ps | grep vmsyslogd'
    output = os.popen(command5)
    result = output.readlines()
    zibby = []
    zibCount = 0
    for line in result:
        line = line.split(" ")
        for index in line:
            if index is not '':
                zibCount = zibCount + 1
                zibby.insert(zibCount, index)
    process = zibby[1]
    command6 = 'kill -9 ' + str(process)
    command7 = 'esxcli storage filsystem unmount -p /vmfs/volumes/' + str(uuid)
    # Get the hardware to confirm how we will be cleaning the SSD's
    serverModel = getServerModel()
    if serverModel == 'HX240C-M4S' or serverModel == 'HXAF240C-M4S':
        print("This is an M4 that needs back SSD's cleaned")
        cleanBackSSDM4()
    elif serverModel == 'HX240C-M5S' or serverModel == 'HXAF240C-M5S':
        print("This node has an M.2 SSD that needs cleaning")
        cleanM2SSDM5()
    else:
        print("This node does not have an M.2 SSD or back SSD that needs to be cleaned. Moving on..")

    # cleanBackSSDM4()
    # esxcli network vswitch standard remove -v "asdf"

def getServerModel():
    command = 'esxcli hardware platform get | grep -i "product name"'
    # output = os.popen(command)
    # result = output.read()
    result = executeFunctionWithRead(command)
    if str(result).startswith('Product Name:'):
        print(result)
    device_model = ((str(result)).strip()[13:str(result).find('.')]).strip()    
    return device_model

def cleanM2SSDM5():
    command = 'esxcli hardware platform get | grep -i "product name"'
    # output = os.popen(command)
    # result = output.read()
    # if str(result).startswith('Product Name:'):
    #     print(result)
    # device_model = (str(result)).strip()[13:str(result).find('.')]
    # print(device_model.strip())

def getM4BackSSDPartitionList():
    m4PartitionList = []
    print("in getM4BackSSDPartitionList")
    command = "esxcli storage core device partition list | sed -n '2!p' | sed -n '1!p'"
    # output = os.popen(command)
    # result = output.readlines()
    result = executeFunctionWithRead(command)
    partitionIndex = 0
    temp = []
    for line in result:        
        if 't10' in line:
            print('t10 in::: ' +line)
            partitionIndex = partitionIndex + 1
            line = line.split(" ")
            temp = []
            for index in line:
                if index is not '':
                    temp.append(index)
            m4PartitionList.insert(partitionIndex, temp)
    return m4PartitionList
        # print(line)
    

def cleanBackSSDM4():
    print("In cleanBackSSDM4")
    m4PartitionList = getM4BackSSDPartitionList()    

    for partition in m4PartitionList:        
        if int(partition[1]) == 1:
            command = 'partedUtil delete /vmfs/devices/disks/' + partition[0] + ' ' + partition[1]
            print(command)
    
    # Verify that the partition has been deleted, and format SSD to a GPT disk
    partition1Exists = 0
    verifyM4PartitionList = getM4BackSSDPartitionList()
    if len(m4PartitionList) == 1 and int(m4PartitionList[1]) == 0:
        print("Back SSD on the M4 has successfully been cleaned. \n Ready to proceed to turning disk into gpt. ")
        formatSSDToGPT()

def formatSSDToGPT():
    print("In the format SSD to GPT function")
    m4PartitionList = getM4BackSSDPartitionList()
    command = "partedUtil mklabel /vmfs/devices/disks/" + m4PartitionList[0] + " gpt"
    verification_command = 'partedUtil getpbl /vmfs/devices/disks/' + m4PartitionList

    print(command)
    print(verification_command)

def uninstallESXIVibs():
    vibList = []
    print("In the uninstallESXIVibs function")
    command = 'esxcli software vib list | grep -i spring'
    output = executeFunctionWithReadlines(command)
    temp = []
    tempCount = 0
    for line in output:
        temp = []
        tempCount = tempCount + 1
        line = line.split(" ")
        for index in line:    
            if(index is not ''):
                temp.append(index)            
        vibList.insert(tempCount, temp)    
    for vib in vibList:
        command = 'esxcli software vib remove -n ' + vib[0]
        commandOutput = executeFunctionWithReadlines(command)
        for response in commandOutput:
            if 'Message' in response and 'successfully' in response:                
                print("Success in removing Vib.. moving on..")
                print(response)
            elif('Reboot Required' in response and 'true' in response):
                print("ESXi needs to reboot to remove " + vib[0])
                print(response)

def executeFunctionWithReadlines(command):
    print("Executing: " + command)
    output = os.popen(command)
    result = output.readlines()
    output.close()
    return result

def executeFunctionWithRead(command):
    print("Executing: " + command)
    output = os.popen(command)
    result = output.read()
    output.close()
    return result
    


def main():
    # Get Python version of the ESXi host
    # getPythonVersion()
    # SSH into the VM and relinquish from cluster
        # https://techzone.cisco.com/t5/HyperFlex/Password-Recovery-for-STCTLVM/ta-p/988028
    sshIntoSCVM()
    # Power off the SCVM
    # Delete the SCVM
        # Destroy the SCVM
        # Make sure the /vmfs/volumes/StCtlVm dir is empty
    # Get all port groups and remove them
        # Do NOT remove vswitch-hx-inband-mgmt 
        # 

    # deletePortGroups()

    # Remove the vswitches
        # List them all and remove them all
            # esxcli network vswitch standard list | grep -i name
    # deleteVswitches()
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
    # uninstallESXIVibs()

    
    # sshIntoSCVM()

if __name__ == "__main__":
    main()