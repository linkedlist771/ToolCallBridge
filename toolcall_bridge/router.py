import os
import json
from typing import AsyncIterator
from copy import deepcopy
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion import ChatCompletion
from toolcall_bridge.tool_parser import OpenAICompatibleToolParser
from toolcall_bridge.tool_prompt_templates import format_system_and_tools
from toolcall_bridge.protocol import ChatMessage
from toolcall_bridge.configs import OPENAI_COMPATIBLE_BASEURL
from loguru import logger
router = APIRouter(
    prefix="/v1"
)

tool_parser = OpenAICompatibleToolParser()

async def _generate_stream(client: AsyncOpenAI, payload: dict, tools: list):
    """内层异步生成器函数，处理流式返回"""
    if tools:
        previous_text: str = ""
        generator: AsyncIterator[ChatCompletionChunk] = await client.chat.completions.create(**payload)
        async for chunk in generator:
            send_chunk = deepcopy(chunk)
            if chunk.choices:
                delta_text: str = chunk.choices[0].delta.content or ""
                current_text: str = previous_text + delta_text
                delta_message = (
                    tool_parser.extract_tool_calls_streaming(
                        previous_text=previous_text,
                        current_text=current_text,
                        delta_text=delta_text))
                
                previous_text = current_text
                send_chunk.choices[0].delta = delta_message
                
            # 按 OpenAI SSE 格式输出
            yield f"data: {json.dumps(send_chunk.model_dump())}\n\n"
        
        # 流式结束标志
        yield "data: [DONE]\n\n"
    else:
        # 走原生的流式
        logger.info(f"Streaming payload: {payload}")
        async for chunk in (await client.chat.completions.create(**payload)):
            yield f"data: {json.dumps(chunk.model_dump())}\n\n"
        yield "data: [DONE]\n\n"


@router.post("/chat/completions")
async def create_chat_completion(raw_request: Request):
    # we don't need a pydantic check here, for we need a 100 % flexibility
    # we don't do verification here, for we don't need to
    payload = await raw_request.json()
    headers = raw_request.headers
    params = raw_request.query_params
    api_key = headers.get("Authorization").removeprefix("Bearer ").strip()
    base_url = OPENAI_COMPATIBLE_BASEURL
    stream = payload.get("stream", False)
    # 不用支持这么复杂的内容， 直接看tools这个字段就行了, 让他自己决定。

    tools = payload.get("tools", [])
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    if tools:
        system_message = payload.get("messages")[0]
        if system_message.get("role") == "system":
            system_prompt = system_message.get("content")
            system_prompt = format_system_and_tools(system_prompt, tools)
            payload["messages"][0]["content"] = system_prompt
        else:
            
            system_prompt = None
            system_prompt = format_system_and_tools(system_prompt, tools)
            role = "system"
            model = payload.get("model", "")
            if "claude" in model:
                role = "user"
            payload["messages"] = [{"role": role, "content": system_prompt}] + payload["messages"]
        # logger.info(f"Payload: {payload}")
    if stream:
        # 流式返回：返回 StreamingResponse
        return StreamingResponse(
            _generate_stream(client, payload, tools),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
    else:
        # 非流式返回：直接 return 结果
        if tools:
            response: ChatCompletion = await client.chat.completions.create(**payload)
            content = response.choices[0].message.content
            tool_call_info = tool_parser.extract_tool_calls(content)
            if tool_call_info.tools_called:
                message = ChatMessage(role="assistant",
                                      content=tool_call_info.content,
                                      tool_calls=tool_call_info.tool_calls)
            else:
                # FOR NOW make it a chat message; we will have to detect
                # the type to make it later.
                message = ChatMessage(role="assistant",
                                      content=content)
            response.choices[0].message = message
            return response
        else:
            return await client.chat.completions.create(**payload)
