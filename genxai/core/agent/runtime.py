"""Agent runtime for executing agents with LLM integration."""

from typing import Any, Dict, Optional, List
import asyncio
import time
import logging
import json
import copy

from genxai.core.agent.base import Agent
from genxai.llm.base import LLMProvider
from genxai.llm.factory import LLMProviderFactory
from genxai.core.memory.shared import SharedMemoryBus
from genxai.utils.tokens import manage_context_window

logger = logging.getLogger(__name__)


class AgentExecutionError(Exception):
    """Exception raised during agent execution."""

    pass


class AgentRuntime:
    """Runtime for executing agents."""

    def __init__(
        self,
        agent: Agent,
        llm_provider: Optional[LLMProvider] = None,
        api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        enable_memory: bool = True,
        shared_memory: Optional[SharedMemoryBus] = None,
    ) -> None:
        """Initialize agent runtime.

        Args:
            agent: Agent to execute
            llm_provider: LLM provider instance (optional, will be created if not provided)
            api_key: API key for LLM provider (optional, deprecated - use openai_api_key or anthropic_api_key)
            openai_api_key: OpenAI API key (for GPT models)
            anthropic_api_key: Anthropic API key (for Claude models)
            enable_memory: Whether to initialize memory system
        """
        self.agent = agent
        self._tools: Dict[str, Any] = {}
        self._memory: Optional[Any] = None
        self._shared_memory = shared_memory

        # Initialize LLM provider
        if llm_provider:
            self._llm_provider = llm_provider
        else:
            # Create provider from agent config
            try:
                # Determine which API key to use based on model
                model = agent.config.llm_model.lower()
                selected_api_key = api_key  # Fallback to deprecated api_key parameter
                
                if model.startswith('claude'):
                    # Claude models use Anthropic API key
                    selected_api_key = anthropic_api_key or api_key
                    logger.info(f"Using Anthropic API key for Claude model: {agent.config.llm_model}")
                elif model.startswith('gpt'):
                    # GPT models use OpenAI API key
                    selected_api_key = openai_api_key or api_key
                    logger.info(f"Using OpenAI API key for GPT model: {agent.config.llm_model}")
                else:
                    # For other models, try to infer or use openai_api_key as default
                    selected_api_key = openai_api_key or anthropic_api_key or api_key
                
                self._llm_provider = LLMProviderFactory.create_provider(
                    model=agent.config.llm_model,
                    api_key=selected_api_key,
                    temperature=agent.config.llm_temperature,
                    max_tokens=agent.config.llm_max_tokens,
                )
                logger.info(f"Created LLM provider for agent {agent.id}: {agent.config.llm_model}")
            except Exception as e:
                logger.warning(f"Failed to create LLM provider for agent {agent.id}: {e}")
                self._llm_provider = None
        
        # Initialize memory system if enabled
        if enable_memory and agent.config.enable_memory:
            try:
                from genxai.core.memory.manager import MemorySystem
                self._memory = MemorySystem(agent_id=agent.id)
                logger.info(f"Memory system initialized for agent {agent.id}")
            except Exception as e:
                logger.warning(f"Failed to initialize memory system: {e}")

    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Execute agent with given task.

        Args:
            task: Task description
            context: Execution context
            timeout: Execution timeout in seconds

        Returns:
            Execution result

        Raises:
            AgentExecutionError: If execution fails
            asyncio.TimeoutError: If execution times out
        """
        start_time = time.time()
        
        if context is None:
            context = {}

        # Apply timeout
        execution_timeout = timeout or self.agent.config.max_execution_time
        
        status = "success"
        error_type: Optional[str] = None
        try:
            if execution_timeout:
                result = await asyncio.wait_for(
                    self._execute_internal(task, context),
                    timeout=execution_timeout
                )
            else:
                result = await self._execute_internal(task, context)

            execution_time = time.time() - start_time
            result["execution_time"] = execution_time
            return result

        except asyncio.TimeoutError as exc:
            status = "error"
            error_type = type(exc).__name__
            logger.error(f"Agent {self.agent.id} execution timed out after {execution_timeout}s")
            raise
        except Exception as e:
            status = "error"
            error_type = type(e).__name__
            logger.error(f"Agent {self.agent.id} execution failed: {e}")
            raise AgentExecutionError(f"Agent execution failed: {e}") from e
        finally:
            _ = time.time() - start_time

    async def _execute_internal(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Internal execution logic with full LLM integration.

        Args:
            task: Task description
            context: Execution context

        Returns:
            Execution result
        """
        logger.info(f"Executing agent {self.agent.id}: {task}")
        
        # Get memory context if available
        memory_context = ""
        if self.agent.config.enable_memory and self._memory:
            memory_context = await self.get_memory_context(limit=5)
        
        # Build prompt (without memory context, as it's handled in _get_llm_response)
        prompt_context = dict(context)
        if self._shared_memory is not None:
            prompt_context["shared_memory"] = {
                key: self._shared_memory.get(key)
                for key in self._shared_memory.list_keys()
            }
        prompt = self._build_prompt(task, prompt_context, "")
        
        # Get LLM response with retry logic and memory context
        if self.agent.config.tools and self._tools and self._provider_supports_tools():
            response = await self._get_llm_response_with_tools(prompt, memory_context, context)
        else:
            response = await self._get_llm_response_with_retry(prompt, memory_context)
            # Process tools if needed (legacy parsing)
            if self.agent.config.tools and self._tools:
                response = await self._process_tools(response, context)
        
        # Update memory if enabled
        if self.agent.config.enable_memory and self._memory:
            await self._update_memory(task, response)
        
        # Build result
        safe_context: Dict[str, Any]
        try:
            safe_context = copy.deepcopy(context)
        except Exception:
            safe_context = dict(context)
        safe_context.pop("llm_provider", None)
        safe_context.pop("shared_memory", None)
        result = {
            "agent_id": self.agent.id,
            "task": task,
            "status": "completed",
            "output": response,
            "tokens_used": self.agent._total_tokens,
            "context": safe_context,
        }
        
        # Store episode in episodic memory
        if self._memory and hasattr(self._memory, 'episodic') and self._memory.episodic:
            try:
                execution_time = time.time() - time.time()  # Will be set by caller
                await self._memory.store_episode(
                    task=task,
                    actions=[{"type": "llm_call", "response": response}],
                    outcome=result,
                    duration=execution_time,
                    success=True,
                    metadata={"agent_id": self.agent.id},
                )
            except Exception as e:
                logger.warning(f"Failed to store episode: {e}")
        
        # Reflection for learning agents
        if self.agent.config.agent_type == "learning":
            reflection = await self.agent.reflect(result)
            result["reflection"] = reflection
        
        return result

    def _build_prompt(
        self, 
        task: str, 
        context: Dict[str, Any],
        memory_context: str = ""
    ) -> str:
        """Build comprehensive prompt for LLM with memory context.

        Args:
            task: Task description
            context: Execution context
            memory_context: Recent memory context

        Returns:
            Formatted prompt
        """
        prompt_parts = []
        
        # Add memory context if available
        if memory_context:
            prompt_parts.append(memory_context)
            prompt_parts.append("")  # Empty line for separation
        
        # Add available tools with descriptions
        if self.agent.config.tools and self._tools:
            prompt_parts.append("Available tools:")
            for tool_name in self.agent.config.tools:
                if tool_name in self._tools:
                    tool = self._tools[tool_name]
                    tool_desc = getattr(tool, 'metadata', None)
                    if tool_desc:
                        prompt_parts.append(f"- {tool_name}: {tool_desc.description}")
                    else:
                        prompt_parts.append(f"- {tool_name}")
            prompt_parts.append("")
        
        # Add context if provided
        if context:
            prompt_parts.append(f"Context: {context}")
            prompt_parts.append("")
        
        # Add task
        prompt_parts.append(f"Task: {task}")
        
        # Add agent type specific instructions
        if self.agent.config.agent_type == "deliberative":
            prompt_parts.append("\nThink step by step and plan your approach before responding.")
        elif self.agent.config.agent_type == "learning":
            prompt_parts.append("\nConsider past experiences and improve your approach.")
        
        return "\n".join(prompt_parts)

    def _build_system_prompt(self) -> str:
        """Build system prompt from agent configuration.

        Returns:
            System prompt string
        """
        system_parts = []
        
        # Add role
        system_parts.append(f"You are a {self.agent.config.role}.")
        
        # Add goal
        system_parts.append(f"Your goal is: {self.agent.config.goal}")
        
        # Add backstory if provided
        if self.agent.config.backstory:
            system_parts.append(f"\nBackground: {self.agent.config.backstory}")
        
        # Add agent type specific instructions
        if self.agent.config.agent_type == "deliberative":
            system_parts.append("\nYou should think carefully and plan before acting.")
        elif self.agent.config.agent_type == "learning":
            system_parts.append("\nYou should learn from feedback and improve over time.")
        elif self.agent.config.agent_type == "collaborative":
            system_parts.append("\nYou should work well with other agents and coordinate effectively.")
        
        return "\n".join(system_parts)

    async def _get_llm_response(self, prompt: str, memory_context: str = "") -> str:
        """Get response from LLM with context window management.

        Args:
            prompt: Prompt to send to LLM
            memory_context: Memory context to include

        Returns:
            LLM response

        Raises:
            RuntimeError: If LLM provider not initialized
        """
        if not self._llm_provider:
            logger.error(f"No LLM provider available for agent {self.agent.id}")
            raise RuntimeError(
                f"Agent {self.agent.id} has no LLM provider. "
                "Provide an API key or set OPENAI_API_KEY environment variable."
            )

        start_time = time.time()
        try:
            logger.debug(f"Calling LLM for agent {self.agent.id}")

            # Build system prompt from agent config
            system_prompt = self._build_system_prompt()

            # Manage context window to fit within model limits
            system_prompt, prompt, memory_context = manage_context_window(
                system_prompt=system_prompt,
                user_prompt=prompt,
                memory_context=memory_context,
                model=self.agent.config.llm_model,
                reserve_tokens=self.agent.config.llm_max_tokens or 1000,
            )

            # Prepend memory context to prompt if available
            if memory_context:
                prompt = f"{memory_context}\n\n{prompt}"

            # Call LLM provider
            response = await self._llm_provider.generate(
                prompt=prompt,
                system_prompt=system_prompt,
            )

            # Update token usage and execution count
            self.agent._total_tokens += response.usage.get("total_tokens", 0)
            self.agent._execution_count += 1

            logger.debug(
                f"LLM response received for agent {self.agent.id}: "
                f"{len(response.content)} chars, "
                f"{response.usage.get('total_tokens', 0)} tokens"
            )

            duration = time.time() - start_time
            provider_name = self._llm_provider.__class__.__name__
            return response.content

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"LLM call failed for agent {self.agent.id}: {e}")
            raise RuntimeError(f"LLM call failed: {e}") from e

    async def _get_llm_response_with_retry(
        self,
        prompt: str,
        memory_context: str = "",
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> str:
        """Get response from LLM with exponential backoff retry logic.

        Args:
            prompt: Prompt to send to LLM
            memory_context: Memory context to include
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff

        Returns:
            LLM response

        Raises:
            RuntimeError: If all retries fail
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return await self._get_llm_response(prompt, memory_context)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s, etc.
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"LLM call failed for agent {self.agent.id} "
                        f"(attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {delay}s... Error: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"LLM call failed for agent {self.agent.id} "
                        f"after {max_retries} attempts"
                    )
        
        raise RuntimeError(
            f"LLM call failed after {max_retries} attempts. Last error: {last_error}"
        ) from last_error

    def _provider_supports_tools(self) -> bool:
        """Check if the configured provider supports schema-based tool calling."""
        if not self._llm_provider:
            return False
        return self._llm_provider.__class__.__name__ == "OpenAIProvider"

    def _build_tool_schemas(self) -> List[Dict[str, Any]]:
        """Build OpenAI-compatible tool schemas from registered tools."""
        schemas: List[Dict[str, Any]] = []
        for tool in self._tools.values():
            if hasattr(tool, "get_schema"):
                schema = tool.get_schema()
                parameters = schema.get("parameters") or {
                    "type": "object",
                    "properties": {},
                    "required": [],
                }
                schemas.append(
                    {
                        "type": "function",
                        "function": {
                            "name": schema.get("name", tool.metadata.name),
                            "description": schema.get("description", ""),
                            "parameters": parameters,
                        },
                    }
                )
            else:
                schemas.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.metadata.name,
                            "description": tool.metadata.description,
                            "parameters": {"type": "object", "properties": {}},
                        },
                    }
                )
        return schemas

    async def _get_llm_response_with_tools(
        self,
        prompt: str,
        memory_context: str,
        context: Dict[str, Any],
    ) -> str:
        """Get response from LLM using schema-based tool calling."""
        if not self._llm_provider:
            raise RuntimeError(
                f"Agent {self.agent.id} has no LLM provider. "
                "Provide an API key or set OPENAI_API_KEY environment variable."
            )

        system_prompt = self._build_system_prompt()
        system_prompt, prompt, memory_context = manage_context_window(
            system_prompt=system_prompt,
            user_prompt=prompt,
            memory_context=memory_context,
            model=self.agent.config.llm_model,
            reserve_tokens=self.agent.config.llm_max_tokens or 1000,
        )

        if memory_context:
            prompt = f"{memory_context}\n\n{prompt}"

        tool_schemas = self._build_tool_schemas()
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        response = await self._llm_provider.generate_chat(
            messages=messages,
            tools=tool_schemas,
            tool_choice="auto",
        )

        tool_calls = self._extract_tool_calls(response.metadata.get("tool_calls"))
        if not tool_calls:
            return response.content

        tool_messages: List[Dict[str, Any]] = []
        for call in tool_calls:
            result = await self._execute_tool(
                {"name": call["name"], "arguments": call["arguments"]},
                context,
            )
            serialized = self._serialize_tool_result(result)
            tool_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": json.dumps(serialized, default=str),
                }
            )

        assistant_message = {
            "role": "assistant",
            "content": response.content or "",
            "tool_calls": [call["raw"] for call in tool_calls],
        }
        messages.append(assistant_message)
        messages.extend(tool_messages)

        final_response = await self._llm_provider.generate_chat(
            messages=messages,
            tools=tool_schemas,
            tool_choice="none",
        )
        return final_response.content

    def _extract_tool_calls(self, raw_calls: Any) -> List[Dict[str, Any]]:
        """Normalize tool calls returned by the LLM provider."""
        if not raw_calls:
            return []

        tool_calls: List[Dict[str, Any]] = []
        for call in raw_calls:
            normalized = call
            if hasattr(call, "model_dump"):
                normalized = call.model_dump()
            elif hasattr(call, "dict"):
                normalized = call.dict()
            elif hasattr(call, "__dict__"):
                normalized = call.__dict__

            function_payload = normalized.get("function") if isinstance(normalized, dict) else None
            if not function_payload:
                continue

            name = function_payload.get("name")
            arguments_raw = function_payload.get("arguments", "{}")
            try:
                arguments = json.loads(arguments_raw) if isinstance(arguments_raw, str) else arguments_raw
            except json.JSONDecodeError:
                arguments = {}

            tool_calls.append(
                {
                    "id": normalized.get("id") or f"tool_call_{name}",
                    "name": name,
                    "arguments": arguments or {},
                    "raw": normalized,
                }
            )

        return tool_calls

    def _serialize_tool_result(self, result: Any) -> Any:
        """Convert tool result into JSON-serializable data."""
        if hasattr(result, "model_dump"):
            return result.model_dump()
        if hasattr(result, "dict"):
            return result.dict()
        return result

    async def stream_execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Execute agent with streaming response.

        Args:
            task: Task description
            context: Execution context

        Yields:
            Response chunks as they arrive

        Raises:
            RuntimeError: If LLM provider not initialized or doesn't support streaming
        """
        if not self._llm_provider:
            raise RuntimeError(
                f"Agent {self.agent.id} has no LLM provider. "
                "Provide an API key or set OPENAI_API_KEY environment variable."
            )

        logger.info(f"Streaming execution for agent {self.agent.id}: {task}")

        # Get memory context if available
        memory_context = ""
        if self.agent.config.enable_memory and self._memory:
            memory_context = await self.get_memory_context(limit=5)

        # Build prompt
        prompt = self._build_prompt(task, context or {}, memory_context)
        system_prompt = self._build_system_prompt()

        try:
            # Stream from LLM provider
            full_response = []
            async for chunk in self._llm_provider.generate_stream(
                prompt=prompt,
                system_prompt=system_prompt,
            ):
                full_response.append(chunk)
                yield chunk

            # Update memory after streaming completes
            complete_response = "".join(full_response)
            if self.agent.config.enable_memory and self._memory:
                await self._update_memory(task, complete_response)

        except Exception as e:
            logger.error(f"Streaming execution failed for agent {self.agent.id}: {e}")
            raise RuntimeError(f"Streaming execution failed: {e}") from e

    async def _process_tools(
        self,
        response: str,
        context: Dict[str, Any],
        max_iterations: int = 5,
    ) -> str:
        """Process tool calls in response with chaining support.

        Args:
            response: LLM response
            context: Execution context
            max_iterations: Maximum tool chaining iterations

        Returns:
            Processed response with tool results
        """
        logger.debug(f"Processing tools for agent {self.agent.id}")
        
        current_response = response
        all_tool_results = []
        iteration = 0
        
        # Tool chaining loop
        while iteration < max_iterations:
            # Parse tool calls from current response
            tool_calls = self._parse_tool_calls(current_response)
            
            if not tool_calls:
                # No more tool calls, we're done
                break
            
            logger.info(f"Tool iteration {iteration + 1}: Found {len(tool_calls)} tool calls")
            
            # Execute tools in this iteration
            iteration_results = []
            for tool_call in tool_calls:
                try:
                    result = await self._execute_tool(tool_call, context)
                    iteration_results.append({
                        "tool": tool_call["name"],
                        "success": True,
                        "result": result,
                        "iteration": iteration + 1,
                    })
                    # Update context with tool result for chaining
                    context[f"tool_result_{tool_call['name']}"] = result
                except Exception as e:
                    logger.error(f"Tool {tool_call['name']} failed: {e}")
                    iteration_results.append({
                        "tool": tool_call["name"],
                        "success": False,
                        "error": str(e),
                        "iteration": iteration + 1,
                    })
            
            all_tool_results.extend(iteration_results)
            
            # Get next response from LLM with tool results
            current_response = await self._format_tool_results(current_response, iteration_results)
            iteration += 1
        
        if iteration >= max_iterations:
            logger.warning(f"Reached max tool chaining iterations ({max_iterations})")
        
        return current_response
    
    def _parse_tool_calls(self, response: str) -> list[Dict[str, Any]]:
        """Parse tool calls from LLM response.
        
        Supports two formats:
        1. Function calling: {"name": "tool_name", "arguments": {...}}
        2. Text format: USE_TOOL: tool_name(arg1="value1", arg2="value2")
        
        Args:
            response: LLM response text
            
        Returns:
            List of tool call dictionaries
        """
        import json
        import re
        
        tool_calls = []
        
        # Try to parse JSON function calls - look for complete JSON objects
        try:
            # Pattern to match JSON objects with name and arguments fields
            # This handles nested objects in arguments
            json_pattern = r'\{[^{}]*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:\s*\{[^}]*\}\s*\}'
            matches = re.findall(json_pattern, response, re.DOTALL)
            
            for match in matches:
                try:
                    call = json.loads(match)
                    if "name" in call and "arguments" in call:
                        tool_calls.append({
                            "name": call["name"],
                            "arguments": call["arguments"],
                        })
                except json.JSONDecodeError:
                    # Try to fix common JSON issues
                    try:
                        # Replace single quotes with double quotes
                        fixed_match = match.replace("'", '"')
                        call = json.loads(fixed_match)
                        if "name" in call and "arguments" in call:
                            tool_calls.append({
                                "name": call["name"],
                                "arguments": call["arguments"],
                            })
                    except:
                        continue
        except Exception as e:
            logger.debug(f"Failed to parse JSON tool calls: {e}")
        
        # Try to parse text-based tool calls
        text_pattern = r'USE_TOOL:\s*(\w+)\((.*?)\)'
        matches = re.findall(text_pattern, response, re.DOTALL)
        
        for tool_name, args_str in matches:
            try:
                # Parse arguments
                arguments = {}
                if args_str.strip():
                    # Parse key="value" pairs
                    arg_pattern = r'(\w+)=(["\'])(.*?)\2'
                    arg_matches = re.findall(arg_pattern, args_str)
                    for key, _, value in arg_matches:
                        arguments[key] = value
                
                tool_calls.append({
                    "name": tool_name,
                    "arguments": arguments,
                })
            except Exception as e:
                logger.error(f"Failed to parse tool call {tool_name}: {e}")
        
        return tool_calls
    
    async def _execute_tool(
        self,
        tool_call: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Any:
        """Execute a single tool.
        
        Args:
            tool_call: Tool call dictionary with name and arguments
            context: Execution context
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool not found
            Exception: If tool execution fails
        """
        tool_name = tool_call["name"]
        arguments = tool_call.get("arguments", {})
        
        # Check if tool exists
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' not found in available tools")
        
        tool = self._tools[tool_name]
        
        logger.info(f"Executing tool {tool_name} with arguments: {arguments}")
        
        # Execute tool
        try:
            # Check if tool has async execute method
            if hasattr(tool, 'execute') and asyncio.iscoroutinefunction(tool.execute):
                result = await tool.execute(**arguments)
            elif hasattr(tool, 'execute'):
                result = tool.execute(**arguments)
            elif callable(tool):
                # Tool is a function
                if asyncio.iscoroutinefunction(tool):
                    result = await tool(**arguments)
                else:
                    result = tool(**arguments)
            else:
                raise ValueError(f"Tool {tool_name} is not callable")
            
            logger.info(f"Tool {tool_name} executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Tool {tool_name} execution failed: {e}")
            raise
    
    async def _format_tool_results(
        self,
        original_response: str,
        tool_results: list[Dict[str, Any]],
    ) -> str:
        """Format tool results and get final response from LLM.
        
        Args:
            original_response: Original LLM response with tool calls
            tool_results: List of tool execution results
            
        Returns:
            Final formatted response
        """
        # Build tool results summary
        results_text = "\n\nTool Execution Results:\n"
        for result in tool_results:
            if result["success"]:
                results_text += f"- {result['tool']}: {result['result']}\n"
            else:
                results_text += f"- {result['tool']}: ERROR - {result['error']}\n"
        
        # Ask LLM to incorporate tool results into final response
        follow_up_prompt = (
            f"Based on the tool execution results below, provide a final response.\n"
            f"{results_text}\n"
            f"Provide a clear, concise response incorporating these results."
        )
        
        try:
            final_response = await self._get_llm_response(follow_up_prompt)
            return final_response
        except Exception as e:
            logger.error(f"Failed to get final response after tool execution: {e}")
            # Return original response with tool results appended
            return original_response + results_text

    async def _update_memory(self, task: str, response: str) -> None:
        """Update agent memory.

        Args:
            task: Task that was executed
            response: Response generated
        """
        if not self._memory:
            return
        
        try:
            # Store in short-term memory
            await self._memory.add_to_short_term(
                content={"task": task, "response": response},
                metadata={"agent_id": self.agent.id, "timestamp": time.time()},
            )
            
            logger.debug(f"Stored interaction in short-term memory for agent {self.agent.id}")
            
            # Consolidate important memories to long-term
            if hasattr(self._memory, 'consolidate_memories'):
                await self._memory.consolidate_memories(importance_threshold=0.7)
        except Exception as e:
            logger.error(f"Failed to update memory: {e}")

    def set_llm_provider(self, provider: Any) -> None:
        """Set LLM provider.

        Args:
            provider: LLM provider instance
        """
        self._llm_provider = provider
        logger.info(f"LLM provider set for agent {self.agent.id}")

    def set_tools(self, tools: Dict[str, Any]) -> None:
        """Set available tools.

        Args:
            tools: Dictionary of tool name to tool instance
        """
        self._tools = tools
        logger.info(f"Tools set for agent {self.agent.id}: {list(tools.keys())}")

    def set_memory(self, memory: Any) -> None:
        """Set memory system.

        Args:
            memory: Memory system instance (MemoryManager or MemorySystem)
        """
        self._memory = memory
        logger.info(f"Memory system set for agent {self.agent.id}")
    
    async def get_memory_context(self, limit: int = 5) -> str:
        """Get recent memory context for LLM prompts.

        Args:
            limit: Number of recent memories to include

        Returns:
            Formatted memory context string
        """
        if not self._memory:
            return ""
        
        try:
            # Get context from short-term memory
            context = await self._memory.get_short_term_context(max_tokens=2000)
            return context
        except Exception as e:
            logger.error(f"Failed to get memory context: {e}")
            return ""

    async def batch_execute(
        self,
        tasks: list[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> list[Dict[str, Any]]:
        """Execute multiple tasks in parallel.

        Args:
            tasks: List of tasks to execute
            context: Shared execution context

        Returns:
            List of execution results
        """
        logger.info(f"Batch executing {len(tasks)} tasks for agent {self.agent.id}")
        
        results = await asyncio.gather(
            *[self.execute(task, context) for task in tasks],
            return_exceptions=True
        )
        
        return [
            r if not isinstance(r, Exception) else {"error": str(r)}
            for r in results
        ]
