from post_analysis import Postprocessing

def test_read_simulation_data():
    filename =  "../0/ZCURU.dat"
    posttool = Postprocessing()
    v_1_2 = posttool.read_simulation_data(filename, 1, 2)
    # check if the the simulation result read is in shape (301, 2)
    assert v_1_2.shape == (301, 2)
    assert v_1_2[1][1] == 9.60639700e-17



