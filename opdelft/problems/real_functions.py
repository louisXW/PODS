import numpy as np
from math import *
import subprocess
import csv
import traceback
import sys
import logging
import copy

from opdelft.util.goodness_of_fit_metrics import Metrics
from opdelft.util.post_analysis import Postprocessing
from threading import Lock


class delft3d_1objs:
    #  Global optimum: f(0,0,...,0)=0
    def __init__(self, dim=4):
        # PREPARE INPUT FILE  [Vicouv, Dicouv, Vicoww, Dicoww]
        self.xlow = np.array([0.1, 0.1, 0, 0])
        self.xup = np.array([1.0, 1.0, 0.005, 0.005])
        self.dim = dim
        self.info = str(dim) + " Ansoulate error function \n" + \
                    "Global optimum: f(0,0,...,0) = 0"
        self.integer = []
        self.continuous = np.arange(0, dim)
        self.runid = 0
        self.simlen = 365  # the simlutation length unit /day
        self.lock = Lock()
        self.exp_iteration = 3  # The number of iteration to finish the initial experimental design
        self.exp_simid = []
        self.no_sub_objs = 1
        self.home_dir = ''

    def objfunction(self, x, simid, iterid):
        simid_loc = copy.copy(simid)
        iterid_loc = copy.copy(iterid)
        print ("current folder", self.home_dir)
        if len(x) != self.dim:
            raise ValueError('Dimension mismatch')
        logging.info('The %d iteration %d simulation called objfunction' % (iterid_loc, simid_loc))


        sub_objs = self.delft3d_flow(x, simid_loc, iterid_loc)
        parms = x.tolist()
        fp = open(self.home_dir + "/result/pysot_result.txt", "a")
        fp.write("%s\t%s\t%s\t@%s\n" % (iterid_loc, simid_loc, sub_objs, parms))
        fp.close()

        return sub_objs

    def delft3d_flow(self, x, simid, iterid):
        simid_lloc = copy.copy(simid)
        iterid_lloc = copy.copy(iterid)
        workingdir = self.home_dir + str(simid_lloc)

        # ====================================Coefficient file modification====================================#
        """ This section is for the model simulation file modification based on the proposed paramter vecor x.
        A simple example of modify 4 parameters [Vicouv, Dicouv, Vicoww, Dicoww] for the coefficient file f34.mdf
         is shown inside the modify_coefficient() function """

        self.modify_coefficient(x, simid_lloc, iterid_lloc)

        # ====================================running simulation====================================#
        """ This section to launch the simulation. The code shown here is running the delft3d under Linux """

        try:
           cmd = './run_flow2d3d.sh'
           subprocess.Popen(cmd, cwd=workingdir).wait()
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
            logging.exception("Trackback Error:%d iteration %d evaluation" % (iterid_lloc, simid_lloc))
            pass
        else:
            logging.info('%s iteration %s evaluation: finished simulation' % (iterid_lloc, simid_lloc))

            # ====================================post analysis of the result file====================================#
            """ convert the NEFIS format history file *.dat *.def into DAT format file *dat. 
            The example shown here is using vs tool inside Delft3D suit convert nefis file to dat file under linux. 
            Users might need to modify the "his2dat.sh" file when work their own problem"""
            cmd2 = './his2dat.sh'
            subprocess.call(cmd2, cwd=workingdir)  # convert the histroy file to python readable dat file

            """ read the observation data and simulation result. An example that reading the velocity at sataion 1 layer 1"""

            objfunc = Metrics()
            postutil = Postprocessing()
            observation_curu = workingdir + "/ZCURU_measured.dat"
            observation_curv = workingdir + "/ZCURV_measured.dat"
            observation_curw = workingdir + "/ZCURW_measured.dat"
            sim_curu = workingdir + "/ZCURU.dat"
            sim_curv = workingdir + "/ZCURV.dat"
            sim_curw = workingdir + "/ZCURW.dat"

            observation_curu_layer1 = postutil.read_simulation_data(observation_curu, 1, 1)

            observation_curv_layer1 = postutil.read_simulation_data(observation_curv, 1, 1)

            observation_curw_layer1 = postutil.read_simulation_data(observation_curw, 1, 1)
            sim_curu_layer1 = postutil.read_simulation_data(sim_curu, 2, 1)
            sim_curv_layer1 = postutil.read_simulation_data(sim_curv, 2, 1)
            sim_curw_layer1 = postutil.read_simulation_data(sim_curw, 2, 1)

            fn_layer1 = objfunc.fouriernorm(observation_curu_layer1, observation_curv_layer1, observation_curw_layer1,
                                            sim_curu_layer1, sim_curv_layer1,
                                            sim_curw_layer1)

            sub_obj1 = fn_layer1

            sub_objs = []
            sub_objs.append(sub_obj1)

            return sub_objs

    def modify_coefficient(self, x, sim_id, iter_id):
        """
        modify the coefficient file *.mdf
        :param x: the parameter vector
        :param sim_id: the index of the simulation id
        :param iter_id: the index of the iteration id
        :return: None
        """
        x = x
        sim_id = sim_id
        iter_id = iter_id
        workingdir = self.home_dir + str(sim_id)
        # PREPARE INPUT FILE  [Vicouv, Dicouv, Vicoww, Dicoww]
        par_linenum = [74, 75, 77, 78]  # the respective line numbers of these parameters in the *.mdf file
        fp = open(workingdir + "/f34_base.mdf", "rb")
        file_copy = fp.readlines()
        for i in range(len(par_linenum)):
            par = "{:.7e}".format(x[i])
            str1 = file_copy[par_linenum[i]-1]
            str2 = str1.split()
            str3 = str2[0] + ' ' + str2[1] + '  ' + str(par) + '\n'
            file_copy[par_linenum[i]-1] = str3
        fp.close()
        fp = open(workingdir + "/f34.mdf", "wb")
        for item in file_copy:
            fp.write("%s" % item)
        fp.close()
        logging.info('%s iteration %s evaluation: finished modify the coefficient file' % (str(iter_id), str(sim_id)))

    def save_result_file(self, sim_id, iter_id):
        """
        An example to save the simulation output file e.g. trih-f34.dat and trih-f34.def
        :param sim_id: the index of the simulation id
        :param iter_id: the index of the iteration id
        :return: None
        """
        sim_id = sim_id
        iter_id = iter_id
        workingdir = self.home_dir + str(sim_id)
        simiter_name = '{:0>3}'.format(iter_id)
        command = "cp %s/trih-f34.dat %s/result/history_data/%s_%strih-f34.dat" % (
            workingdir, self.home_dir, simiter_name, sim_id)
        subprocess.call(command, shell=True, cwd=workingdir)

        command = "cp %s/trih-f34.def %s/result/history_data/%s_%strih-f34.def" % (
            workingdir, self.home_dir, simiter_name, sim_id)
        subprocess.call(command, shell=True, cwd=workingdir)




class delft3d_2objs:
    #  Global optimum: f(0,0,...,0)=0
    def __init__(self, dim=4):
        # PREPARE INPUT FILE  [Vicouv, Dicouv, Vicoww, Dicoww]
        self.xlow = np.array([0.1, 0.1, 0, 0])
        self.xup = np.array([1.0, 1.0, 0.005, 0.005])
        self.dim = dim
        self.info = str(dim) + " Ansoulate error function \n" + \
                    "Global optimum: f(0,0,...,0) = 0"
        self.integer = []
        self.continuous = np.arange(0, dim)
        self.runid = 0
        self.simlen = 365  # the simlutation length unit /day
        self.lock = Lock()
        self.exp_iteration = 3  # The number of iteration to finish the initial experimental design
        self.exp_simid = []
        self.no_sub_objs = 2
        self.home_dir = ''

    def objfunction(self, x, simid, iterid):
        simid = simid
        iterid = iterid
        print ("current folder", self.home_dir)
        if len(x) != self.dim:
            raise ValueError('Dimension mismatch')
        logging.info('The %d iteration %d simulation called objfunction' % (iterid, simid))

        if iterid <= self.exp_iteration & iterid > 1:
            """ The part of code only take effect when the number of iterations to 
            finish the initial experimental desgin larger than 1"""
            with self.lock:
                simid = self.exp_simid[0]
                self.exp_simid.pop(0)

        sub_objs = self.delft3d_flow(x, simid, iterid)
        parms = x.tolist()
        fp = open(self.home_dir + "/result/pysot_result.txt", "a")
        fp.write("%s\t%s\t%s\t@%s\n" % (iterid, simid, sub_objs, parms))
        fp.close()

        if iterid < self.exp_iteration:
            with self.lock:
                self.exp_simid.append(simid)

        return sub_objs

    def delft3d_flow(self, x, simid, iterid):
        simid = simid
        iterid = iterid
        workingdir = self.home_dir + str(simid)

        # ====================================Coefficient file modification====================================#
        """ This section is for the model simulation file modification based on the proposed paramter vecor x.
        A simple example of modify 4 parameters [Vicouv, Dicouv, Vicoww, Dicoww] for the coefficient file f34.mdf
         is shown inside the modify_coefficient() function """

        self.modify_coefficient(x, simid, iterid)

        # ====================================running simulation====================================#
        """ This section to launch the simulation. The code shown here is running the delft3d under Linux """

        try:
           cmd = './run_flow2d3d.sh'
           subprocess.Popen(cmd, cwd=workingdir).wait()
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
            logging.exception("Trackback Error:%d iteration %d evaluation" % (iterid, simid))
            pass
        else:
            logging.info('%s iteration %s evaluation: finished simulation' % (iterid, simid))

            # ====================================post analysis of the result file====================================#
            """ convert the NEFIS format history file *.dat *.def into DAT format file *dat. 
            The example shown here is using vs tool inside Delft3D suit convert nefis file to dat file under linux. 
            Users might need to modify the "his2dat.sh" file when work their own problem"""
            cmd2 = './his2dat.sh'
            subprocess.call(cmd2, cwd=workingdir)  # convert the histroy file to python readable dat file

            """ read the observation data and simulation result. An example that reading the velocity at sataion 1 layer 1"""

            objfunc = Metrics()
            postutil = Postprocessing()
            observation_curu = workingdir + "/ZCURU_measured.dat"
            observation_curv = workingdir + "/ZCURV_measured.dat"
            observation_curw = workingdir + "/ZCURW_measured.dat"
            sim_curu = workingdir + "/ZCURU.dat"
            sim_curv = workingdir + "/ZCURV.dat"
            sim_curw = workingdir + "/ZCURW.dat"

            observation_curu_layer1 = postutil.read_simulation_data(observation_curu, 1, 1)

            observation_curv_layer1 = postutil.read_simulation_data(observation_curv, 1, 1)

            observation_curw_layer1 = postutil.read_simulation_data(observation_curw, 1, 1)
            sim_curu_layer1 = postutil.read_simulation_data(sim_curu, 2, 1)
            sim_curv_layer1 = postutil.read_simulation_data(sim_curv, 2, 1)
            sim_curw_layer1 = postutil.read_simulation_data(sim_curw, 2, 1)

            fn_layer1 = objfunc.fouriernorm(observation_curu_layer1, observation_curv_layer1, observation_curw_layer1,
                                            sim_curu_layer1, sim_curv_layer1,
                                            sim_curw_layer1)

            sub_obj1 = fn_layer1

            """ read the observation data and simulation result. An example that reading the velocity at sataion 2 layer 1"""

            observation_curu_layer2 = postutil.read_simulation_data(observation_curu, 1, 1)

            observation_curv_layer2 = postutil.read_simulation_data(observation_curv, 1, 1)

            observation_curw_layer2 = postutil.read_simulation_data(observation_curw, 1, 1)
            sim_curu_layer2 = postutil.read_simulation_data(sim_curu, 2, 1)
            sim_curv_layer2 = postutil.read_simulation_data(sim_curv, 2, 1)
            sim_curw_layer2 = postutil.read_simulation_data(sim_curw, 2, 1)

            fn_layer2 = objfunc.fouriernorm(observation_curu_layer2, observation_curv_layer2, observation_curw_layer2,
                                            sim_curu_layer2, sim_curv_layer2,
                                            sim_curw_layer2)

            sub_obj2 = fn_layer2
            sub_objs = []
            sub_objs.append(sub_obj1)
            sub_objs.append(sub_obj1)
            logging.info('%s iteration %s evaluation: finished calculating the objection function' % (iterid, simid))



            return sub_objs

    def modify_coefficient(self, x, sim_id, iter_id):
        """
        modify the coefficient file *.mdf
        :param x: the parameter vector
        :param sim_id: the index of the simulation id
        :param iter_id: the index of the iteration id
        :return: None
        """
        x = x
        sim_id = sim_id
        iter_id = iter_id
        workingdir = self.home_dir + str(sim_id)
        # PREPARE INPUT FILE  [Vicouv, Dicouv, Vicoww, Dicoww]
        par_linenum = [74, 75, 77, 78]  # the respective line numbers of these parameters in the *.mdf file
        fp = open(workingdir + "/f34_base.mdf", "rb")
        file_copy = fp.readlines()
        for i in range(len(par_linenum)):
            par = "{:.7e}".format(x[i])
            str1 = file_copy[par_linenum[i]-1]
            str2 = str1.split()
            str3 = str2[0] + ' ' + str2[1] + '  ' + str(par) + '\n'
            file_copy[par_linenum[i]-1] = str3
        fp.close()
        fp = open(workingdir + "/f34.mdf", "wb")
        for item in file_copy:
            fp.write("%s" % item)
        fp.close()
        logging.info('%s iteration %s evaluation: finished modify the coefficient file' % (str(iter_id), str(sim_id)))

    def save_result_file(self, sim_id, iter_id):
        """
        An example to save the simulation output file e.g. trih-f34.dat and trih-f34.def
        :param sim_id: the index of the simulation id
        :param iter_id: the index of the iteration id
        :return: None
        """
        sim_id = sim_id
        iter_id = iter_id
        workingdir = self.home_dir + str(sim_id)
        simiter_name = '{:0>3}'.format(iter_id)
        command = "cp %s/trih-f34.dat %s/result/history_data/%s_%strih-f34.dat" % (
            workingdir, self.home_dir, simiter_name, sim_id)
        subprocess.call(command, shell=True, cwd=workingdir)

        command = "cp %s/trih-f34.def %s/result/history_data/%s_%strih-f34.def" % (
            workingdir, self.home_dir, simiter_name, sim_id)
        subprocess.call(command, shell=True, cwd=workingdir)















