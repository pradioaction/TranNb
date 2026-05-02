#!/usr/bin/env python3
import httpx

print("=== Ollama 诊断工具 ===\n")

# 1. 检查 Ollama 服务是否运行
try:
    print("1. 检查 Ollama 服务...")
    with httpx.Client(timeout=10) as client:
        response = client.get("http://localhost:11434/api/tags")
        print(f"   ✓ Ollama 服务运行正常 (状态码: {response.status_code})")
        data = response.json()
        models = data.get("models", [])
        print(f"\n2. 已下载的模型:")
        if models:
            for model in models:
                print(f"   - {model['name']}")
        else:
            print("   ⚠ 没有找到任何模型！")
            print("\n   提示：您需要下载一个模型才能使用翻译功能。")
            print("   例如，运行: ollama pull qwen2.5:0.5b")
except Exception as e:
    print(f"   ✗ Ollama 服务连接失败: {e}")
    print("\n   请确保 Ollama 正在运行！")
    print("   可以运行: ollama serve")

# 2. 检查配置
print("\n3. 当前程序配置:")
import json
import os
settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
if os.path.exists(settings_path):
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = json.load(f)
        ollama_config = settings.get('translation', {}).get('ollama', {})
        print(f"   - base_url: {ollama_config.get('base_url')}")
        print(f"   - model: {ollama_config.get('model')}")
