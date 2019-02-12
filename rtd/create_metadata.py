import os
import sys 

sys.path.append(os.path.join(os.getcwd(), "rtd"))  
from rtd_workflow_wMARCFINDER import rtd_metadata   

if __name__=="__main__":
    rtd_metadata()
