from pods.problems.real_functions import *
import filecmp

def test_modify_coefficient():
    data = delft3d_1objs(dim=4)
    data.home_dir = './'
    x = [0.1, 0.1, 0, 0]
    data.modify_coefficient(x, 'f34_flow/model/', 0)
    assert filecmp.cmp("f34_flow/model/f34.mdf", "f34_flow/model/f34_goal.mdf")


def main():
    test_modify_coefficient()

if __name__ == '__main__':
    main()