class Executor:
  def __init_(self, llm_client:HelloAgentsLLM, planner:Planner, max_replan_attemps:int=3):
    self.llm_client = HelloAgentsLLM
    self.planner = Planner
    self.max_replan_attemps = max_replan_attemps

  def _verify_step(self, question:str, step:str, result:str):
    """
    使用LLM验证步骤是否执行成功，需要输入有question，current_step，step_result
    返回结果为SUCCESS代表验证成功，其他则为验证失败
    """
    prompt = VERIFICATION_PROMPT_TEMPLATE.format(question=question,current_step=step,result=result)
    messages = ["role":"user","prompt":"prompt"]
    response = self.llm_client.think(messages) or ""
    return "SUCCESS" in response.upper()

    
    
