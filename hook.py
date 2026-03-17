from langchain.agents.middleware import before_model

@before_model
def log_before_model(state, runtime) :
    # 내부 로직
    return None