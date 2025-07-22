#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIGIMON GraphRAG 运行示例
这个脚本展示了如何使用DIGIMON框架进行GraphRAG查询
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from Core.GraphRAG import GraphRAG
from Option.Config2 import Config


def create_sample_config():
    """创建示例配置"""
    config_dict = {
        # 基础LLM配置
        'llm': {
            'api_type': 'openai',  # 或 'open_llm' 用于本地模型
            'base_url': 'https://api.openai.com/v1',
            'model': 'gpt-3.5-turbo',
            'api_key': 'your-api-key-here'  # 请替换为你的API Key
        },
        
        # 嵌入模型配置
        'embedding': {
            'api_type': 'openai',
            'model': 'text-embedding-ada-002',
            'api_key': 'your-api-key-here',  # 请替换为你的API Key
            'dimensions': 1536,
            'max_token_size': 8192
        },
        
        # 数据和工作目录
        'data_root': './Data',
        'working_dir': './',
        'exp_name': 'demo_experiment',
        
        # 图配置
        'graph': {
            'graph_type': 'tree_graph',
            'force': False,
            'num_layers': 3,
            'top_k': 5,
            'threshold': 0.15
        },
        
        # 检索配置
        'retriever': {
            'top_k': 8,
            'query_type': 'basic'
        },
        
        # 查询配置
        'query': {
            'query_type': 'qa',
            'retrieve_top_k': 15,
            'tree_search': True,
            'response_type': 'Multiple Paragraphs'
        },
        
        # 分块配置
        'chunk': {
            'chunk_token_size': 800,
            'chunk_overlap_token_size': 100,
            'chunk_method': 'chunking_by_token_size'
        }
    }
    
    return config_dict


async def demo_query_single():
    """演示单个查询"""
    print("🚀 开始单个查询演示...")
    
    # 创建配置
    config_dict = create_sample_config()
    config = Config(config_dict)
    
    # 初始化GraphRAG系统
    digimon = GraphRAG(config)
    
    # 示例查询
    query = "什么是GraphRAG？它有什么优势？"
    
    print(f"📝 查询问题: {query}")
    print("🔄 正在处理查询...")
    
    try:
        # 执行查询
        result = await digimon.query(query)
        
        print("\n✅ 查询结果:")
        print("-" * 50)
        print(result)
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")
        print("💡 请检查API配置和网络连接")


async def demo_query_batch():
    """演示批量查询"""
    print("\n🚀 开始批量查询演示...")
    
    # 创建配置
    config_dict = create_sample_config()
    config = Config(config_dict)
    
    # 初始化GraphRAG系统
    digimon = GraphRAG(config)
    
    # 示例查询列表
    queries = [
        "GraphRAG的核心组件有哪些？",
        "如何选择合适的图类型？",
        "RAPTOR和LightRAG有什么区别？"
    ]
    
    results = []
    
    for i, query in enumerate(queries, 1):
        print(f"\n📝 查询 {i}: {query}")
        print("🔄 正在处理...")
        
        try:
            result = await digimon.query(query)
            results.append({
                'query': query,
                'result': result,
                'status': 'success'
            })
            print(f"✅ 查询 {i} 完成")
            
        except Exception as e:
            results.append({
                'query': query,
                'result': str(e),
                'status': 'failed'
            })
            print(f"❌ 查询 {i} 失败: {str(e)}")
    
    # 显示结果摘要
    print("\n📊 批量查询结果摘要:")
    print("=" * 60)
    
    for i, result in enumerate(results, 1):
        status_icon = "✅" if result['status'] == 'success' else "❌"
        print(f"{status_icon} 查询 {i}: {result['query'][:30]}...")
        if result['status'] == 'success':
            print(f"   结果长度: {len(result['result'])} 字符")
        else:
            print(f"   错误: {result['result']}")
        print()


def check_configuration():
    """检查配置是否正确"""
    print("🔍 检查配置...")
    
    config_dict = create_sample_config()
    
    # 检查API Key
    if 'your-api-key-here' in str(config_dict):
        print("⚠️  警告: 请在配置中设置正确的API Key")
        print("   请编辑 create_sample_config() 函数中的 api_key 字段")
        return False
    
    # 检查数据目录
    data_dir = Path(config_dict['data_root'])
    if not data_dir.exists():
        print(f"⚠️  警告: 数据目录不存在: {data_dir}")
        print("   请确保数据目录存在并包含相关文档")
        return False
    
    print("✅ 配置检查通过")
    return True


def show_usage():
    """显示使用说明"""
    print("📖 DIGIMON GraphRAG 使用说明")
    print("=" * 50)
    print()
    print("🔧 配置步骤:")
    print("1. 设置API Key (OpenAI或其他LLM服务)")
    print("2. 准备数据集 (放在Data目录下)")
    print("3. 选择合适的方法配置文件")
    print()
    print("🚀 运行方式:")
    print("1. 直接运行此脚本: python 运行示例.py")
    print("2. 使用命令行: python main.py -opt Option/Method/RAPTOR.yaml -dataset_name your_data")
    print()
    print("📁 支持的图类型:")
    print("- tree_graph: 树形图 (RAPTOR)")
    print("- er_graph: 实体关系图")
    print("- rkg_graph: 丰富知识图 (LightRAG)")
    print("- passage_graph: 段落图")
    print()
    print("🎯 查询类型:")
    print("- qa: 问答")
    print("- summarization: 摘要生成")
    print()


async def main():
    """主函数"""
    print("🎉 欢迎使用 DIGIMON GraphRAG 框架!")
    print("=" * 60)
    
    # 显示使用说明
    show_usage()
    
    # 检查配置
    if not check_configuration():
        print("\n❌ 配置检查失败，请修正配置后重试")
        return
    
    # 询问用户选择
    print("\n请选择运行模式:")
    print("1. 单个查询演示")
    print("2. 批量查询演示")
    print("3. 仅显示配置信息")
    
    try:
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == '1':
            await demo_query_single()
        elif choice == '2':
            await demo_query_batch()
        elif choice == '3':
            config_dict = create_sample_config()
            print("\n📋 当前配置:")
            for key, value in config_dict.items():
                print(f"  {key}: {value}")
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 运行出错: {str(e)}")
    
    print("\n🎉 演示结束，感谢使用!")


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())