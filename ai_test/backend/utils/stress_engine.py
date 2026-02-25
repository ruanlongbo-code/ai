"""
压力测试引擎 - 基于 asyncio + aiohttp 实现高并发压测
支持多种负载模型: 恒定(constant), 梯度加压(ramp_up), 尖峰(spike), 耐久(soak)
"""
import asyncio
import time
import statistics
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
import aiohttp
import json

logger = logging.getLogger(__name__)


@dataclass
class RequestResult:
    """单次请求结果"""
    url: str
    method: str
    status_code: int
    response_time: float  # ms
    content_length: int
    success: bool
    error: Optional[str] = None
    timestamp: float = 0


@dataclass
class MetricSnapshot:
    """指标快照(每秒采集)"""
    timestamp: float
    current_users: int
    requests_per_second: float
    avg_response_time: float
    error_count: int
    active_connections: int


@dataclass
class StressTestReport:
    """压测最终报告"""
    total_requests: int = 0
    success_count: int = 0
    fail_count: int = 0
    error_rate: float = 0
    avg_response_time: float = 0
    min_response_time: float = 0
    max_response_time: float = 0
    p50_response_time: float = 0
    p90_response_time: float = 0
    p95_response_time: float = 0
    p99_response_time: float = 0
    tps: float = 0
    throughput: float = 0
    api_details: list = field(default_factory=list)
    error_distribution: dict = field(default_factory=dict)
    duration: float = 0


class StressEngine:
    """压测引擎"""

    def __init__(
        self,
        target_apis: List[Dict],
        concurrency: int = 10,
        duration: int = 60,
        load_type: str = "constant",
        ramp_up_time: int = 0,
        ramp_up_steps: int = 1,
        target_rps: int = 0,
        think_time: int = 0,
        timeout: int = 30,
        parameter_data: Optional[List[Dict]] = None,
        parameter_strategy: str = "sequential",
        on_metric: Optional[Callable] = None,  # 实时指标回调
        on_anomaly: Optional[Callable] = None,  # 异常检测回调
    ):
        self.target_apis = target_apis
        self.concurrency = concurrency
        self.duration = duration
        self.load_type = load_type
        self.ramp_up_time = ramp_up_time
        self.ramp_up_steps = ramp_up_steps
        self.target_rps = target_rps
        self.think_time = think_time / 1000.0 if think_time else 0  # convert ms to sec
        self.timeout = timeout
        self.parameter_data = parameter_data or []
        self.parameter_strategy = parameter_strategy
        self.on_metric = on_metric
        self.on_anomaly = on_anomaly

        # 运行状态
        self._running = False
        self._stop_event = asyncio.Event()
        self._results: List[RequestResult] = []
        self._metrics: List[MetricSnapshot] = []
        self._param_index = 0
        self._current_users = 0
        self._active_connections = 0
        self._lock = asyncio.Lock()

        # 异常检测用
        self._recent_rt_values: List[float] = []

    async def run(self) -> StressTestReport:
        """执行压测"""
        self._running = True
        self._stop_event.clear()
        start_time = time.time()

        connector = aiohttp.TCPConnector(limit=self.concurrency * 2, force_close=False)
        timeout_config = aiohttp.ClientTimeout(total=self.timeout)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout_config) as session:
            # 启动指标采集
            metric_task = asyncio.create_task(self._collect_metrics(start_time))

            if self.load_type == "constant":
                await self._run_constant(session, start_time)
            elif self.load_type == "ramp_up":
                await self._run_ramp_up(session, start_time)
            elif self.load_type == "spike":
                await self._run_spike(session, start_time)
            elif self.load_type == "soak":
                await self._run_constant(session, start_time)  # soak = long constant

            self._running = False
            metric_task.cancel()
            try:
                await metric_task
            except asyncio.CancelledError:
                pass

        total_duration = time.time() - start_time
        return self._generate_report(total_duration)

    def stop(self):
        """停止压测"""
        self._stop_event.set()
        self._running = False

    async def _run_constant(self, session: aiohttp.ClientSession, start_time: float):
        """恒定负载"""
        tasks = []
        for i in range(self.concurrency):
            tasks.append(asyncio.create_task(self._worker(session, i, start_time)))
        self._current_users = self.concurrency
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_ramp_up(self, session: aiohttp.ClientSession, start_time: float):
        """梯度加压"""
        if self.ramp_up_steps <= 0:
            self.ramp_up_steps = 1
        users_per_step = max(1, self.concurrency // self.ramp_up_steps)
        step_duration = self.ramp_up_time / self.ramp_up_steps if self.ramp_up_steps > 0 else 0

        tasks = []
        worker_id = 0
        for step in range(self.ramp_up_steps):
            # 每步增加用户
            users_this_step = min(users_per_step, self.concurrency - len(tasks))
            for _ in range(users_this_step):
                tasks.append(asyncio.create_task(self._worker(session, worker_id, start_time)))
                worker_id += 1
            self._current_users = len(tasks)

            if step < self.ramp_up_steps - 1:
                await asyncio.sleep(step_duration)
                if self._stop_event.is_set():
                    break

        # 剩余时间保持最大并发
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_spike(self, session: aiohttp.ClientSession, start_time: float):
        """尖峰负载: 正常10%并发 -> 突然拉满 -> 恢复"""
        base_users = max(1, self.concurrency // 10)
        spike_at = self.duration * 0.3   # 30%时开始尖峰
        spike_end = self.duration * 0.6  # 60%时恢复

        tasks = []
        # Phase 1: 基础负载
        for i in range(base_users):
            tasks.append(asyncio.create_task(self._worker(session, i, start_time)))
        self._current_users = base_users

        # 等到尖峰时间
        while time.time() - start_time < spike_at and not self._stop_event.is_set():
            await asyncio.sleep(0.5)

        # Phase 2: 尖峰
        spike_tasks = []
        for i in range(base_users, self.concurrency):
            spike_tasks.append(asyncio.create_task(self._worker(session, i, start_time)))
        self._current_users = self.concurrency

        # 等到恢复时间
        while time.time() - start_time < spike_end and not self._stop_event.is_set():
            await asyncio.sleep(0.5)

        # Phase 3: 恢复 - 取消额外任务
        for t in spike_tasks:
            t.cancel()
        self._current_users = base_users

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _worker(self, session: aiohttp.ClientSession, worker_id: int, start_time: float):
        """单个虚拟用户的工作循环"""
        api_index = 0
        while not self._stop_event.is_set() and (time.time() - start_time) < self.duration:
            api = self.target_apis[api_index % len(self.target_apis)]
            api_index += 1

            # 参数化替换
            resolved_api = self._resolve_parameters(api)

            result = await self._send_request(session, resolved_api)
            async with self._lock:
                self._results.append(result)

            if self.think_time > 0:
                await asyncio.sleep(self.think_time)

    async def _send_request(self, session: aiohttp.ClientSession, api: Dict) -> RequestResult:
        """发送单个请求"""
        method = api.get("method", "GET").upper()
        url = api.get("url", "")
        headers = api.get("headers", {})
        body = api.get("body")
        params = api.get("params")

        async with self._lock:
            self._active_connections += 1

        start = time.time()
        try:
            kwargs = {"headers": headers, "params": params}
            if body and method in ("POST", "PUT", "PATCH"):
                if isinstance(body, dict):
                    kwargs["json"] = body
                else:
                    kwargs["data"] = body

            async with session.request(method, url, **kwargs) as resp:
                content = await resp.read()
                elapsed = (time.time() - start) * 1000
                return RequestResult(
                    url=url,
                    method=method,
                    status_code=resp.status,
                    response_time=elapsed,
                    content_length=len(content),
                    success=200 <= resp.status < 400,
                    timestamp=time.time()
                )
        except asyncio.TimeoutError:
            elapsed = (time.time() - start) * 1000
            return RequestResult(
                url=url, method=method, status_code=0,
                response_time=elapsed, content_length=0,
                success=False, error="Timeout", timestamp=time.time()
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return RequestResult(
                url=url, method=method, status_code=0,
                response_time=elapsed, content_length=0,
                success=False, error=str(e), timestamp=time.time()
            )
        finally:
            async with self._lock:
                self._active_connections -= 1

    def _resolve_parameters(self, api: Dict) -> Dict:
        """参数化替换"""
        if not self.parameter_data:
            return api

        if self.parameter_strategy == "random":
            import random
            params = random.choice(self.parameter_data)
        else:  # sequential
            params = self.parameter_data[self._param_index % len(self.parameter_data)]
            self._param_index += 1

        # 替换 url, headers, body 中的 {{key}} 占位符
        api_str = json.dumps(api, ensure_ascii=False)
        for key, value in params.items():
            api_str = api_str.replace(f"{{{{{key}}}}}", str(value))
        return json.loads(api_str)

    async def _collect_metrics(self, start_time: float):
        """每秒采集指标"""
        last_count = 0
        last_error_count = 0
        while self._running:
            await asyncio.sleep(1)
            current_time = time.time()

            async with self._lock:
                current_count = len(self._results)
                current_errors = sum(1 for r in self._results[last_count:] if not r.success)
                recent_rts = [r.response_time for r in self._results[last_count:] if r.success]

            rps = current_count - last_count
            avg_rt = statistics.mean(recent_rts) if recent_rts else 0

            snapshot = MetricSnapshot(
                timestamp=current_time,
                current_users=self._current_users,
                requests_per_second=rps,
                avg_response_time=round(avg_rt, 2),
                error_count=current_errors,
                active_connections=self._active_connections
            )
            self._metrics.append(snapshot)

            # 简单异常检测: RT突增或错误率突增
            is_anomaly = False
            anomaly_reason = ""
            self._recent_rt_values.append(avg_rt)
            if len(self._recent_rt_values) > 10:
                baseline_rt = statistics.mean(self._recent_rt_values[-10:-1])
                if baseline_rt > 0 and avg_rt > baseline_rt * 3:
                    is_anomaly = True
                    anomaly_reason = f"响应时间突增: {avg_rt:.0f}ms (基线: {baseline_rt:.0f}ms)"
            if rps > 0 and current_errors / rps > 0.3:
                is_anomaly = True
                anomaly_reason = f"错误率突增: {current_errors}/{rps} ({current_errors/rps*100:.1f}%)"

            if self.on_metric:
                try:
                    await self.on_metric(snapshot, is_anomaly, anomaly_reason)
                except Exception as e:
                    logger.error(f"Metric callback error: {e}")

            last_count = current_count

    def _generate_report(self, total_duration: float) -> StressTestReport:
        """生成最终报告"""
        if not self._results:
            return StressTestReport(duration=total_duration)

        rts = [r.response_time for r in self._results]
        success_rts = [r.response_time for r in self._results if r.success]
        sorted_rts = sorted(rts)
        n = len(sorted_rts)

        success_count = sum(1 for r in self._results if r.success)
        fail_count = n - success_count
        total_bytes = sum(r.content_length for r in self._results)

        # 按接口分组统计
        api_stats: Dict[str, List[RequestResult]] = {}
        error_dist: Dict[str, int] = {}
        for r in self._results:
            key = f"{r.method} {r.url}"
            api_stats.setdefault(key, []).append(r)
            if not r.success:
                err_key = str(r.status_code) if r.status_code else (r.error or "Unknown")
                error_dist[err_key] = error_dist.get(err_key, 0) + 1

        api_details = []
        for key, results in api_stats.items():
            parts = key.split(" ", 1)
            api_rts = sorted([r.response_time for r in results])
            api_n = len(api_rts)
            api_errors = sum(1 for r in results if not r.success)
            api_details.append({
                "method": parts[0],
                "url": parts[1] if len(parts) > 1 else "",
                "total": api_n,
                "success": api_n - api_errors,
                "avg_rt": round(statistics.mean(api_rts), 2),
                "p99_rt": round(api_rts[int(api_n * 0.99)] if api_n > 0 else 0, 2),
                "error_rate": round(api_errors / api_n * 100, 2) if api_n > 0 else 0,
                "tps": round(api_n / total_duration, 2) if total_duration > 0 else 0,
            })

        return StressTestReport(
            total_requests=n,
            success_count=success_count,
            fail_count=fail_count,
            error_rate=round(fail_count / n * 100, 2) if n > 0 else 0,
            avg_response_time=round(statistics.mean(rts), 2),
            min_response_time=round(min(rts), 2),
            max_response_time=round(max(rts), 2),
            p50_response_time=round(sorted_rts[int(n * 0.50)], 2),
            p90_response_time=round(sorted_rts[int(n * 0.90)], 2),
            p95_response_time=round(sorted_rts[int(n * 0.95)], 2),
            p99_response_time=round(sorted_rts[min(int(n * 0.99), n - 1)], 2),
            tps=round(n / total_duration, 2) if total_duration > 0 else 0,
            throughput=round(total_bytes / total_duration, 2) if total_duration > 0 else 0,
            api_details=api_details,
            error_distribution=error_dist,
            duration=round(total_duration, 2),
        )

    def get_metrics(self) -> List[MetricSnapshot]:
        return self._metrics
