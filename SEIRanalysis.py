# SEIR model class definition
# Bogdan Hlevca, Markham, Ontario, Canada
#   Code inspired by Tirthajyoti Sarkar, Fremont, CA
# April 2020

import numpy as np
import matplotlib.pyplot as plt

class SEIR:
    def __init__(self,
                 init_vals=[1 - 1/1000, 1/1000, 0, 0], 
                 params_=[0.2,1.75,0.5,0.9]):
        """
        Initializes and sets the initial lists and parameters
        Arguments:
                init_vals: Fractions of population in the S, E, I, and R categories
                params_: Dynamical parameters - alpha, beta, gamma, and rho.
                Here the last parameter 'rho' models social distancing factor.
        """
        # Initial values
        self.s0 = init_vals[0]
        self.e0 = init_vals[1]
        self.i0 = init_vals[2]
        self.r0 = init_vals[3]
        # Lists
        self.s, self.e, self.i, self.r = [self.s0], [self.e0], [self.i0], [self.r0]
        # Dynamical parameters
        self.alpha = params_[0]
        self.beta = params_[1]
        self.gamma = params_[2]
        self.rho = params_[3]
        # All parameters together in a list
        self.params_ = [self.alpha,self.beta,self.gamma,self.rho]
        # All final values together in a list
        self.vals_ = [self.s[-1], self.e[-1], self.i[-1], self.r[-1]]

    # --------------------------------------------------------------------------------------------------------------
    @staticmethod
    def runScenarioOne():
        s = SEIR()
        r,dt = s.run(t_max=90, dt=0.1)
        s.plot(r, dt)

    @staticmethod
    def runScenarioFlatteningCurve(social_dist):
        social_dist = social_dist #[0.4, 0.5, 0.6, 0.7, 0.8]
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111)
        dt = 0.1
        for d in social_dist:
            s = SEIR()
            s.rho = d
            r,dt = s.run(t_max=120, dt=dt)
            ax.plot(r[:, 2], lw=3)
        plt.title('Flattening the curve with social distancing', fontsize=18)
        plt.legend(["Social distancing factor: " + str(d) for d in social_dist],
                   fontsize=15)
        ax.set_xlabel('Time [days]', fontsize=16)
        ax.set_ylabel('Fraction of Population', fontsize=16)
        plt.grid(True)

        xticks = s.computeTicks(range(0, len(r)), 100)
        xticklabels = (xticks * dt).astype(np.float)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels, fontsize=15)
        plt.setp(ax.get_yticklabels(), fontsize=15)
        plt.show()

    @staticmethod
    def runScenarioLockdown(parameters, days):
        p = parameters #[0.7, 2.1, 0.7, 0.4]
        days = days #[60, 90, 120, 150, 180, 210]
        s = SEIR(params_=p)
        dt = 0.1
        fig, ax = plt.subplots(3, 3, figsize=(15, 12))
        axes = ax.ravel()

        dmax=max(days)
        rmax, dt = s.run(t_max=dmax, dt=dt)
        for i, d in enumerate(days):
            r,dt = s.run(t_max=d, dt=dt)
            axes[i].plot(r[:, 0], lw=3)
            axes[i].set_title('Lockdown for {} days'.format(d), fontsize=16)
            axes[i].set_xlabel('Time [days]', fontsize=14)
            axes[i].set_ylabel('Susceptible fraction', fontsize=14)
            axes[i].set_xlim(0, 1800)
            axes[i].set_ylim(0.5, 1.0)
            axes[i].grid(True)
            plt.subplots_adjust(bottom=0.12)
            xticks = s.computeTicks(range(0, len(rmax)), 500)
            xticklabels = (xticks * dt).astype(np.float)
            axes[i].set_xticks(xticks)
            axes[i].set_xticklabels(xticklabels, fontsize=12)
            plt.setp(axes[i].get_yticklabels(), fontsize=12)
        fig.tight_layout()
        plt.show()

    @staticmethod
    def runCalculatePeaks(params, lockdown, rho2):
        s1 = SEIR(params_=params)
        s1.rho = 0.45
        r1,dt1 = s1.run(t_max=lockdown, dt=0.1)
        new_init = s1.vals_
        s2 = SEIR(init_vals=new_init,
                  params_=params)
        s2.rho = rho2
        r2,dt2 = s2.run(t_max=135, dt=0.1, reset=False)
        r3 = np.vstack((r1, r2))
        s2.plot_var(r3[:, 2], var_name='Infected',dt=dt1)


    def reinitialize(self,init_vals,verbose=False):
        """
        Re-initializes with new values
        """
        assert len(init_vals)==4,"Four initial values are expected"
        assert type(init_vals)==list, "Initial values are expected in a list"
        # Initial values
        self.s0 = init_vals[0]
        self.e0 = init_vals[1]
        self.i0 = init_vals[2]
        self.r0 = init_vals[3]
        
        if verbose:
            print("Initialized with the following values\n"+"-"*50)
            print("S0: ",self.s0)
            print("E0: ",self.e0)
            print("I0: ",self.i0)
            print("R0: ",self.r0)
    
    def set_params(self,params_,verbose=False):
        """
        Sets the dynamical parameters value
        """
        assert len(params_)==4,"Four parameter values are expected"
        assert type(params_)==list, "Parameter values are expected in a list"
        # Dynamical parameters
        self.alpha = params_[0]
        self.beta = params_[1]
        self.gamma = params_[2]
        self.rho = params_[3]
        self.params_ = [self.alpha,self.beta,self.gamma,self.rho]
        
        if verbose:
            print("Set the following parameter values\n"+"-"*50)
            print("alpha: ",self.alpha)
            print("beta: ",self.beta)
            print("gamma: ",self.gamma)
            print("rho: ",self.rho)
        
    def reset(self):
        """
        Resets the internal lists to zero-state
        """
        self.s, self.e, self.i, self.r = [self.s0], [self.e0], [self.i0], [self.r0]
    
    def run(self,t_max=100,dt=0.1,reset=True):
        """
        Runs the dynamical simulation
        Arguments:
                t_max: Maximum simulation time, e.g. 20 or 100 (can be thought of days)
                dt: Time step interval e.g. 0.1 or 0.02, a small value
                reset: A flag to reset the internal lists (restarts the simulation from initial values)
        """
        if reset:
            self.reset()
        # Time step array
        t = np.linspace(0, t_max, int(t_max/dt) + 1)
        # Temp lists
        S, E, I, R = self.s, self.e, self.i, self.r
        # Temp parameters
        alpha, beta, gamma, rho = self.alpha,self.beta,self.gamma,self.rho
        dt = t[1] - t[0]
        # Loop
        for _ in t[1:]:
            next_S = S[-1] - (rho*beta*S[-1]*I[-1])*dt
            next_E = E[-1] + (rho*beta*S[-1]*I[-1] - alpha*E[-1])*dt
            next_I = I[-1] + (alpha*E[-1] - gamma*I[-1])*dt
            next_R = R[-1] + (gamma*I[-1])*dt
            S.append(next_S)
            E.append(next_E)
            I.append(next_I)
            R.append(next_R)
        # Stack results
        result = np.stack([S, E, I, R]).T
        self.s, self.e, self.i, self.r = S, E, I, R
        # Update final values
        self.vals_ = [self.s[-1], self.e[-1], self.i[-1], self.r[-1]]
        
        return result,dt

    def computeTicks(self, x, step=5):
        """
        Computes domain with given step encompassing series x
        @ params
        x    - Required - A list-like object of integers or floats
        step - Optional - Tick frequency
        """
        import math as Math
        xMax, xMin = Math.ceil(max(x)), Math.floor(min(x))
        dMax, dMin = xMax + abs((xMax % step) - step) + (step if (xMax % step != 0) else 0), xMin - abs((xMin % step))
        ticks = np.array(range(dMin, dMax, step))
        return ticks


    def plot(self,results=None, dt=None, title=None):
        """
        Plots the basic results
        """
        # Runs a simulation is no result is provided
        if results is None:
            results = self.run()
        # Plot
        fig = plt.figure(figsize=(12,8))
        ax = fig.add_subplot(111)
        ax.plot(np.array(range(0, len(results))), results,lw=3)
        if title is None:
            plt.title('Principle of SEIR Model',fontsize=18)
        else:
            plt.title(title, fontsize=18)
        ax.legend(['Susceptible', 'Exposed', 'Infected', 'Recovered'],
                   fontsize=15)
        ax.set_xlabel('Time [days]',fontsize=16)
        ax.set_ylabel('Fraction of Population',fontsize=16)
        plt.grid(True)

        xticks = self.computeTicks(range(0, len(results)), 100)
        xticklabels = (xticks*dt).astype(np.float)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels, fontsize=15)
        plt.setp(ax.get_yticklabels(), fontsize=15)
        plt.show()


    def plot_var(
        self,
        var,
        dt=None,
        var_name=None,
        show=True):
        """
        Plots the given variable
        Expect a list or Numpy array as the variable
        If var is None, plots the infected fraction
        """
        if var is None:
            var = self.i
        fig = plt.figure(figsize=(12,8))
        ax = fig.add_subplot(111)
        ax.plot(var,lw=3,c='blue')
        ax.set_title('Demonstration SEIR Model',fontsize=18)
        if var_name is not None:
            plt.legend([var_name],fontsize=15)
        ax.set_xlabel('Time [days]',fontsize=16)
        ax.set_ylabel('Percentage of Population',fontsize=16)
        plt.grid(True)
        xticks = self.computeTicks(range(0, len(var)), 300)
        xticklabels = (xticks * dt).astype(np.float)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels, fontsize=16)
        plt.setp(ax.get_yticklabels(), fontsize=16)
        if show:
            plt.show()