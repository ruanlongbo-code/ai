"""
压力测试 AI 分析器
集成 LLM + RAG 实现:
1. 智能生成压测场景
2. AI推荐压测配置
3. 性能报告AI分析
4. 异常检测与解读
5. 基线对比分析
"""
import json
import logging
from typing import Dict, List, Optional, Any
from config.settings import llm

logger = logging.getLogger(__name__)

NL = "\n"


def _build_scenario_section(scenario_info):
    concurrency = scenario_info.get('concurrency', 'N/A')
    duration = scenario_info.get('duration', 'N/A')
    load_type = scenario_info.get('load_type', 'N/A')
    return f"## 场景信息{NL}并发数: {concurrency}, 持续时间: {duration}s, 负载类型: {load_type}"


def _build_baseline_section(baseline_data):
    data_str = json.dumps(baseline_data, ensure_ascii=False, indent=2)
    return f"## 性能基线对比{NL}{data_str}"


async def ai_generate_scenario(
    api_specs: List[Dict],
    requirement_text: str = "",
    scenario_type: str = "single_api",
    rag_context: str = ""
) -> Dict:
    """
    AI 智能生成压测场景
    - 根据API规格 + 需求描述 + RAG历史知识 生成合理的压测场景
    """
    apis_desc = json.dumps(api_specs, ensure_ascii=False, indent=2)

    prompt = f"""你是一位资深的性能测试专家。请根据以下信息生成一个完整的压测场景配置。

## API信息
{apis_desc}

## 测试需求
{requirement_text or "对以上API进行性能压测"}

## 场景类型
{scenario_type}（single_api=单接口压测, multi_api=多接口混合, chain_api=接口链路）

{('## 历史知识参考' + chr(10) + rag_context) if rag_context else ''}

请返回JSON格式：
```json
{{
    "name": "场景名称",
    "description": "场景描述，说明测试目的和关注点",
    "scenario_type": "{scenario_type}",
    "target_apis": [
        {{
            "method": "GET/POST/...",
            "url": "完整URL",
            "headers": {{"Content-Type": "application/json"}},
            "body": null或请求体,
            "params": null或查询参数,
            "name": "接口说明"
        }}
    ],
    "think_time": 思考时间毫秒数,
    "timeout": 超时秒数,
    "recommended_concurrency": 建议并发数,
    "recommended_duration": 建议持续时间秒,
    "test_focus": ["关注点1", "关注点2"],
    "parameter_data": [参数化数据]或null,
    "parameter_strategy": "sequential或random"
}}
```

要求：
1. URL必须是完整可访问的地址
2. 根据接口类型合理设置headers和body
3. 参数化数据要覆盖边界情况
4. 思考时间要模拟真实用户行为
5. 给出合理的并发数和持续时间建议
"""

    try:
        response = await llm.ainvoke(prompt)
        content = response.content
        # 提取JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content.strip())
    except Exception as e:
        logger.error(f"AI生成场景失败: {e}")
        raise


async def ai_recommend_config(
    scenario_info: Dict,
    test_goal: str = "",
    rag_context: str = ""
) -> Dict:
    """
    AI 推荐最优压测配置
    - 根据场景特点 + 测试目标推荐负载模型、并发数、持续时间等
    """
    prompt = f"""你是性能测试专家。根据以下压测场景信息，推荐最优的压测配置。

## 场景信息
- 场景名称: {scenario_info.get('name', '')}
- 场景类型: {scenario_info.get('scenario_type', '')}
- 目标API数量: {len(scenario_info.get('target_apis', []))}
- API列表: {json.dumps([a.get('name', a.get('url', '')) for a in scenario_info.get('target_apis', [])], ensure_ascii=False)}

## 测试目标
{test_goal or "评估系统在不同负载下的性能表现"}

{('## 历史性能数据参考' + chr(10) + rag_context) if rag_context else ''}

请返回JSON格式：
```json
{{
    "load_type": "constant/ramp_up/spike/soak",
    "load_type_reason": "选择此负载类型的原因",
    "concurrency": 并发用户数,
    "concurrency_reason": "并发数设置依据",
    "ramp_up_time": 梯度加压时间秒(仅ramp_up模式),
    "ramp_up_steps": 梯度步骤数,
    "duration": 持续时间秒,
    "duration_reason": "持续时间设置依据",
    "target_rps": 目标RPS(0=不限制),
    "suggestions": ["建议1", "建议2"],
    "risk_warnings": ["风险提示1"]
}}
```
"""

    try:
        response = await llm.ainvoke(prompt)
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content.strip())
    except Exception as e:
        logger.error(f"AI推荐配置失败: {e}")
        raise


async def ai_analyze_report(
    result_data: Dict,
    scenario_info: Dict = None,
    baseline_data: Dict = None
) -> Dict:
    """
    AI 分析压测结果，生成深度性能洞察报告
    """
    prompt = f"""你是资深性能测试分析专家。请深度分析以下压测结果，生成专业的性能分析报告。

## 压测结果概览
- 总请求数: {result_data.get('total_requests', 0)}
- 成功数/失败数: {result_data.get('success_count', 0)} / {result_data.get('fail_count', 0)}
- 错误率: {result_data.get('error_rate', 0)}%
- TPS: {result_data.get('tps', 0)}
- 平均响应时间: {result_data.get('avg_response_time', 0)}ms
- P50: {result_data.get('p50_response_time', 0)}ms
- P90: {result_data.get('p90_response_time', 0)}ms
- P95: {result_data.get('p95_response_time', 0)}ms
- P99: {result_data.get('p99_response_time', 0)}ms
- 最大响应时间: {result_data.get('max_response_time', 0)}ms

## 各接口明细
{json.dumps(result_data.get('api_details', []), ensure_ascii=False, indent=2)}

## 错误分布
{json.dumps(result_data.get('error_distribution', {}), ensure_ascii=False, indent=2)}

{_build_scenario_section(scenario_info) if scenario_info else ""}

{_build_baseline_section(baseline_data) if baseline_data else ""}

请返回JSON格式：
```json
{{
    "risk_level": "low/medium/high/critical",
    "summary": "一句话总结性能状况",
    "analysis": "详细分析报告(Markdown格式，包含分析维度：响应时间分析、吞吐量分析、错误分析、稳定性分析)",
    "bottleneck_analysis": "瓶颈分析",
    "suggestions": ["优化建议1", "优化建议2", "优化建议3"],
    "highlights": ["亮点1"],
    "concerns": ["关注点1", "关注点2"]
}}
```

分析要求：
1. P99与P50差距过大说明有长尾请求
2. 错误率>1%需要重点关注
3. 分析TPS是否达到预期
4. 与基线对比时标注性能变化趋势
5. 给出具体可执行的优化建议
"""

    try:
        response = await llm.ainvoke(prompt)
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content.strip())
    except Exception as e:
        logger.error(f"AI分析报告失败: {e}")
        raise


async def ai_detect_anomaly(
    current_metrics: Dict,
    history_metrics: List[Dict],
) -> Dict:
    """
    AI 实时异常检测
    分析当前指标是否存在异常，并给出解读
    """
    prompt = f"""你是性能监控专家。分析以下实时压测指标，判断是否存在异常。

## 当前指标
- RPS: {current_metrics.get('rps', 0)}
- 平均响应时间: {current_metrics.get('avg_rt', 0)}ms
- 当前并发: {current_metrics.get('users', 0)}
- 错误数: {current_metrics.get('errors', 0)}

## 近期指标趋势(最近10个采样点)
{json.dumps(history_metrics[-10:], ensure_ascii=False, indent=2)}

请判断当前是否存在异常，返回JSON：
```json
{{
    "is_anomaly": true/false,
    "severity": "info/warning/critical",
    "anomaly_type": "异常类型(如:响应时间突增/错误率飙升/TPS骤降/无异常)",
    "description": "简短说明",
    "suggestion": "建议操作"
}}
```"""

    try:
        response = await llm.ainvoke(prompt)
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content.strip())
    except Exception as e:
        logger.error(f"AI异常检测失败: {e}")
        return {"is_anomaly": False, "severity": "info", "anomaly_type": "检测失败", "description": str(e)}


async def ai_compare_baselines(
    baseline_a: Dict,
    baseline_b: Dict
) -> Dict:
    """
    AI 基线对比分析
    对比两个版本的性能基线，检测性能回归
    """
    prompt = f"""你是性能回归分析专家。对比以下两个性能基线，分析性能变化。

## 基线A: {baseline_a.get('name', '基线A')} (版本: {baseline_a.get('version', 'N/A')})
{json.dumps(baseline_a.get('baseline_metrics', {}), ensure_ascii=False, indent=2)}

## 基线B: {baseline_b.get('name', '基线B')} (版本: {baseline_b.get('version', 'N/A')})
{json.dumps(baseline_b.get('baseline_metrics', {}), ensure_ascii=False, indent=2)}

请对比分析，返回JSON：
```json
{{
    "overall_trend": "improved/degraded/stable",
    "regression_detected": true/false,
    "summary": "对比总结",
    "details": [
        {{
            "api": "接口名",
            "metric": "指标名",
            "baseline_a_value": 值A,
            "baseline_b_value": 值B,
            "change_percent": 变化百分比,
            "trend": "improved/degraded/stable",
            "comment": "说明"
        }}
    ],
    "recommendations": ["建议1", "建议2"],
    "risk_assessment": "风险评估说明"
}}
```"""

    try:
        response = await llm.ainvoke(prompt)
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content.strip())
    except Exception as e:
        logger.error(f"AI基线对比失败: {e}")
        raise
