# --- x. 步骤验证器 (Executor) 定义 ---
VERIFICATION_PROMPT_TEMPLATE = """
#角色定位
你是一位顶级的AI执行步骤验证专家。

# 固定任务
你的任务是针对提出的问题和获取到的当前任务描述和执行结果进行分析验证，验证当前任务执行成功还是失败。
你将收到原始问题、完整的计划、以及当前执行子任务的已经完成的子任务描述和执行结果。
请你专注于验证“当前步骤和子任务”，并仅验证该步骤的执行结果是成功还是失败，给出验证结论，如果是成功的，输出的验证语句中必须包括字符`SUCCESS`，如果失败，必须输出额外的解释或对话，说明该步骤执行失败。

# 原始问题:
{question}

# 当前步骤:
{current_step}

# 当前结果:
{result}

请仅输出针对“当前步骤”的结果的验证回答:如果验证成功，输出内容中必须包含"SUCCESS"
"""

class StepValidator:
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
        messages = [{"role":"user","prompt":"prompt"}]
        response = self.llm_client.think(messages) or ""
        return "SUCCESS" in response.upper()

# --- x. 重新规划器 (RePlanner) 定义 ---
REPLANNER_PROMPT_TEMPLATE = """
你是一个顶级的AI动态规划专家。你的任务是针对规划的完整计划步骤和子步骤执行过程中遇到失败时，结合用户提出的复杂问题和当前已完成子步骤情况，进行系统分析和动态规划，重新规划剩余步骤。
你将收到原始问题、原始完整计划、目前为止已经完成的步骤和结果、当前失败的步骤描述、该步骤的执行结果情况。
请将根据接收信息重新规划剩余步骤和计划，确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列后，能完成整个问题的解答。
你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

# 原始问题:
{question}

# 原始完整计划:
{original_plan}

# 已经完成步骤和结果:
{completed_steps}

# 当前步骤:
{failed_step}

# 当前步骤结果:
{failure_reason}

请严格按照以下格式输出你的计划，```python与```作为前后缀是必要的:
```python
["步骤1", "步骤2", "步骤3", ...]
```
"""

class RePlanner:
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
            messages = [{"role":"user","prompt":"prompt"}]
            print("\n--- 正在重新规划剩余步骤 ---")
            response = self.llm_client.think(messages) or ""
            print(f"✅ 新计划已生成:\n{response_text}")

            return self._parse_plan(response_text)
    
