# Run Usage
#--------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------
import SEIRanalysis

if __name__ == '__main__':
    s = SEIRanalysis.SEIR()
    s.runScenarioOne()
    s.runScenarioFlatteningCurve([0.4, 0.5, 0.6, 0.7, 0.8, 0.9])

    params = [0.7, 2.1, 0.7, 0.4]  # [S,E.I,R]
    days = [30, 60, 90, 120, 150, 180, 210, 240, 270]
    s.runScenarioLockdown(params, days)

    params = [0.7,2.1,0.7,0.4] # [S,E.I,R]
    lockdown = 150
    rho2 = 0.9
    SEIRanalysis.SEIR.runCalculatePeaks(params, lockdown, rho2)

    lockdown = 60
    rho2 = 0.9
    SEIRanalysis.SEIR.runCalculatePeaks(params, lockdown, rho2)