"""

"""

import random
from time import time
import numpy as np
import math



class Rastrigin:
    """Rastrigin function

    .. math::
        f(x_1,\\ldots,x_n)=10n-\\sum_{i=1}^n (x_i^2 - 10 \\cos(2 \\pi x_i))

    subject to

    .. math::
        -5.12 \\leq x_i \\leq 5.12

    Global optimum: :math:`f(0,0,...,0)=0`

    :param dim: Number of dimensions
    :type dim: int

    :ivar dim: Number of dimensions
    :type dim: int
    :ivar xlow: Lower bound constraints
    :type xlow: numpy.array
    :ivar xup: Upper bound constraints
    :type xup: numpy.array
    :ivar info: Problem information
    :type info: string
    :ivar min: Global optimum
    :type min: float
    :ivar integer: Integer variables
    :type integer: numpy.array
    :ivar continuous: Continuous variables
    :type continuous: numpy.array
    """
    def __init__(self, dim=10):
        self.xlow = -5.12 * np.ones(dim)
        self.xup = 5.12 * np.ones(dim)
        self.dim = dim
        self.info = str(dim)+"-dimensional Rastrigin function \n" +\
                             "Global optimum: f(0,0,...,0) = 0"
        self.min = 0
        self.integer = []
        self.continuous = np.arange(0, dim)
        self.workdir = './'

    def objfunction(self, x):
        """Evaluate the Rastrigin function  at x

        :param x: Data point
        :type x: numpy.array
        :return: Value at x
        :rtype: float
        """

        if len(x) != self.dim:
            raise ValueError('Dimension mismatch')
        return 10 * self.dim + sum(x**2 - 10 * np.cos(2 * np.pi * x))


class Ackley:
    """Ackley function

    .. math::
        f(x_1,\\ldots,x_n) = -20\\exp\\left( -0.2 \\sqrt{\\frac{1}{n} \
        \\sum_{j=1}^n x_j^2} \\right) -\\exp \\left( \\frac{1}{n} \
        \\sum{j=1}^n \\cos(2 \\pi x_j) \\right) + 20 - e

    subject to

    .. math::
        -15 \\leq x_i \\leq 20

    Global optimum: :math:`f(0,0,...,0)=0`

    :param dim: Number of dimensions
    :type dim: int

    :ivar dim: Number of dimensions
    :type dim: int
    :ivar xlow: Lower bound constraints
    :type xlow: numpy.array
    :ivar xup: Upper bound constraints
    :type xup: numpy.array
    :ivar info: Problem information:
    :type info: string
    :ivar min: Global optimum
    :type min: float
    :ivar integer: Integer variables
    :type integer: numpy.array
    :ivar continuous: Continuous variables
    :type continuous: numpy.array
    """

    def __init__(self, dim=10):
        self.xlow = -15 * np.ones(dim)
        self.xup = 20 * np.ones(dim)
        self.dim = dim
        self.info = str(dim)+"-dimensional Ackley function \n" +\
                             "Global optimum: f(0,0,...,0) = 0"
        self.min = 0
        self.integer = []
        self.continuous = np.arange(0, dim)
        self.workdir = './'

    def objfunction(self, x):
        """Evaluate the Ackley function  at x

        :param x: Data point
        :type x: numpy.array
        :return: Value at x
        :rtype: float
        """

        if len(x) != self.dim:
            raise ValueError('Dimension mismatch')
        n = float(len(x))
        return -20.0 * np.exp(-0.2*np.sqrt(np.sum(x**2)/n)) - \
            np.exp(np.sum(np.cos(2.0*np.pi*x))/n) + 20 + np.exp(1)


class Michalewicz:
    """Michalewicz function

    .. math::
        f(x_1,\\ldots,x_n) = -\\sum_{i=1}^n \\sin(x_i) \\sin^{20} \\left( \\frac{ix_i^2}{\\pi} \\right)

    subject to

    .. math::
        0 \\leq x_i \\leq \\pi

    :param dim: Number of dimensions
    :type dim: int

    :ivar dim: Number of dimensions
    :type dim: int
    :ivar xlow: Lower bound constraints
    :type xlow: numpy.array
    :ivar xup: Upper bound constraints
    :type xup: numpy.array
    :ivar info: Problem information
    :type info: string
    :ivar min: Global optimum
    :type min: float
    :ivar integer: Integer variables
    :type integer: numpy.array
    :ivar continuous: Continuous variables
    :type continuous: numpy.array
    """
    def __init__(self, dim=10):
        self.xlow = np.zeros(dim)
        self.xup = np.pi * np.ones(dim)
        self.dim = dim
        self.info = str(dim)+"-dimensional Michalewicz function \n" +\
                             "Global optimum: ??"
        self.min = np.NaN
        self.integer = []
        self.continuous = np.arange(0, dim)
        self.workdir = './'

    def objfunction(self, x):
        """Evaluate the Michalewicz function  at x

        :param x: Data point
        :type x: numpy.array
        :return: Value at x
        :rtype: float
        """

        if len(x) != self.dim:
            raise ValueError('Dimension mismatch')
        return -np.sum(np.sin(x) * (np.sin(((1+np.arange(self.dim))
                                            * x**2)/np.pi)) ** 20)


class Levy:
    """Levy function

    Details: https://www.sfu.ca/~ssurjano/levy.html

    Global optimum: :math:`f(1,1,...,1)=0`

    :param dim: Number of dimensions
    :type dim: int

    :ivar dim: Number of dimensions
    :type dim: int
    :ivar xlow: Lower bound constraints
    :type xlow: numpy.array
    :ivar xup: Upper bound constraints
    :type xup: numpy.array
    :ivar info: Problem information
    :type info: string
    :ivar min: Global optimum
    :type min: float
    :ivar integer: Integer variables
    :type integer: numpy.array
    :ivar continuous: Continuous variables
    :type continuous: numpy.array
    """

    def __init__(self, dim=10):
        self.xlow = -10 * np.ones(dim)
        self.xup = 10 * np.ones(dim)
        self.dim = dim
        self.min = 0.0
        self.info = str(dim)+"-dimensional Levy function \n" +\
                             "Global optimum: ?"
        self.integer = []
        self.continuous = np.arange(0, dim)
        self.workdir = './'

    def objfunction(self, x):
        """Evaluate the Levy function  at x

        :param x: Data point
        :return: Value at x
        """
        if len(x) != self.dim:
            raise ValueError('Dimension mismatch')
        w = 1 + (x - 1) / 4
        wp = w[:-1]
        wd = w[-1]
        a = np.sin(np.pi * w[0]) ** 2
        b = sum((wp - 1) ** 2 * (1 + 10 * np.sin(np.pi * wp + 1) ** 2))
        c = (wd - 1) ** 2 * (1 + np.sin(2 * np.pi * wd) ** 2)
        return a + b + c


class Griewank:
    """Griewank function

    .. math::
        f(x_1,\\ldots,x_n) = 1 + \\frac{1}{4000} \\sum_{j=1}^n x_j^2 - \
        \\prod_{j=1}^n \\cos \\left( \\frac{x_i}{\\sqrt{i}} \\right)

    subject to

    .. math::
        -512 \\leq x_i \\leq 512

    Global optimum: :math:`f(0,0,...,0)=0`

    :param dim: Number of dimensions
    :type dim: int

    :ivar dim: Number of dimensions
    :type dim: int
    :ivar xlow: Lower bound constraints
    :type xlow: numpy.array
    :ivar xup: Upper bound constraints
    :type xup: numpy.array
    :ivar info: Problem information
    :type info: string
    :ivar min: Global optimum
    :type min: float
    :ivar integer: Integer variables
    :type integer: numpy.array
    :ivar continuous: Continuous variables
    :type continuous: numpy.array
    """

    def __init__(self, dim=10):
        self.xlow = -512 * np.ones(dim)
        self.xup = 512 * np.ones(dim)
        self.dim = dim
        self.info = str(dim)+"-dimensional Griewank function \n" +\
                             "Global optimum: f(0,0,...,0) = 0"
        self.min = 0
        self.integer = []
        self.continuous = np.arange(0, dim)
        self.workdir = './'

    def objfunction(self, x):
        """Evaluate the Griewank function  at x

        :param x: Data point
        :type x: numpy.array
        :return: Value at x
        :rtype: float
        """

        if len(x) != self.dim:
            raise ValueError('Dimension mismatch')
        total = 1
        for i, y in enumerate(x):
            total *= np.cos(y / np.sqrt(i+1))
        return 1.0 / 4000.0 * sum([y**2 for y in x]) - total + 1


class Rosenbrock:
    """Rosenbrock function

    .. math::
        f(x_1,\\ldots,x_n) = \\sum_{j=1}^{n-1} \
        \\left( 100(x_j^2-x_{j+1})^2 + (1-x_j)^2 \\right)

    subject to

    .. math::
        -2.048 \\leq x_i \\leq 2.048

    Global optimum: :math:`f(1,1,...,1)=0`

    :param dim: Number of dimensions
    :type dim: int

    :ivar dim: Number of dimensions
    :type dim: int
    :ivar xlow: Lower bound constraints
    :type xlow: numpy.array
    :ivar xup: Upper bound constraints
    :type xup: numpy.array
    :ivar info: Problem information
    :type info: string
    :ivar min: Global optimum
    :type min: float
    :ivar integer: Integer variables
    :type integer: numpy.array
    :ivar continuous: Continuous variables
    :type continuous: numpy.array
    """

    def __init__(self, dim=10):
        self.xlow = -2.048 * np.ones(dim)
        self.xup = 2.048 * np.ones(dim)
        self.dim = dim
        self.info = str(dim)+"-dimensional Rosenbrock function \n" +\
                             "Global optimum: f(1,1,...,1) = 0"
        self.min = 0
        self.integer = []
        self.continuous = np.arange(0, dim)
        self.workdir = './'

    def objfunction(self, x):
        """Evaluate the Rosenbrock function  at x

        :param x: Data point
        :type x: numpy.array
        :return: Value at x
        :rtype: float
        """

        if len(x) != self.dim:
            raise ValueError('Dimension mismatch')
        total = 0
        for i in range(len(x) - 1):
            total += 100 * (x[i] ** 2 - x[i+1]) ** 2 + (x[i] - 1) ** 2
        return total


class Schwefel:
    """Schwefel function

    .. math::
        f(x_1,\\ldots,x_n) = \\sum_{j=1}^{n} \
        \\left( -x_j \\sin(\\sqrt{|x_j|}) \\right) + 418.982997 n

    subject to

    .. math::
        -512 \\leq x_i \\leq 512

    Global optimum: :math:`f(420.968746,420.968746,...,420.968746)=0`

    :param dim: Number of dimensions
    :type dim: int

    :ivar dim: Number of dimensions
    :type dim: int
    :ivar xlow: Lower bound constraints
    :type xlow: numpy.array
    :ivar xup: Upper bound constraints
    :type xup: numpy.array
    :ivar info: Problem information
    :type info: string
    :ivar min: Global optimum
    :type min: float
    :ivar integer: Integer variables
    :type integer: numpy.array
    :ivar continuous: Continuous variables
    :type continuous: numpy.array
    """

    def __init__(self, dim=10):
        self.xlow = -512 * np.ones(dim)
        self.xup = 512 * np.ones(dim)
        self.dim = dim
        self.info = str(dim)+"-dimensional Schwefel function \n" +\
                             "Global optimum: f(420.968746,...,420.968746) = 0"
        self.min = 0
        self.integer = []
        self.continuous = np.arange(0, dim)
        self.workdir = './'

    def objfunction(self, x):
        """Evaluate the Schwefel function  at x

        :param x: Data point
        :type x: numpy.array
        :return: Value at x
        :rtype: float
        """

        if len(x) != self.dim:
            raise ValueError('Dimension mismatch')
        return 418.9829 * self.dim - \
            sum([y * np.sin(np.sqrt(abs(y))) for y in x])


class Sphere:
    """Sphere function

    .. math::
        f(x_1,\\ldots,x_n) = \\sum_{j=1}^n x_j^2

    subject to

    .. math::
        -5.12 \\leq x_i \\leq 5.12

    Global optimum: :math:`f(0,0,...,0)=0`

    :param dim: Number of dimensions
    :type dim: int

    :ivar dim: Number of dimensions
    :type dim: int
    :ivar xlow: Lower bound constraints
    :type xlow: numpy.array
    :ivar xup: Upper bound constraints
    :type xup: numpy.array
    :ivar info: Problem information
    :type info: string
    :ivar min: Global optimum
    :type min: float
    :ivar integer: Integer variables
    :type integer: numpy.array
    :ivar continuous: Continuous variables
    :type continuous: numpy.array
    """

    def __init__(self, dim=10):
        self.xlow = -5.12 * np.ones(dim)
        self.xup = 5.12 * np.ones(dim)
        self.dim = dim
        self.info = str(dim)+"-dimensional Sphere function \n" +\
                             "Global optimum: f(0,0,...,0) = 0"
        self.min = 0
        self.integer = []
        self.continuous = np.arange(0, dim)
        self.workdir = './'

    def objfunction(self, x):
        """Evaluate the Sphere function  at x

        :param x: Data point
        :type x: numpy.array
        :return: Value at x
        :rtype: float
        """

        if len(x) != self.dim:
            raise ValueError('Dimension mismatch')
        return np.sum(x ** 2)


class StyblinskiTang:
    """StyblinskiTang function

    .. math::
        f(x_1,\\ldots,x_n) = \\frac{1}{2} \\sum_{j=1}^n  \
        \\left(x_j^4 -16x_j^2 +5x_j \\right)

    subject to

    .. math::
        -5 \\leq x_i \\leq 5

    Global optimum: :math:`f(-2.903534,-2.903534,...,-2.903534)=\
    -39.16599 \\cdot n`

    :param dim: Number of dimensions
    :type dim: int

    :ivar dim: Number of dimensions
    :type dim: int
    :ivar xlow: Lower bound constraints
    :type xlow: numpy.array
    :ivar xup: Upper bound constraints
    :type xup: numpy.array
    :ivar info: Problem information
    :type info: string
    :ivar min: Global optimum
    :type min: float
    :ivar integer: Integer variables
    :type integer: numpy.array
    :ivar continuous: Continuous variables
    :type continuous: numpy.array
    """

    def __init__(self, dim=10):
        self.xlow = -5 * np.ones(dim)
        self.xup = 5 * np.ones(dim)
        self.dim = dim
        self.info = str(dim)+"-dimensional Styblinski-Tang function \n" +\
                             "Global optimum: f(-2.903534,...,-2.903534) = " +\
                             str(-39.16599*dim)
        self.min = -39.16599*dim
        self.integer = []
        self.continuous = np.arange(0, dim)
        self.workdir = './'

    def objfunction(self, x):
        """Evaluate the StyblinskiTang function  at x

        :param x: Data point
        :type x: numpy.array
        :return: Value at x
        :rtype: float
        """

        if len(x) != self.dim:
            raise ValueError('Dimension mismatch')
        return 0.5*np.sum(x ** 4 - 16 * x ** 2 + 5 * x)


class Whitley:
    """Quartic function

    .. math::
        f(x_1,\\ldots,x_n) = \\sum_{i=1}^n \\sum_{j=1}^n \
        \\left( \\frac{(100(x_i^2-x_j)^2+(1-x_j)^2)^2}{4000} \
        - \\cos(100(x_i^2-x_j)^2 + (1-x_j)^2 ) + 1 \\right)

    subject to

    .. math::
        -10.24 \\leq x_i \\leq 10.24

    Global optimum: :math:`f(1,1,...,1)=0`

    :param dim: Number of dimensions
    :type dim: int

    :ivar dim: Number of dimensions
    :type dim: int
    :ivar xlow: Lower bound constraints
    :type xlow: numpy.array
    :ivar xup: Upper bound constraints
    :type xup: numpy.array
    :ivar info: Problem information
    :type info: string
    :ivar min: Global optimum
    :type min: float
    :ivar integer: Integer variables
    :type integer: numpy.array
    :ivar continuous: Continuous variables
    :type continuous: numpy.array
    """

    def __init__(self, dim=10):
        self.xlow = -10.24 * np.ones(dim)
        self.xup = 10.24 * np.ones(dim)
        self.dim = dim
        self.info = str(dim)+"-dimensional Whitley function \n" +\
                             "Global optimum: f(1,1,...,1) = 0"
        self.min = 0
        self.integer = []
        self.continuous = np.arange(0, dim)
        self.workdir = './'

    def objfunction(self, x):
        """Evaluate the Whitley function  at x

        :param x: Data point
        :type x: numpy.array
        :return: Value at x
        :rtype: float
        """

        if len(x) != self.dim:
            raise ValueError('Dimension mismatch')
        total = 0
        for i in range(len(x)):
            for j in range(len(x)):
                temp = 100*((x[i]**2)-x[j]) + (1-x[j])**2
                total += (float(temp**2)/4000.0) - np.cos(temp) + 1
        return total


class Weierstrass:

    def __init__(self, dim=10):
        self.xlow = -0.5 * np.ones(dim)
        self.xup = 0.5 * np.ones(dim)
        self.dim = dim
        self.info = str(dim)+"-dimensional Weierstrass function \n" +\
                             "Global optimum: f(0,0,...,0) = 0"
        self.min = 4.0
        self.integer = []
        self.continuous = np.arange(0, dim)
        self.workdir = './'

    def objfunction(self, x):
        """Evaluate the Weiestrass function  at x

        :param x: Data point
        :type x: numpy.array
        :return: Value at x
        :rtype: float
        """

        a = 0.5
        b = 3
        k_max = 20

        def sub_sum(x):
            return sum([a ** k * np.cos(2 * math.pi * (b ** k) * (x + 0.5)) for k in range(k_max)])

        val = sum([sub_sum(x0) for x0 in x]) - (
                    len(x) * sum([a ** k * np.cos(2 * math.pi * (b ** k) * 0.5) for k in range(k_max)]))

        return val


if __name__ == "__main__":

    print("\n========================= Rastrigin =======================")
    fun = Rastrigin(dim=3)
    print(fun.info)
    print("Rastrigin(1,1,1) = " + str(fun.objfunction(np.array([1, 1, 1]))))
    print("Continuous variables: " + str(fun.continuous))
    print("Integer variables: " + str(fun.integer))


    print("\n========================= Ackley =======================")
    fun = Ackley(dim=3)
    print(fun.info)
    print("Ackley(1,1,1) = " + str(fun.objfunction(np.array([1, 1, 1]))))


    print("\n========================= Levy =======================")
    fun = Levy(dim=3)
    print(fun.info)
    print("Levy(1,1,1) = " + str(fun.objfunction(np.array([1, 1, 1]))))


    print("\n========================= Schwefel =======================")
    fun = Schwefel(dim=3)
    print(fun.info)
    print("Schwefel(1,1,1) = " + str(fun.objfunction(np.array([1, 1, 1]))))
    print("Continuous variables: " + str(fun.continuous))
    print("Integer variables: " + str(fun.integer))

    #
    print("\n======================= Styblinski-Tang =====================")
    fun = StyblinskiTang(dim=3)
    print(fun.info)
    print("StyblinskiTang(-2.903534,-2.903534,-2.903534) = " +
          str(fun.objfunction(np.array([-2.903534, -2.903534, -2.903534]))))
    print("Continuous variables: " + str(fun.continuous))
    print("Integer variables: " + str(fun.integer))
    #
    print("\n========================= Whitley =======================")
    fun = Whitley(dim=3)
    print(fun.info)
    print("Whitley(1,1,1) = " + str(fun.objfunction(np.array([1, 1, 1]))))
    print("Continuous variables: " + str(fun.continuous))
    print("Integer variables: " + str(fun.integer))

    print("\n========================= Michalewicz =======================")
    fun = Michalewicz(dim=2)
    print(fun.info)
    print("Michalewicz(2.20, 1.57) = " +
          str(fun.objfunction(np.array([2.20, 1.57]))))
    print("Continuous variables: " + str(fun.continuous))
    print("Integer variables: " + str(fun.integer))

    print("\n========================= Weiestrass =======================")
    fun = Weierstrass(dim=10)
    print(fun.info)
    print(np.zeros((10,)))
    print(fun.objfunction(np.zeros((10,))))
