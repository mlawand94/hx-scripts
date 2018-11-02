import os
import sys
import subprocess
import re
import getpass
import string



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
    command = 'ssh root@`/opt/springpath/support/getstctlvmip.sh "Storage Controller Management Network"` -i /etc/ssh/ssh_host_rsa_key'    
    # os.system(command)        
    # output = subprocess.Popen(command).readlines()
    import subprocess  
    output = subprocess.Popen(command, shell=True)  
    counter = 0
    # for line in output:
    #     print('Counter: ' + counter + ': ' + line)
    #     if (re.match(r'(.*)sure you want to continue connecting(.*)'), line):
    #         print(" We can hit yes now")
    #         os.system('yes')
    # print(output)
    


def main():
    # Get Python version of the ESXi host
    getPythonVersion()
    # SSH into the VM and relinquish from cluster
        # https://techzone.cisco.com/t5/HyperFlex/Password-Recovery-for-STCTLVM/ta-p/988028
    sshIntoSCVM()
    # Power off the SCVM
    # Delete the SCVM
        # Destroy the SCVM
        # Make sure the /vmfs/volumes/StCtlVm dir is empty
    # Get all port groups and remove them
        # Do NOT remove vswitch-hx-inband-mgmt    
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