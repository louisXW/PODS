#!/usr/bin/env python
import numpy as np
import time
import logging
import multiprocessing

# logger = logging.getLogger(__name__)

class Ackley_1obj:
    #  Details: http://www.cs.unm.edu/~neal.holts/dga/benchmarkFunction/ackley.html
    #  Global optimum: f(0,0,...,0)=0
    def __init__(self, dim=10):
        self.xlow = -15 * np.ones(dim)
        self.xup = 20 * np.ones(dim)
        self.dim = dim
        self.no_sub_objs = 1
        self.info = str(dim)+"-dimensional Ackley function \n" +\
                             "Global optimum: f(0,0,...,0) = 0 \n" + \
                            str(self.no_sub_objs) + "-constituents problems"
        self.integer = []
        self.continuous = np.arange(0, dim)
        self.workdir = './'

    def objfunction(self, x, simid, simiter):
        simid = simid
        simiter = simiter
        logging.info('The %d iteration %d simulation called objfunction' % (simiter, simid))
        if len(x) != self.dim:
            raise ValueError('Dimension mismatch')
        n = float(len(x))
        sub_obj1 = -20.0 * np.exp(-0.2*np.sqrt(sum(x**2)/n)) - np.exp(sum(np.cos(2.0*np.pi*x))/n)
        sub_obj2 = -20.0 * np.exp(-0.2*np.sqrt(sum(x**2)/n)) - np.exp(sum(np.cos(2.0*np.pi*x))/n)

        print 'sub_obj1', sub_obj1
        print 'sub_obj2', sub_obj2

        sub_objs = []
        sub_objs.append(sub_obj1)

        # sub_objs.append(sub_obj2)

        if len(sub_objs) != self.no_sub_objs:
            raise ValueError('Number of sub objectives mismatch')

        parms = x.tolist()
        with multiprocessing.Lock():
            fp = open(self.workdir + "result/pysot_result.txt", "a")
            fp.write("%s\t%s\t%s\t@%s\n" % (simiter, simid, sub_objs, parms))
            fp.close()

        # return self.sub_obj
        return sub_objs

class Ackley_2obj:
    #  Details: http://www.cs.unm.edu/~neal.holts/dga/benchmarkFunction/ackley.html
    #  Global optimum: f(0,0,...,0)=0
    def __init__(self, dim=10):
        self.xlow = -15 * np.ones(dim)
        self.xup = 20 * np.ones(dim)
        self.dim = dim
        self.no_sub_objs = 2
        self.info = str(dim)+"-dimensional Ackley function \n" +\
                             "Global optimum: f(0,0,...,0) = 0 \n" + \
                            str(self.no_sub_objs) + "-constituents problems"
        self.integer = []
        self.continuous = np.arange(0, dim)
        self.workdir = './'


    def objfunction(self, x, simid, simiter):
        simid = simid
        simiter = simiter
        logging.info('The %d iteration %d simulation called objfunction' % (simiter, simid))
        if len(x) != self.dim:
            raise ValueError('Dimension mismatch')
        n = float(len(x))
        sub_obj1 = -20.0 * np.exp(-0.2*np.sqrt(sum(x**2)/n)) - np.exp(sum(np.cos(2.0*np.pi*x))/n)
        sub_obj2 = -20.0 * np.exp(-0.2*np.sqrt(sum(x**2)/n)) - np.exp(sum(np.cos(2.0*np.pi*x))/n)

        print 'sub_obj1', sub_obj1
        print 'sub_obj2', sub_obj2

        sub_objs = []
        sub_objs.append(sub_obj1)
        sub_objs.append(sub_obj2)

        if len(sub_objs) != self.no_sub_objs:
            raise ValueError('Number of sub objectives mismatch')

        parms = x.tolist()
        fp = open(self.workdir + "result/pysot_result.txt", "a")
        fp.write("%s\t%s\t%s\t@%s\n" % (simiter, simid, sub_objs, parms))
        fp.close()

        # return self.sub_obj
        return sub_objs


class Ackley_3obj:
    #  Details: http://www.cs.unm.edu/~neal.holts/dga/benchmarkFunction/ackley.html
    #  Global optimum: f(0,0,...,0)=0
    def __init__(self, dim=10):
        self.xlow = -15 * np.ones(dim)
        self.xup = 20 * np.ones(dim)
        self.dim = dim
        self.no_sub_objs = 3
        self.info = str(dim)+"-dimensional Ackley function \n" +\
                             "Global optimum: f(0,0,...,0) = 0 \n" + \
                            str(self.no_sub_objs) + "-constituents problems"
        self.integer = []
        self.continuous = np.arange(0, dim)
        self.workdir = './'


    def objfunction(self, x, simid, simiter):
        simid = simid
        simiter = simiter
        logging.info('The %d iteration %d simulation called objfunction' % (simiter, simid))
        if len(x) != self.dim:
            raise ValueError('Dimension mismatch')
        n = float(len(x))
        sub_obj1 = -20.0 * np.exp(-0.2*np.sqrt(sum(x**2)/n)) - np.exp(sum(np.cos(2.0*np.pi*x))/n)
        sub_obj2 = -20.0 * np.exp(-0.2*np.sqrt(sum(x**2)/n)) - np.exp(sum(np.cos(2.0*np.pi*x))/n)
        sub_obj3 = -20.0 * np.exp(-0.2*np.sqrt(sum(x**2)/n)) - np.exp(sum(np.cos(2.0*np.pi*x))/n)


        print 'sub_obj1', sub_obj1
        print 'sub_obj2', sub_obj2
        print 'sub_obj3', sub_obj3

        sub_objs = []
        sub_objs.append(sub_obj1)
        sub_objs.append(sub_obj2)
        sub_objs.append(sub_obj3)

        if len(sub_objs) != self.no_sub_objs:
            raise ValueError('Number of sub objectives mismatch')

        parms = x.tolist()
        fp = open(self.workdir + "result/pysot_result.txt", "a")
        fp.write("%s\t%s\t%s\t@%s\n" % (simiter, simid, sub_objs, parms))
        fp.close()

        # return self.sub_obj
        return sub_objs
