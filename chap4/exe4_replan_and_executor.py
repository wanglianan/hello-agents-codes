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

class Planner:
    """
    负责生成初始计划和失败时的重规划
    当某步失败时，将**已完成的步骤+结果+失败步骤+失败原因**作为上下文，调用 LLM 重新生成**剩余步骤的新计划**，而非从头重建整个计划。
    """
    def __init__(self,llm_client:HelloAgentsLLM):
      self.llm_client = llm_client

    def _parse_plan(self, response_text: str) -> list[str]:
        try:
            plan_str = response_text.split("```python")[1].split("```")[0].strip()
            plan = ast.literal_eval(plan_str)
            return plan if isinstance(plan, list) else []
        except (ValueError, SyntaxError, IndexError) as e:
            print(f"❌ 解析计划时出错: {e}")
            print(f"原始响应: {response_text}")
            return []
        except Exception as e:
            print(f"❌ 解析计划时发生未知错误: {e}")
            return []

    def replan(self, question: str, original_plan: list[str],
               completed_steps: str, failed_step: str,
               failure_reason: str) -> list[str]:
        """
        基于已完成的步骤和失败信息，重新规划剩余步骤
        - question: 原始问题
        - original_plan: 原始完整计划
        - completed_steps: 已成功完成的步骤与结果（作为上下文）
        - failed_step: 当前失败的步骤描述
        - failure_reason: 失败原因（即该步骤的执行结果）
        """
        prompt = REPLANNER_PROMPT_TEMPLATE.format(
          question = question,
          original_plan = original_plan,
          completed_steps = completed_steps if completed_steps else "无",
          failed_step = failed_step,
          failure_reason = failure_reason
          )
        messages = ["role":"user","prompt":"prompt"]
        print("\n--- 正在重新规划剩余步骤 ---")
        response = self.llm_client.think(messages) or ""
        print(f"✅ 新计划已生成:\n{response_text}")

        return self._parse_plan(response_text)
    
