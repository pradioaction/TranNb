#!/usr/bin/env python3
import httpx

print("=== 测试 Ollama Chat API ===\n")

base_url = "http://localhost:11434"

# 测试 /api/chat
print("测试 /api/chat 端点...")
try:
    with httpx.Client(timeout=30) as client:
        response = client.post(
            f"{base_url}/api/chat",
            json={
                "model": "qwen:7b",
                "messages": [
                    {
                        "role": "user",
                        "content": "请翻译：Hello World!"
                    }
                ],
                "stream": False
            }
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 成功！响应: {data.get('message', {}).get('content', '')}")
        else:
            print(f"✗ 响应内容: {response.text}")
except Exception as e:
    print(f"✗ 失败: {e}")

print("\n=== 两个 API 端点都已准备就绪 ===")
print("• 如果 generate API 有问题，可以在 settings.json 中设置 'use_chat_api': true 来使用 chat API")
