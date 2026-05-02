#!/usr/bin/env python3
import httpx

print("=== 测试 Ollama API 端点 ===\n")

base_url = "http://localhost:11434"

# 1. 测试 /api/tags
print("1. 测试 /api/tags...")
try:
    with httpx.Client(timeout=10) as client:
        response = client.get(f"{base_url}/api/tags")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ 成功！找到 {len(data.get('models', []))} 个模型")
except Exception as e:
    print(f"   ✗ 失败: {e}")

# 2. 测试 /api/generate
print("\n2. 测试 /api/generate...")
try:
    with httpx.Client(timeout=30) as client:
        response = client.post(
            f"{base_url}/api/generate",
            json={
                "model": "qwen:7b",
                "prompt": "你好，请说一句话",
                "stream": False
            }
        )
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ 成功！响应: {data.get('response', '')}")
        else:
            print(f"   ✗ 响应内容: {response.text}")
except Exception as e:
    print(f"   ✗ 失败: {e}")

# 3. 列出所有可用模型以供选择
print("\n3. 已下载的模型列表:")
try:
    with httpx.Client(timeout=10) as client:
        response = client.get(f"{base_url}/api/tags")
        data = response.json()
        for model in data.get("models", []):
            print(f"   - {model['name']}")
except Exception:
    pass
