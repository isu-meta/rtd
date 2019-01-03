import os
import sys 

sys.path.append(os.getcwd()+"/code_base")  
from rtd_workflow_wMARCFINDER import rtd_metadata   

if __name__=="__main__":
    rtd_metadata()
