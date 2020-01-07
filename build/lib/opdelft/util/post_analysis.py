import numpy as np

class Postprocessing:
    def read_simulation_data(self, filename, station_id, layer_id):
        """
        read the simulation output file with format *.dat (convert from NEFIS file *.dat and *.def to txt file
        :param filename: The name of the file
        :param station_id: the id of the observation station. Integer start from zero
        :param layer_id: the id of the layer number. Integer start from one
        :return: the time series simulation result [daynumber, result]
        """
        filename = filename
        station = station_id
        layer = layer_id
        f = open(filename, "r")
        file_copy = f.readlines()
        str1 = file_copy[3]
        str2 = str1.split()
        nrow = int(str2[0])
        ncol = int(str2[1])
        nplane = int(str2[2])
        nstation = nrow / nplane
        f.close()
        sim_layer = []
        for i in range(nplane):
            str1 = file_copy[3 + station + nstation * i]
            str2 = str1.split()
            sim = []
            sim.append(i + 1)
            sim.append(float(str2[layer - 1]))
            sim_layer.append(sim)
        sim_layer = np.asarray(sim_layer)
        return sim_layer