import sys
import numpy as np
import ROOT
from ROOT import gROOT, AddressOf
import pickle
OS = sys.platform
if OS == 'win32':
    sep = '\\'
elif OS == 'linux':
    sep = '/'
else:
    print("ERROR: OS {} non compatible".format(OS))
    sys.exit()

step = -5
base_value = 340+63*5
class thr_importer_cl():
    
    def __init__(self, scan_path):
        self.run_path = scan_path
        self.baseline = {}
        self.baseline_from_calib_matrix=np.zeros((20, 8, 64))
        self.real_baseline_T = np.zeros((20, 8, 64))
        self.real_baseline_E = np.zeros((20, 8, 64))
        self.thr_matrix_T = np.zeros((20, 8, 64))
        self.thr_matrix_E = np.zeros((20, 8, 64))
        self.distance_from_baseline = np.zeros((20,8,64))
        self.diff_matrix = np.zeros((20,8,3))
        
    def import_run_thr(self):
        """
        Funcion to import the channel configuration from old RUNS. Needs the pickle containing the data
        :return:
        """
        File_name = "CONF_run_304.pkl"

        with open(File_name, 'rb') as f:
            old_conf_dict = pickle.load(f)

        for GEMROC_key, dict in old_conf_dict.items():
            GEMROC_id=GEMROC_key.split(" ")[1]
            for TIGER_key, dict2 in dict.items():
                if TIGER_key.split(" ")[0] == "TIGER":
                    TIGER_id = int(TIGER_key.split(" ")[1])
                    for channel_key, dict3 in dict2.items():
                        if channel_key.split(" ")[0] == "Ch":
                            channel_id = int(channel_key.split(" ")[1])
                            print ("{} - {} - {}".format(GEMROC_id, TIGER_id, channel_id))
                            try:
                                print (dict3["Vth_T1"])
                                print (dict3["Vth_T2"])
                                self.thr_matrix_T[int(GEMROC_id)][int(TIGER_id)][int(channel_id)]=dict3["Vth_T1"]
                                self.thr_matrix_E[int(GEMROC_id)][int(TIGER_id)][int(channel_id)]=dict3["Vth_T2"]
                            except KeyError as e:
                                print ('I a KeyError - missing %s. Probably a GEMROC is offline '% str(e))
                                break
                            # print self.GEMROC_reading_dict[GEMROC_key].c_inst.Channel_cfg_list[TIGER_id][channel_id]
            print ("Channel settings for {} loaded".format(GEMROC_key))

    def save_delta_VTHR_root(self):
        """
        Save the information about thr and baseline in a root file
        :return:
        """
        gROOT.ProcessLine('struct TreeStruct2 {\
                        int layer_id;\
                        int gemroc_id;\
                        int software_feb_id;\
                        int channel_id;\
                        int baseline;\
                        int vth1_digit;\
                        int vth2_digit;\
                        float vth1_mV;\
                        float vth2_mV;\
                        };')
        rootFile = ROOT.TFile("thresholds.root", 'recreate')
        tree = ROOT.TTree('tree', '')
        mystruct = ROOT.TreeStruct2()
        for key in ROOT.TreeStruct2.__dict__.keys():
            if '__' not in key:
                formstring = '/F'
                if isinstance(mystruct.__getattribute__(key), int):
                    formstring = '/I'
                tree.Branch(key, AddressOf(mystruct, key), key + formstring)

        for GEMROC in range(0, 4):
            for TIGER in range(0, 8):
                for ch in range(0, 64):
                    mystruct.layer_id = int(1)
                    mystruct.gemroc_id = (int(GEMROC))
                    mystruct.software_feb_id = int(TIGER)
                    mystruct.channel_id = int(ch)
                    mystruct.vth1_digit = int(self.thr_matrix_T[GEMROC][TIGER][ch])
                    mystruct.vth2_digit = int(self.thr_matrix_E[GEMROC][TIGER][ch])
                    mystruct.vth1_mV = float(mystruct.vth1_digit*step+base_value)
                    mystruct.vth2_mV = float(mystruct.vth2_digit*step+base_value)
                    tree.Fill()

        for GEMROC in range(4, 11):
            for TIGER in range(0, 8):
                for ch in range(0, 64):
                    mystruct.layer_id = int(2)
                    mystruct.gemroc_id = (int(GEMROC))
                    mystruct.software_feb_id = int(TIGER)
                    mystruct.channel_id = int(ch)
                    mystruct.baseline = int(self.real_baseline_T[GEMROC][TIGER][ch])
                    mystruct.vth1_digit = int(self.thr_matrix_T[GEMROC][TIGER][ch])
                    mystruct.vth2_digit = int(self.thr_matrix_E[GEMROC][TIGER][ch])
                    mystruct.vth1_mV = float(mystruct.vth1_digit*step+base_value)
                    mystruct.vth2_mV = float(mystruct.vth2_digit*step+base_value)
                    tree.Fill()
        rootFile.Write()
        rootFile.Close()

if __name__ == "__main__":
    thr_importer = thr_importer_cl("./scans")
    thr_importer.import_run_thr()
    thr_importer.save_delta_VTHR_root()
