# Creating Class Memory Mananger 
class MemoryManager:
   

    def __init__(self):
        self.previous_question=None
        self.previous_answer=None
        self.previous_steps=[]

    # this is getMemory function to  get the whatever question previously asked and answer and steps
    def get_memory(self):
        return {
            "previous_question": self.previous_question,
            "previous_answer": self.previous_answer,
            "previous_steps": self.previous_steps
        }

    def update_memory(self, question, answer, steps):
        self.previous_question = question
        self.previous_answer = answer
        self.previous_steps = steps

    def clear_memory(self):
        self.previous_question = None
        self.previous_answer = None
        self.previous_steps = []
            
         


    