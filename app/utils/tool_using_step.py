import logging
from .base_step import PlaybookStep
from app.ai_models import get_llm
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
from .playbook_utils import render_template
import dpath



class ToolUsingLLMStep(PlaybookStep):
    """
    A playbook step that uses an LLM agent with a set of tools to accomplish a task.
    """
    def execute(self, step_config: dict, context: dict, db, doc_id: str, playbook_executor):
        prompt_template = step_config.get('prompt')
        output_key = step_config.get('output_key')
        tool_names = step_config.get('tools', [])

        if not all([prompt_template, output_key, tool_names]):
            raise ValueError("ToolUsingLLMStep requires 'prompt', 'output_key', and 'tools' in its configuration.")

        # Dynamically load the tools from the tool registry
        tools = [TOOL_REGISTRY[name] for name in tool_names if name in TOOL_REGISTRY]
        if not tools:
            raise ValueError(f"None of the specified tools ({tool_names}) were found in the tool registry.")

        formatted_prompt = render_template(prompt_template, context)

        llm = get_llm()
        prompt = ChatPromptTemplate.from_messages([("user", formatted_prompt), ("placeholder", "{agent_scratchpad}")])
        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

        logger.info(f"Executing Tool-Using LLM step '{step_config.get('name')}'.")
        result = agent_executor.invoke({})

        dpath.new(context, f"outputs.{output_key}", result.get('output'))
        logger.info(f"Tool-Using LLM step completed. Stored result in context at 'outputs.{output_key}'.")
