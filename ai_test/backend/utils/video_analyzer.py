"""
视频评审分析工具
功能：从评审视频中提取关键帧，使用视觉模型分析内容，提取评审要点
"""
import os
import base64
import json
import subprocess
import tempfile
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# 评审类型对应的分析 prompt
REVIEW_PROMPTS = {
    "requirement": """你是一位资深的需求评审专家。请仔细分析这张需求评审会议的截图/幻灯片。
请提取以下信息：
1. **需求要点**：截图中讨论的核心需求内容
2. **业务规则**：提到的业务逻辑和约束条件
3. **边界条件**：讨论的边界场景和异常情况
4. **关键决策**：做出的决策和结论
5. **补充说明**：需求文档中可能遗漏的信息
6. **测试建议**：基于需求讨论，建议重点测试的场景

请用结构化的中文输出，确保信息准确完整。如果截图中没有相关内容，请如实说明。""",

    "technical": """你是一位资深的技术评审专家。请仔细分析这张技术方案评审会议的截图/幻灯片。
请提取以下信息：
1. **技术方案要点**：讨论的技术实现方案
2. **架构设计**：系统架构、接口设计、数据流等
3. **技术风险**：识别的技术风险和应对措施
4. **性能指标**：讨论的性能要求和约束
5. **接口变更**：涉及的API/接口改动
6. **测试建议**：基于技术方案，建议的测试策略和重点

请用结构化的中文输出，确保信息准确完整。如果截图中没有相关内容，请如实说明。""",

    "testcase": """你是一位资深的用例评审专家。请仔细分析这张用例评审会议的截图/幻灯片。
请提取以下信息：
1. **用例补充**：评审中提出需要补充的测试用例
2. **遗漏场景**：发现的遗漏测试场景
3. **优先级调整**：需要调整优先级的用例
4. **测试数据**：讨论的特殊测试数据要求
5. **关联影响**：讨论的功能关联和影响范围
6. **改进建议**：对现有用例的改进意见

请用结构化的中文输出，确保信息准确完整。如果截图中没有相关内容，请如实说明。"""
}

# 汇总分析 prompt
SUMMARY_PROMPT = """你是一位资深的测试专家。以下是从一次{review_type_name}会议视频中提取的多个关键帧分析结果。

请将这些分析结果进行整合汇总，生成一份完整的评审知识文档：

{frame_analyses}

请输出以下内容：

## 评审要点汇总
（合并去重后的核心要点）

## 关键决策
（以JSON数组格式输出关键决策列表）

## 待办事项
（以JSON数组格式输出需要跟进的待办事项）

## 测试影响分析
（对测试工作的影响和建议）

## 补充测试场景
（评审中发现的需要补充的测试场景，这些在需求文档中可能没有体现）

请确保输出内容全面、准确、可直接作为测试用例编写的参考依据。"""

REVIEW_TYPE_NAMES = {
    "requirement": "需求评审",
    "technical": "技术方案评审",
    "testcase": "用例评审",
}


class VideoAnalyzer:
    """视频评审分析器"""

    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL"),
        )
        self.vision_model = os.getenv("VISION_MODEL", os.getenv("LLM_MODEL", "gpt-4o"))

    def extract_frames(self, video_path: str, output_dir: str, interval: int = 30, max_frames: int = 20) -> List[str]:
        """
        使用 ffmpeg 从视频中提取关键帧
        :param video_path: 视频文件路径
        :param output_dir: 帧图片输出目录
        :param interval: 提取间隔（秒），默认每30秒提取一帧
        :param max_frames: 最大提取帧数
        :return: 提取的帧图片路径列表
        """
        os.makedirs(output_dir, exist_ok=True)

        # 先获取视频时长
        duration = self._get_video_duration(video_path)
        if duration <= 0:
            logger.warning("无法获取视频时长，使用默认间隔提取")
            duration = interval * max_frames

        # 根据视频时长动态调整提取间隔
        total_possible_frames = int(duration / interval)
        if total_possible_frames > max_frames:
            interval = int(duration / max_frames)

        # 使用 ffmpeg 提取帧
        output_pattern = os.path.join(output_dir, "frame_%04d.jpg")
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vf", f"fps=1/{interval},scale=1280:-1",  # 每interval秒一帧，缩放到1280宽
            "-q:v", "2",  # JPEG质量
            "-frames:v", str(max_frames),
            output_pattern,
            "-y",  # 覆盖已有文件
            "-loglevel", "error"
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)
        except FileNotFoundError:
            logger.error("ffmpeg 未安装，请先安装 ffmpeg")
            raise RuntimeError("ffmpeg 未安装，请使用 'brew install ffmpeg' (macOS) 或 'apt install ffmpeg' (Linux) 安装")
        except subprocess.TimeoutExpired:
            raise RuntimeError("视频帧提取超时")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"视频帧提取失败: {e.stderr}")

        # 收集提取的帧文件
        frames = sorted([
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if f.startswith("frame_") and f.endswith(".jpg")
        ])

        logger.info(f"从视频中提取了 {len(frames)} 个关键帧")
        return frames

    def _get_video_duration(self, video_path: str) -> float:
        """获取视频时长（秒）"""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return float(result.stdout.strip())
        except Exception:
            return 0

    def _encode_image(self, image_path: str) -> str:
        """将图片编码为 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def analyze_frame(self, frame_path: str, review_type: str) -> str:
        """
        使用视觉模型分析单个帧
        :param frame_path: 帧图片路径
        :param review_type: 评审类型
        :return: 分析结果文本
        """
        prompt = REVIEW_PROMPTS.get(review_type, REVIEW_PROMPTS["requirement"])
        base64_image = self._encode_image(frame_path)

        try:
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"视觉模型分析帧失败: {e}")
            return f"[分析失败: {str(e)}]"

    def analyze_frames_batch(self, frame_paths: List[str], review_type: str) -> List[Dict[str, str]]:
        """
        批量分析多个帧
        :return: [{"frame": "frame_path", "analysis": "分析结果"}, ...]
        """
        results = []
        for i, frame_path in enumerate(frame_paths):
            logger.info(f"正在分析第 {i + 1}/{len(frame_paths)} 帧: {os.path.basename(frame_path)}")
            analysis = self.analyze_frame(frame_path, review_type)
            results.append({
                "frame": os.path.basename(frame_path),
                "frame_index": i + 1,
                "analysis": analysis
            })
        return results

    def generate_summary(self, frame_analyses: List[Dict[str, str]], review_type: str) -> Dict[str, Any]:
        """
        将所有帧的分析结果汇总生成最终评审知识文档
        :return: {"summary": "汇总文本", "key_decisions": [...], "action_items": [...]}
        """
        review_type_name = REVIEW_TYPE_NAMES.get(review_type, "评审")

        # 拼接所有帧分析结果
        analyses_text = "\n\n".join([
            f"### 第{item['frame_index']}帧分析\n{item['analysis']}"
            for item in frame_analyses
        ])

        prompt = SUMMARY_PROMPT.format(
            review_type_name=review_type_name,
            frame_analyses=analyses_text
        )

        try:
            response = self.client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "gpt-4o"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.3,
            )
            summary_text = response.choices[0].message.content

            # 尝试提取关键决策和待办事项
            key_decisions = self._extract_json_list(summary_text, "关键决策")
            action_items = self._extract_json_list(summary_text, "待办事项")

            return {
                "summary": summary_text,
                "key_decisions": key_decisions,
                "action_items": action_items,
            }
        except Exception as e:
            logger.error(f"生成评审汇总失败: {e}")
            return {
                "summary": analyses_text,
                "key_decisions": [],
                "action_items": [],
            }

    def _extract_json_list(self, text: str, section_name: str) -> List[str]:
        """从文本中提取JSON数组"""
        import re
        # 查找 section_name 之后的JSON数组
        pattern = rf'{section_name}.*?\[([^\]]*)\]'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                arr_str = "[" + match.group(1) + "]"
                return json.loads(arr_str)
            except json.JSONDecodeError:
                # 尝试按行提取
                lines = match.group(1).strip().split("\n")
                return [line.strip().strip('",').strip('"') for line in lines if line.strip()]
        return []

    def full_analysis(self, video_path: str, review_type: str, frames_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        完整的视频分析流程
        :return: 包含分析结果的字典
        """
        if frames_dir is None:
            frames_dir = tempfile.mkdtemp(prefix="review_frames_")

        # 1. 提取关键帧
        logger.info(f"开始提取视频关键帧: {video_path}")
        frame_paths = self.extract_frames(video_path, frames_dir)

        if not frame_paths:
            raise RuntimeError("未能从视频中提取到任何帧")

        # 2. 逐帧分析
        logger.info(f"开始分析 {len(frame_paths)} 个关键帧")
        frame_analyses = self.analyze_frames_batch(frame_paths, review_type)

        # 3. 汇总生成
        logger.info("开始生成评审汇总")
        summary = self.generate_summary(frame_analyses, review_type)

        return {
            "frame_count": len(frame_paths),
            "frame_analyses": frame_analyses,
            "summary": summary["summary"],
            "key_decisions": summary["key_decisions"],
            "action_items": summary["action_items"],
        }
