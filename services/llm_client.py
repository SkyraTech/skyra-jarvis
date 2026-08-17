"""
Unified LLM Client
===================
Adapter pattern implementation to abstract Google Gemini (google-genai SDK) and Groq APIs.
Provides a unified interface, standard response structures, and a dynamic tool schema compiler.
Now supports async generators for streaming, dynamic event loop resolution, and Groq tool calling.
"""

import json
import asyncio
import threading
from typing import List, Any, Optional, Dict, Union

from google import genai
from google.genai import types
from groq import Groq
from loguru import logger


class UnifiedFunctionCall:
    """Unified representation of a model function call request."""
    def __init__(self, name: str, args: Dict[str, Any]):
        self.name = name
        self.args = args


class UnifiedResponse:
    """Unified representation of model completion responses."""
    def __init__(self, text: Optional[str], function_calls: Optional[List[UnifiedFunctionCall]] = None, raw_response: Any = None):
        self.text = text
        self.function_calls = function_calls or []
        self.raw_response = raw_response


class UnifiedLLMClient:
    """Adapts calls to both Gemini and Groq with unified input/output mappings and schema compilation."""
    
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.loop = loop

    async def generate(
        self,
        provider: str,
        key_value: str,
        model_name: str,
        contents: List[Any],
        system_instruction: str,
        tools: Optional[List[Any]] = None
    ) -> UnifiedResponse:
        """
        Main execution endpoint running the client request in a background thread.
        """
        active_loop = self.loop or asyncio.get_running_loop()
        if provider == "google":
            return await active_loop.run_in_executor(
                None,
                self._generate_gemini,
                key_value,
                model_name,
                contents,
                system_instruction,
                tools
            )
        elif provider == "groq":
            return await active_loop.run_in_executor(
                None,
                self._generate_groq,
                key_value,
                model_name,
                contents,
                system_instruction,
                tools
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def generate_stream(
        self,
        provider: str,
        key_value: str,
        model_name: str,
        contents: List[Any],
        system_instruction: str,
        tools: Optional[List[Any]] = None
    ):
        """
        Async generator yielding text chunks from Gemini or Groq streaming endpoints.
        Handles thread safety and event loop scheduling.
        """
        queue = asyncio.Queue()
        active_loop = self.loop or asyncio.get_running_loop()

        def producer():
            try:
                if provider == "google":
                    stream = self._generate_gemini_stream(key_value, model_name, contents, system_instruction, tools)
                elif provider == "groq":
                    stream = self._generate_groq_stream(key_value, model_name, contents, system_instruction, tools)
                else:
                    raise ValueError(f"Unsupported provider: {provider}")
                
                for chunk in stream:
                    active_loop.call_soon_threadsafe(queue.put_nowait, ("chunk", chunk))
                active_loop.call_soon_threadsafe(queue.put_nowait, ("done", None))
            except Exception as e:
                active_loop.call_soon_threadsafe(queue.put_nowait, ("error", e))

        # Spawn producer in a background thread to prevent blocking the event loop
        thread = threading.Thread(target=producer, daemon=True)
        thread.start()

        while True:
            msg_type, val = await queue.get()
            if msg_type == "chunk":
                yield val
            elif msg_type == "done":
                break
            elif msg_type == "error":
                raise val

    def _generate_gemini(
        self,
        key_value: str,
        model_name: str,
        contents: List[Any],
        system_instruction: str,
        tools: Optional[List[Any]] = None
    ) -> UnifiedResponse:
        """Execute Gemini model call."""
        client = genai.Client(api_key=key_value)
        
        # Build generate content config
        config_args = {
            "system_instruction": system_instruction,
            "temperature": 0.7,
            "max_output_tokens": 1024,
        }
        
        if tools:
            config_args["tools"] = tools
            config_args["automatic_function_calling"] = types.AutomaticFunctionCallingConfig(
                disable=True
            )
            
        gen_config = types.GenerateContentConfig(**config_args)
        
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=gen_config
        )
        
        # Translate to unified function calls if requested
        function_calls = []
        if response.function_calls:
            for call in response.function_calls:
                function_calls.append(
                    UnifiedFunctionCall(
                        name=call.name,
                        args=dict(call.args) if call.args else {}
                    )
                )
                
        text = response.text.strip() if response.text else ""
        return UnifiedResponse(text=text, function_calls=function_calls, raw_response=response)

    def _generate_gemini_stream(
        self,
        key_value: str,
        model_name: str,
        contents: List[Any],
        system_instruction: str,
        tools: Optional[List[Any]] = None
    ):
        """Generator running in background thread yielding chunks from Gemini."""
        client = genai.Client(api_key=key_value)
        config_args = {
            "system_instruction": system_instruction,
            "temperature": 0.7,
            "max_output_tokens": 1024,
        }
        if tools:
            config_args["tools"] = tools
            config_args["automatic_function_calling"] = types.AutomaticFunctionCallingConfig(disable=True)
            
        gen_config = types.GenerateContentConfig(**config_args)
        response_stream = client.models.generate_content_stream(
            model=model_name,
            contents=contents,
            config=gen_config
        )
        for chunk in response_stream:
            yield chunk.text or ""

    def _generate_groq(
        self,
        key_value: str,
        model_name: str,
        contents: List[Any],
        system_instruction: str,
        tools: Optional[List[Any]] = None
    ) -> UnifiedResponse:
        """Execute Groq model call (chat completion) with dynamic tool support."""
        client = Groq(api_key=key_value)
        
        # Convert Gemini Content history objects to standard OpenAI/Groq message list
        messages = [{"role": "system", "content": system_instruction}]
        
        for item in contents:
            role = getattr(item, "role", "user")
            # Convert model -> assistant
            if role == "model":
                role = "assistant"
            elif role != "user":
                role = "user"
                
            parts = getattr(item, "parts", [])
            text_content = ""
            for p in parts:
                if hasattr(p, "text") and p.text:
                    text_content += p.text + "\n"
                elif hasattr(p, "function_response") and p.function_response:
                    text_content += f"[System Tool Output for {p.function_response.name}]: {json.dumps(p.function_response.response)}\n"
            
            if text_content.strip():
                if messages and messages[-1]["role"] == role:
                    messages[-1]["content"] += "\n" + text_content.strip()
                else:
                    messages.append({"role": role, "content": text_content.strip()})
                    
        # Dynamically compile tools to OpenAI schemas
        openai_tools = None
        if tools:
            openai_tools = [self._compile_tool_schema(t) for t in tools]

        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                tools=openai_tools
            )
        except Exception as e:
            err_msg = str(e).lower()
            if "tool calling" in err_msg or "tool_calling" in err_msg or "tools" in err_msg:
                logger.warning(f"Groq model {model_name} does not support tool calling. Retrying call without tools...")
                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1024,
                )
            else:
                raise e
        
        # Translate tool calls
        function_calls = []
        message = completion.choices[0].message
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tc in message.tool_calls:
                if tc.type == "function":
                    function_calls.append(
                        UnifiedFunctionCall(
                            name=tc.function.name,
                            args=json.loads(tc.function.arguments) if tc.function.arguments else {}
                        )
                    )

        text = message.content or ""
        return UnifiedResponse(text=text, function_calls=function_calls, raw_response=completion)

    def _generate_groq_stream(
        self,
        key_value: str,
        model_name: str,
        contents: List[Any],
        system_instruction: str,
        tools: Optional[List[Any]] = None
    ):
        """Generator running in background thread yielding chunks from Groq."""
        client = Groq(api_key=key_value)
        messages = [{"role": "system", "content": system_instruction}]
        
        for item in contents:
            role = getattr(item, "role", "user")
            if role == "model":
                role = "assistant"
            elif role != "user":
                role = "user"
                
            parts = getattr(item, "parts", [])
            text_content = ""
            for p in parts:
                if hasattr(p, "text") and p.text:
                    text_content += p.text + "\n"
                elif hasattr(p, "function_response") and p.function_response:
                    text_content += f"[System Tool Output for {p.function_response.name}]: {json.dumps(p.function_response.response)}\n"
            
            if text_content.strip():
                if messages and messages[-1]["role"] == role:
                    messages[-1]["content"] += "\n" + text_content.strip()
                else:
                    messages.append({"role": role, "content": text_content.strip()})

        openai_tools = None
        if tools:
            openai_tools = [self._compile_tool_schema(t) for t in tools]

        try:
            completion_stream = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                stream=True,
                tools=openai_tools
            )
        except Exception as e:
            err_msg = str(e).lower()
            if "tool calling" in err_msg or "tool_calling" in err_msg or "tools" in err_msg:
                logger.warning(f"Groq model {model_name} does not support tool calling in stream. Retrying call without tools...")
                completion_stream = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1024,
                    stream=True,
                )
            else:
                raise e
        for chunk in completion_stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _compile_tool_schema(self, tool) -> Dict[str, Any]:
        """
        Dynamically transforms a Python function or Gemini FunctionDeclaration
        into a standard OpenAI/Groq compatible JSON schema tool definition.
        """
        if hasattr(tool, "name") and hasattr(tool, "description"):
            # It's a Gemini FunctionDeclaration object
            parameters = {}
            if hasattr(tool, "parameters") and tool.parameters:
                parameters = self._convert_gemini_schema_to_json_schema(tool.parameters)
            return {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": parameters
                }
            }
        elif callable(tool):
            # It's a standard Python function. We inspect its signature and docstring.
            import inspect
            name = tool.__name__
            doc = tool.__doc__ or ""
            # Extract description (first block of lines before parameter docs)
            description = doc.strip().split("\n\n")[0].strip() if doc else ""
            
            sig = inspect.signature(tool)
            properties = {}
            required = []
            
            # Simple type mapping
            type_mapping = {
                str: "string",
                int: "integer",
                float: "number",
                bool: "boolean",
                list: "array",
                dict: "object",
                List: "array",
                Dict: "object"
            }
            
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue
                param_type = "string"
                if param.annotation != inspect.Parameter.empty:
                    # Get base annotation
                    anno = param.annotation
                    # Handle typing like Optional[type] or Union[type, None]
                    if hasattr(anno, "__origin__") and anno.__origin__ is Union:
                        args = anno.__args__
                        args = [a for a in args if a is not type(None)]
                        if args:
                            anno = args[0]
                    param_type = type_mapping.get(anno, "string")
                
                # Check for standard parameter descriptions in docstring
                param_desc = ""
                if doc:
                    for line in doc.split("\n"):
                        clean_line = line.strip()
                        if param_name in clean_line and ":" in clean_line:
                            param_desc = clean_line.split(":", 1)[1].strip()
                            break
                
                properties[param_name] = {
                    "type": param_type,
                    "description": param_desc
                }
                
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)
                    
            return {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            }
        else:
            raise TypeError(f"Cannot compile tool schema for type: {type(tool)}")

    def _convert_gemini_schema_to_json_schema(self, gemini_schema) -> Dict[str, Any]:
        """Recursively converts a Gemini Schema object/dictionary into standard JSON schema."""
        properties = {}
        if hasattr(gemini_schema, "properties") and gemini_schema.properties:
            for k, v in gemini_schema.properties.items():
                properties[k] = self._convert_gemini_schema_to_json_schema(v)
        elif isinstance(gemini_schema, dict) and "properties" in gemini_schema:
            for k, v in gemini_schema["properties"].items():
                properties[k] = self._convert_gemini_schema_to_json_schema(v)
                
        type_str = "object"
        if hasattr(gemini_schema, "type"):
            type_str = str(gemini_schema.type).lower().split(".")[-1]
            if type_str == "string":
                type_str = "string"
            elif type_str == "integer":
                type_str = "integer"
            elif type_str == "number":
                type_str = "number"
            elif type_str == "boolean":
                type_str = "boolean"
            elif type_str == "array":
                type_str = "array"
        elif isinstance(gemini_schema, dict) and "type" in gemini_schema:
            type_str = gemini_schema["type"]
            
        required = []
        if hasattr(gemini_schema, "required") and gemini_schema.required:
            required = list(gemini_schema.required)
        elif isinstance(gemini_schema, dict) and "required" in gemini_schema:
            required = gemini_schema["required"]
            
        desc = ""
        if hasattr(gemini_schema, "description"):
            desc = gemini_schema.description
        elif isinstance(gemini_schema, dict) and "description" in gemini_schema:
            desc = gemini_schema["description"]
            
        schema = {"type": type_str}
        if desc:
            schema["description"] = desc
        if properties:
            schema["properties"] = properties
        if required:
            schema["required"] = required
            
        # Array items
        if type_str == "array":
            items = None
            if hasattr(gemini_schema, "items") and gemini_schema.items:
                items = self._convert_gemini_schema_to_json_schema(gemini_schema.items)
            elif isinstance(gemini_schema, dict) and "items" in gemini_schema:
                items = self._convert_gemini_schema_to_json_schema(gemini_schema["items"])
            if items:
                schema["items"] = items
                
        return schema
