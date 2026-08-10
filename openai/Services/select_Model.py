def select_model(problem_type):
   
    if problem_type in ["arithmetic", "equation"]:
        return "llama"

    return "gemini"