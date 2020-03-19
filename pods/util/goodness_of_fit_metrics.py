import numpy as np
class Metrics:
# this class include some common objective funtion
    def nse(self, obs, sim):
        # This is to calculate the Nash Sutcliffe Efficiency (NSE)
        mean_obs = np.mean(obs[:, 1])
        n = np.size(obs, 0)
        m = np.size(sim, 0)
        num = 0.0
        den = 0.0
        for i in range(n):
            den = den + (obs[i, 1] - mean_obs) ** 2
            for j in range(m):
                if float(sim[j, 0]) == obs[i, 0]:
                    print sim[j, 0]
                    num = num + (obs[i, 1] - float(sim[j, 1])) ** 2
                    break
        nse = 1 - (num / den)
        return nse

    def kge(self, obs, sim):
        # This is to calculated the Kling- Gupta efficiency (KGE)
        obs_cal = []
        sim_cal = []
        n = np.size(obs, 0)
        m = np.size(sim, 0)
        for i in range(n):
            for j in range(m):
                if float(sim[j, 0]) == obs[i, 0]:
                    obs_cal.append(obs[i, 1])
                    sim_cal.append(float(sim[j, 1]))
                    break
        obs_cal = np.array(obs_cal)
        sim_cal = np.array(sim_cal)
        a =self.alpha_value(obs_cal, sim_cal)
        b = self.beta_value(obs_cal, sim_cal)
        r = self.r_value(obs_cal, sim_cal)
        v = (1 - r) ** 2 + (1 - a) ** 2 + (1 - b) ** 2
        kge = 1 - np.sqrt(v)
        return kge, a, b, r

    def alpha_value(self, obs, sim):
        # alpha is the ratio between the standard deviation of simulated data and observed data
        sigma1 = np.std(sim) / (len(sim) - 1) ** 0.5 * len(sim) ** 0.5
        sigma2 = np.std(obs) / (len(obs) - 1) ** 0.5 * len(obs) ** 0.5
        return sigma1 / sigma2

    def beta_value(self, obs, sim):
        # beta is the ratio between the mean of simulated data and observed data
        beta1 = np.mean(sim)
        beta2 = np.mean(obs)
        return beta1 / beta2

    def r_value(self, obs, sim):
        # This function is to calculate the correlation coefficient
        covmatrix = np.cov(sim, obs)
        cov = covmatrix[0, 1]
        sigma1 = np.std(sim) / (len(sim) - 1) ** 0.5 * len(sim) ** 0.5
        sigma2 = np.std(obs) / (len(obs) - 1) ** 0.5 * len(obs) ** 0.5
        return cov / sigma1 / sigma2

    def mae(self, obs, sim):
        # This function is to calculate the mean absolute error
        n = np.size(obs, 0)
        m = np.size(sim, 0)
        SAE = 0  # sum of absolute error
        for i in range(n):
            for j in range(m):
                if float(sim[j, 0]) == obs[i, 0]:
                    SAE = SAE + abs(obs[i, 1]-float(sim[j, 1]))
                    break
        mae = SAE / n
        return mae

    def rmse(self, obs, sim):
        # This function is to calculated the Root Mean Squared Error (RMSE)
        n = np.size(obs, 0)
        m = np.size(sim, 0)
        SAE = 0  # sum of absolute error
        for i in range(n):
            for j in range(m):
                if float(sim[j, 0]) == obs[i, 0]:
                    SAE = SAE + (obs[i, 1] - float(sim[j, 1])) ** 2
                    break
        rmse = np.sqrt(SAE / n)
        return rmse

    def fouriernorm(self, obs1, obs2, obs3, sim1, sim2, sim3):
        n = np.size(obs1, 0)
        m = np.size(sim1, 0)
        FN_1 = 0
        FN_2 = 0
        for i in range(n):
            for j in range(m):
                if float(sim1[j, 0]) == obs1[i, 0]:
                    FN_1 = FN_1 + (obs1[i, 1] - float(sim1[j, 1])) ** 2 + (obs2[i, 1] - float(sim2[j, 1])) ** 2 + (obs3[
                                                                                                                       i, 1] - float(
                        sim3[j, 1])) ** 2
                    FN_2 = FN_2 + (obs1[i, 1]) ** 2 + (obs2[i, 1]) ** 2 + (obs3[i, 1]) ** 2
        FN = np.sqrt(FN_1 / n) / np.sqrt(FN_2 / n)
        return FN

    def rmse_norm(self, obs, sim):
        n = np.size(obs, 0)
        m = np.size(sim, 0)
        SAE = 0  # sum of absolute error
        Mean_obs = 0
        for i in range(n):
            for j in range(m):
                if float(sim[j, 0]) == obs[i, 0]:
                    SAE = SAE + (obs[i, 1] - float(sim[j, 1])) ** 2
                    Mean_obs = Mean_obs + (obs[i, 1]) ** 2
                    break
        rmse_norm = np.sqrt(SAE / n) / np.sqrt(Mean_obs / n)
        return rmse_norm

    def rmse_norm_2(self, obs, sim):
        n = np.size(obs, 0)
        m = np.size(sim, 0)
        SAE = 0  # sum of absolute error
        Mean_obs = 0
        for i in range(n):
            for j in range(m):
                if float(sim[j, 0]) == obs[i, 0]:
                    SAE = SAE + (obs[i, 1] - float(sim[j, 1])) ** 2
                    Mean_obs = Mean_obs + (obs[i, 1])
                    break
        rmse_norm = np.sqrt(SAE / n) / (Mean_obs / n)
        return rmse_norm

    def mae_norm(self, obs, sim):
        n = np.size(obs, 0)
        m = np.size(sim, 0)
        SAE = 0  # sum of absolute error
        Mean_obs = 0
        for i in range(n):
            for j in range(m):
                if float(sim[j, 0]) == obs[i, 0]:
                    SAE = SAE + abs(obs[i, 1] - float(sim[j, 1]))
                    Mean_obs =  Mean_obs + abs(obs[i, 1])
                    break
        mae = (SAE / n) / (Mean_obs / n)
        return mae
