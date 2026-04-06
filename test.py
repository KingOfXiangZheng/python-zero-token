"""Test script for Zero Token API"""
import openai

client = openai.OpenAI(
    api_key="dummy",
    base_url="http://localhost:8000/v1"
)

def test_deepseek():
    print("=" * 60)
    print("Testing DeepSeek")
    print("=" * 60)
    
    response = client.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=[{"role": "user", "content": "你好！请介绍一下你自己。"}],
        stream=True
    )
    
    print("Response: ", end="", flush=True)
    for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print("\n✓ Done\n")

def test_glm():
    print("=" * 60)
    print("Testing GLM")
    print("=" * 60)
    
    response = client.chat.completions.create(
        model="glm/glm-4-plus",
        messages=[{"role": "user", "content": "你好！"}],
        stream=True
    )
    
    print("Response: ", end="", flush=True)
    for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print("\n✓ Done\n")

def test_kimi():
    print("=" * 60)
    print("Testing Kimi")
    print("=" * 60)
    
    response = client.chat.completions.create(
        model="kimi/kimi",
        messages=[{"role": "user", "content": "你好！"}],
        stream=True
    )
    
    print("Response: ", end="", flush=True)
    for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print("\n✓ Done\n")

def test_doubao():
    print("=" * 60)
    print("Testing Doubao (豆包)")
    print("=" * 60)
    
    response = client.chat.completions.create(
        model="doubao/doubao-pro-4k",
        messages=[{"role": "user", "content": "你好！"}],
        stream=True
    )
    
    print("Response: ", end="", flush=True)
    for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print("\n✓ Done\n")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Python Zero Token Test")
    print("=" * 60 + "\n")
    
    try:
        test_deepseek()
    except Exception as e:
        print(f"✗ DeepSeek failed: {e}\n")
    
    try:
        test_glm()
    except Exception as e:
        print(f"✗ GLM failed: {e}\n")
    
    try:
        test_kimi()
    except Exception as e:
        print(f"✗ Kimi failed: {e}\n")
    
    try:
        test_doubao()
    except Exception as e:
        print(f"✗ Doubao failed: {e}\n")
    
    print("=" * 60)
    print("Test Complete")
    print("=" * 60)
