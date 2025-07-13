from meta_learner import MetaLearner


def test_q_learning_update():
    learner = MetaLearner(actions=["a", "b"])
    action = learner.choose_action("intent")
    learner.update("intent", action, 1.0, "intent")
    assert ("intent", action) in learner.q_table
