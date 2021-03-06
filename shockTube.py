# coding: utf-8
"""
Shock Tube Simulations Considering Boundary Effects

Ignition delay time computations in a high-pressure reflected shock tube reactor
DMM shock tube experiments by Jacobs et al., doi.org/10.1016/j.combustflame.2018.12.026
The mechanism is adopted from Li et al.,doi.org/10.1016/j.combustflame.2021.111583
"""
import numpy as np
import matplotlib.pyplot as plt
import time
import cantera as ct

print('Running Cantera version: ' + ct.__version__)


def get_IDT(solution_results, signal='T'):
    """
    calculate ignition delay time according to the specified signal, i.e.
    Maximum temperature/pressure rise rate or peak concentration for the specified species.
    :param solution_results: Reactor thermodynamic state.
    :param signal: string, only 'T', 'P', 'OH'(or other species name) are optional.
    :return: ignition delay time
    """
    tau_idt = 0
    scope_max = 0
    if signal.upper() not in ['T', 'P']:
        return solution_results.t[solution_results(signal).Y.argmax()]
    else:
        y = solution_results.T if signal.upper() == 'T' else solution_results.P
        for i in range(len(solution_results.t) - 1):
            temp_scope = (y[i + 1] - y[i]) / (solution_results.t[i + 1] - solution_results.t[i])
            if temp_scope > scope_max:
                scope_max = temp_scope
                tau_idt = solution_results.t[i]
    return tau_idt


def run_cal_ideal(gas, end_time=0.01, print_step=20):
    r = ct.Reactor(contents=gas)
    reactorNetwork = ct.ReactorNet([r])

    # create an array of solution states
    timeHistory = ct.SolutionArray(gas, extra=['t'])

    t = 0
    counter = 1
    while t < end_time:
        t = reactorNetwork.step()
        if counter % print_step == 0:
            timeHistory.append(r.thermo.state, t=t)
        counter += 1
    return get_IDT(timeHistory) * 1000  # Units: ms


def run_cal_real(gas, end_time=0.005, print_step=20):
    r1 = ct.Reactor(contents=gas)
    r1.volume = 1

    gas2 = gas
    gas2.X = {'H2': 1}
    r2 = ct.Reactor(contents=gas2)

    def v(t):
        V_t = np.array(
            [[0, 2.00E-04, 4.00E-04, 6.00E-04, 8.00E-04, 0.001, 0.0012, 0.0014, 0.0016, 0.0018, 0.002, 0.0022,
              0.0024, 0.0026, 0.0028, 0.003, 0.0032, 0.0034, 0.0036, 0.0038, 0.004, 0.0042, 0.0044, 0.0046,
              0.0048,
              0.005, 0.0052, 0.0054, 0.0056, 0.0058, 0.006, 0.0062, 0.0064, 0.0066, 0.0068, 0.007, 0.0072,
              0.0074,
              0.0076, 0.0078, 0.008, 0.0082, 0.0084, 0.0086, 0.0088, 0.009],
             [1, 0.990523087, 0.981281978, 0.972267286, 0.963470131, 0.95488211, 0.946495261, 0.938302037,
              0.930295277, 0.922468181, 0.91481429, 0.907327458, 0.900001842, 0.892831873, 0.885812248,
              0.878937911,
              0.872204038, 0.865606022, 0.859139466, 0.852800165, 0.846584099, 0.840487423, 0.834506453,
              0.828637663,
              0.822877673, 0.817223244, 0.811671266, 0.806218758, 0.800862855, 0.795600807, 0.790429969,
              0.7853478,
              0.780351855, 0.775439782, 0.770609317, 0.765858279, 0.761184567, 0.756586156, 0.752061095,
              0.747607501,
              0.743223558, 0.738907513, 0.734657673, 0.730472404, 0.726350127, 0.722289314]])
        for i in range(len(V_t[0]) - 1):
            if V_t[0][i] <= t < V_t[0][i + 1]:
                return (V_t[1][i + 1] - V_t[1][i]) / (V_t[0][i + 1] - V_t[0][i])
        return (V_t[1][-1] - V_t[1][-2]) / (V_t[0][-1] - V_t[0][-2])

    w = ct.Wall(r1, r2, velocity=v)

    reactorNetwork = ct.ReactorNet([r1, r2])

    # create an array of solution states
    timeHistory = ct.SolutionArray(gas, extra=['t'])

    t = 0
    counter = 1
    while t < end_time:
        t = reactorNetwork.step()

        if counter % print_step == 0:
            timeHistory.append(r1.thermo.state, t=t)
        counter += 1

    return get_IDT(timeHistory) * 1000  # Units: ms


if __name__ == '__main__':
    # Load the real gas mechanism:
    gas_ideal = ct.Solution('DMM-test.yaml', 'gas')
    gas_real = ct.Solution('DMM-test.yaml', 'gas')

    print('\n\nTemperature    IDT_ideal(ms)    IDT_real(ms)    Time cost(s)')

    temperature = np.array([700, 750, 800, 850, 900, 950, 1000, 1050, 1100, 1150, 1200, 1250])
    pressure = 2.0E6  # 20 bar
    idt_ideal = np.zeros(len(temperature))
    idt_real = np.zeros(len(temperature))
    for i, T in enumerate(temperature):
        t0 = time.time()

        # run the calculation of ideal conditions
        gas_ideal.TPX = [T, pressure, {'CH3OCH2OCH3': 4.9880287E-2,
                                       'O2': 1.9952115E-1,
                                       'N2': 7.5059856E-1,
                                       'HE': 4.9880287E-9,
                                       'H2O': 4.9880287E-9}]
        idt_ideal[i] = run_cal_ideal(gas_ideal, end_time=0.005)

        # run the calculation considering boundary effects
        gas_real.TPX = [T, pressure, {'CH3OCH2OCH3': 4.9880287E-2,
                                      'O2': 1.9952115E-1,
                                      'N2': 7.5059856E-1,
                                      'HE': 4.9880287E-9,
                                      'H2O': 4.9880287E-9}]
        idt_real[i] = run_cal_real(gas_real, end_time=0.005)

        t1 = time.time()

        print("{}K            {:.4f}          {:.4f}          {:.2f}".format(T, idt_ideal[i], idt_real[i], t1 - t0))

    # Figure: ignition delay (tau) vs. the inverse of temperature (1000/T).
    idt_chemkin = np.array([2.96E+00, 1.91E+00, 1.53E+00, 1.15E+00, 8.43E-01, 6.47E-01,
                            5.04E-01, 3.77E-01, 2.48E-01, 1.39E-01, 7.16E-02, 3.62E-02])
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(1000 / temperature, idt_chemkin, '*', linewidth=2.0, color='r')
    ax.plot(1000 / temperature, idt_ideal, '-', linewidth=2.0, color='b')
    ax.plot(1000 / temperature, idt_real, '-.', linewidth=2.0, color='g')

    ax.set_ylabel(r'Ignition Delay (ms)', fontsize=14)
    ax.set_xlabel(r'1000/T (K$^\mathdefault{-1}$)', fontsize=14)
    plt.yscale('log')

    # Add a second axis on top to plot the temperature for better readability
    ax2 = ax.twiny()
    ticks = ax.get_xticks()
    ax2.set_xticks(ticks)
    ax2.set_xticklabels((1000 / ticks).round(1))
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xlabel('Temperature (K)', fontsize=14)

    ax.legend(['Chemkin', 'Cantera-ideal', 'Cantera-real'], frameon=False, loc='upper left')

    # If you want to save the plot, uncomment this line (and edit as you see fit):
    # plt.savefig('NTC_nDodecane_40atm.pdf', dpi=350, format='pdf')

    # Show the plots.
    plt.show()
