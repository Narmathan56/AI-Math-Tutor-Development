
from uuid import uuid4
# Creating Class Memory Mananger 
class MemoryManager:
   

    def __init__(self):
        self.solution_id = None
        self.step_explanations = {}
        self.previous_question=None
        self.previous_answer=None
        self.previous_steps=[]

    # this is getMemory function to  get the whatever question previously asked and answer and steps
    def get_memory(self):
        return {
            "previous_question": self.previous_question,
            "previous_answer": self.previous_answer,
            "solution_id": self.solution_id,
            "previous_steps": self.previous_steps
        }

    def update_memory(self, question, answer, steps):
        self.previous_question = question
        self.previous_answer = answer
        self.previous_steps = steps
        self.solution_id = str(uuid4())
        self.step_explanations = {}

    def clear_memory(self):
        self.previous_question = None
        self.previous_answer = None
        self.previous_steps = []
        self.solution_id = None
        self.step_explanations = {}



    def get_step_context(self, solution_id, step_id):
       if not self.solution_id or solution_id != self.solution_id:
         raise ValueError("This solution is no longer available.")

    # Frontend step IDs use step-1, step-2, etc.
       if not isinstance(step_id, str) or not step_id.startswith("step-"):
         raise ValueError("Invalid step ID.")

       number = step_id.removeprefix("step-")

       if not number.isascii() or not number.isdigit():
         raise ValueError("Invalid step ID.")

       index = int(number) - 1

       if index < 0 or index >= len(self.previous_steps):
         raise ValueError("Step does not exist.")

       return {
         "question": self.previous_question,
         "current": self.previous_steps[index],
         "previous": self.previous_steps[index - 1] if index > 0 else None,
    }     
            
         


    