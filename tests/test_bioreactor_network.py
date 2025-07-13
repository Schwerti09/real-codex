import numpy as np
from bioreactor_network_optimization import BioreactorNetworkOptimizer, SensorState

def test_optimizer():
    optimizer = BioreactorNetworkOptimizer(n_reactors=2)
    states = [
        SensorState(reactor_id="r1", light=100, temperature=25, co2=0.03, nutrients=1.2, ph=7.5),
        SensorState(reactor_id="r2", light=120, temperature=26, co2=0.04, nutrients=1.3, ph=7.4),
    ]
    actions, absorptions = optimizer.process_states(states)
    assert len(actions) == 2
    assert len(absorptions) == 2
    assert all(isinstance(a, float) for a in absorptions)
