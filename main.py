from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional
from pathlib import Path

import httpx
import chardet

from astrbot.api import logger, star
from astrbot.api.event import AstrMessageEvent, MessageEventResult, filter
from astrbot.api.star import Context
from astrbot.core.config.astrbot_config import AstrBotConfig
import astrbot.api.message_components as Comp


@dataclass
class Lesson:
    id: str
    title: str
    goals: list[str]
    explanation: str
    examples: list[str]
    exercises: list[str]
    quiz: list[str]


@dataclass
class Module:
    id: str
    title: str
    lessons: list[Lesson]


def _mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "*" * len(key)
    return key[:3] + "*" * (len(key) - 6) + key[-3:]


def _safe_int(s: str, default: int | None = None) -> int | None:
    try:
        return int(s)
    except Exception:
        return default


def _compact_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _normalize_arg_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _clean_multiline_payload(s: str) -> str:
    return (s or "").strip("\n").strip()


def _parse_py_command(raw_text: str) -> tuple[str, str]:
    raw_text = (raw_text or "").strip()
    if not raw_text:
        return "", ""

    if "\n" in raw_text:
        first_line, rest = raw_text.split("\n", 1)
        rest = rest.strip("\n")
    else:
        first_line, rest = raw_text, ""

    first_line = first_line.strip()
    tokens = re.split(r"\s+", first_line, maxsplit=2)
    if len(tokens) < 2:
        return "", ""

    sub = tokens[1]
    arg_from_line = tokens[2] if len(tokens) >= 3 else ""

    if arg_from_line and rest:
        return sub, arg_from_line + "\n" + rest
    if arg_from_line:
        return sub, arg_from_line
    return sub, rest


def _recover_newlines(s: str) -> str:
    if "\n" in s:
        return s
    return s.replace(" / ", "\n").replace(" /", "\n").replace("/ ", "\n")


def _read_text_file(file_path: str) -> str:
    """读取文本文件，自动检测编码"""
    try:
        with open(file_path, "rb") as f:
            raw_data = f.read()
            encoding = chardet.detect(raw_data)["encoding"] or "utf-8"
        return raw_data.decode(encoding)
    except Exception as e:
        logger.error(f"读取文件失败 {file_path}: {e}")
        raise RuntimeError(f"读取文件失败: {e}")


def _build_curriculum() -> list[Module]:
    modules: list[Module] = []

    modules.append(
        Module(
            id="1",
            title="Python 基础入门",
            lessons=[
                Lesson(
                    id="1.1",
                    title="环境与第一个程序",
                    goals=["理解解释器与脚本", "能运行一个 .py 文件", "知道 print 的基本用法"],
                    explanation=(
                        "Python 是解释型语言。你可以在命令行运行 python 来进入交互模式，"
                        "也可以把代码写进 .py 文件中执行。学习时建议同时掌握：运行脚本、阅读报错、"
                        "以及用 print 做最小验证。"
                    ),
                    examples=[
                        "print('Hello, Python!')",
                        "name = 'Alice'\nprint('Hello', name)",
                    ],
                    exercises=[
                        "写一个脚本，打印三行内容：你的名字、当前日期（手写字符串即可）、你学习 Python 的目标。",
                        "修改脚本，让它把两数相加的结果打印出来（先用固定数字）。",
                    ],
                    quiz=[
                        "解释器与 .py 脚本运行的区别是什么？",
                        "print 可以打印哪些类型的值？",
                    ],
                ),
                Lesson(
                    id="1.2",
                    title="变量、类型与基本运算",
                    goals=["知道常见类型：int/float/str/bool", "会做基本运算", "理解赋值与引用的直觉"],
                    explanation=(
                        "变量是名字，指向一个对象。常见类型包括整数、浮点、字符串、布尔。"
                        "初学阶段重点：能读懂表达式，知道运算优先级，能用 type() 和 print() 验证。"
                    ),
                    examples=[
                        "a = 10\nb = 3\nprint(a + b, a / b, a // b, a % b)",
                        "s = 'py'\nprint(s * 3)",
                        "flag = (2 + 2 == 4)\nprint(flag)",
                    ],
                    exercises=[
                        "给定摄氏温度 c=30，计算华氏温度 f 并打印（公式：f=c*9/5+32）。",
                        "写一个脚本，判断一个数 n 是否为偶数，并打印 True/False。",
                    ],
                    quiz=[
                        "a/b 与 a//b 的区别是什么？",
                        "字符串乘法 'a'*3 会得到什么？",
                    ],
                ),
            ],
        )
    )

    modules.append(
        Module(
            id="2",
            title="流程控制与函数",
            lessons=[
                Lesson(
                    id="2.1",
                    title="条件与循环",
                    goals=["会写 if/elif/else", "会写 for/while", "能用 break/continue"],
                    explanation=(
                        "条件分支用于处理不同情况；循环用于重复执行。掌握循环变量、范围、以及停止条件。"
                        "建议练习时把每一步打印出来，以便理解控制流。"
                    ),
                    examples=[
                        "n = 5\nif n % 2 == 0:\n    print('even')\nelse:\n    print('odd')",
                        "for i in range(3):\n    print(i)",
                        "i = 0\nwhile i < 3:\n    print(i)\n    i += 1",
                    ],
                    exercises=[
                        "打印 1~100 中所有 3 的倍数。",
                        "给定一个列表 [3,1,4,1,5]，求和并打印。",
                    ],
                    quiz=[
                        "range(3) 会产生哪些值？",
                        "break 和 continue 的区别是什么？",
                    ],
                ),
                Lesson(
                    id="2.2",
                    title="函数与参数",
                    goals=["会定义函数 def", "理解参数与返回值", "会写简单的 docstring"],
                    explanation=(
                        "函数用于复用逻辑。学习函数时把关注点放在：输入是什么、输出是什么、边界情况是什么。"
                        "建议每个函数都先写 2~3 个例子（输入->输出），再写实现。"
                    ),
                    examples=[
                        "def add(a, b):\n    return a + b\n\nprint(add(2, 3))",
                        "def clamp(x, lo=0, hi=10):\n    return max(lo, min(hi, x))\n\nprint(clamp(15))",
                    ],
                    exercises=[
                        "写一个函数 is_prime(n) 判断素数（先处理 n<2）。",
                        "写一个函数 summarize(nums) 返回 (count, sum, avg)。",
                    ],
                    quiz=[
                        "return 的作用是什么？",
                        "默认参数什么时候计算？",
                    ],
                ),
            ],
        )
    )

    modules.append(
        Module(
            id="3",
            title="数据结构与常用库",
            lessons=[
                Lesson(
                    id="3.1",
                    title="list/dict/set/tuple",
                    goals=["会使用常见数据结构", "会做遍历与查询", "能选择合适结构"],
                    explanation=(
                        "list 适合有序集合；tuple 通常表示不可变记录；dict 适合键值映射；set 适合去重与集合运算。"
                        "学习重点：增删改查、遍历、以及典型用法（统计、索引、去重）。"
                    ),
                    examples=[
                        "nums = [1,2,2,3]\nprint(set(nums))",
                        "m = {'a': 1, 'b': 2}\nprint(m.get('c', 0))",
                        "pairs = [('a', 1), ('b', 2)]\nprint(dict(pairs))",
                    ],
                    exercises=[
                        "统计一句话中每个单词出现次数（结果用 dict）。",
                        "给定 nums 列表，返回去重后的列表（保持原顺序）。",
                    ],
                    quiz=[
                        "dict.get(key, default) 的意义是什么？",
                        "set 的一个典型用途是什么？",
                    ],
                ),
                Lesson(
                    id="3.2",
                    title="文件与 JSON",
                    goals=["会读写文本文件", "会用 json 序列化", "理解编码与异常"],
                    explanation=(
                        "文件读写要注意编码与异常处理。json 是常用的数据交换格式，适合保存结构化配置。"
                        "建议练习：先写一个 dict -> json -> 文件，再读回来验证。"
                    ),
                    examples=[
                        "import json\nobj = {'a': 1}\ntext = json.dumps(obj, ensure_ascii=False)\nprint(text)",
                        "with open('a.txt','w',encoding='utf-8') as f:\n    f.write('hello')",
                    ],
                    exercises=[
                        "把一份学习计划（列表/字典）保存成 json 文件，再读出来打印。",
                        "读取一个文本文件，统计行数与字符数。",
                    ],
                    quiz=[
                        "为什么写文件时要显式指定 encoding='utf-8'？",
                        "json.dumps 与 json.dump 的区别是什么？",
                    ],
                ),
            ],
        )
    )

    modules.append(
        Module(
            id="4",
            title="工程化与进阶",
            lessons=[
                Lesson(
                    id="4.1",
                    title="调试、异常与日志",
                    goals=["会读 traceback", "会用 try/except", "会写最小可复现"],
                    explanation=(
                        "遇到报错先看 traceback 最后一行，再向上找触发点。处理异常时：只捕获你能处理的异常，"
                        "并输出有用信息。调试靠最小复现：缩小输入与代码范围直到错误稳定出现。"
                    ),
                    examples=[
                        "try:\n    x = int('a')\nexcept ValueError as e:\n    print('bad input', e)",
                    ],
                    exercises=[
                        "写一个函数 safe_int(s, default=None)，转换失败返回 default。",
                        "构造一个会报错的例子，并写出你如何从 traceback 定位问题。",
                    ],
                    quiz=[
                        "为什么不建议用裸 except: 直接吞掉异常？",
                        "最小可复现（MRE）是什么？",
                    ],
                ),
                Lesson(
                    id="4.2",
                    title="模块、包与虚拟环境",
                    goals=["理解 import 机制的直觉", "会创建 venv", "知道依赖管理基本方式"],
                    explanation=(
                        "模块是 .py 文件，包是包含 __init__.py 的目录。虚拟环境用于隔离依赖。"
                        "工程化的第一步是：固定依赖、固定入口、让别人能复现运行。"
                    ),
                    examples=[
                        "python -m venv .venv",
                        "pip install requests",
                    ],
                    exercises=[
                        "为一个小项目创建虚拟环境并安装一个依赖，然后写个脚本使用它。",
                        "把一个脚本拆成两个模块，体验 import。",
                    ],
                    quiz=[
                        "为什么要用虚拟环境？",
                        "包与模块的区别是什么？",
                    ],
                ),
            ],
        )
    )

    return modules


class PythonTeacher(star.Star):
    def __init__(self, context: Context, config: AstrBotConfig | dict | None = None):
        super().__init__(context)
        self._config = config
        self._modules = _build_curriculum()
        self._mem_state: dict[str, dict[str, Any]] = {}
        self._file_cache: Dict[str, list[Dict[str, Any]]] = {}  # {session_id: [{file_name, content, timestamp}, ...]}

    def _get_plugin_config(self) -> dict[str, Any]:
        cfg = self._config
        if cfg is None:
            return {}

        if isinstance(cfg, dict):
            if any(k in cfg for k in ("api_base", "api_key", "model", "system_profile", "max_turns")):
                return cfg
            plugin_settings = cfg.get("plugin_settings")
            if isinstance(plugin_settings, dict):
                nested = plugin_settings.get("python_teacher")
                if isinstance(nested, dict):
                    return nested
            nested = cfg.get("python_teacher")
            if isinstance(nested, dict):
                return nested
            return {}

        try:
            plugin_settings = getattr(cfg, "plugin_settings", None)
            if isinstance(plugin_settings, dict):
                nested = plugin_settings.get("python_teacher")
                if isinstance(nested, dict):
                    return nested
        except Exception:
            return {}

        return {}

    def _cfg(self, key: str, default: Any = None) -> Any:
        value = self._get_plugin_config().get(key, default)
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return default
        return value

    async def initialize(self):
        logger.info("python_teacher initialized")

    def _state_key(self, event: AstrMessageEvent) -> str:
        session = getattr(event, "unified_msg_origin", None) or getattr(event, "session", None)
        return f"python_teacher:{session}"

    async def _load_state(self, event: AstrMessageEvent) -> dict[str, Any]:
        key = self._state_key(event)
        if hasattr(self, "kv_get"):
            try:
                value = await self.kv_get(key)
                if not value:
                    return {}
                if isinstance(value, dict):
                    return value
                if isinstance(value, str):
                    return json.loads(value)
            except Exception:
                return {}
        return self._mem_state.get(key, {})

    async def _save_state(self, event: AstrMessageEvent, state: dict[str, Any]) -> None:
        key = self._state_key(event)
        if hasattr(self, "kv_set"):
            await self.kv_set(key, _compact_json(state))
        else:
            self._mem_state[key] = state

    def _find_lesson(self, lesson_id: str) -> Lesson | None:
        for m in self._modules:
            for l in m.lessons:
                if l.id == lesson_id:
                    return l
        return None

    def _find_prev_next_lesson(self, lesson_id: str) -> tuple[Lesson | None, Lesson | None]:
        all_lessons = []
        for m in self._modules:
            all_lessons.extend(m.lessons)
        idx = None
        for i, l in enumerate(all_lessons):
            if l.id == lesson_id:
                idx = i
                break
        if idx is None:
            return None, None
        prev = all_lessons[idx - 1] if idx > 0 else None
        next = all_lessons[idx + 1] if idx < len(all_lessons) - 1 else None
        return prev, next

    def _lesson_by_index(self, module: Module, index: int) -> Lesson | None:
        if index < 1 or index > len(module.lessons):
            return None
        return module.lessons[index - 1]

    def _find_module(self, module_id_or_title: str) -> Module | None:
        q = _normalize_arg_text(module_id_or_title)
        for m in self._modules:
            if m.id == q:
                return m
        for m in self._modules:
            if q and q in m.title:
                return m
        return None

    def _format_help(self) -> str:
        lines: list[str] = []
        lines.append("Python 学习教练 - 帮助信息")
        lines.append("指令前缀：/py（别名：/python /Python）")
        lines.append("")
        lines.append("子命令：")
        lines.append("- 路线 / route          查看系统学习路线")
        lines.append("- 开始 / start          初始化学习进度，进入第一课")
        lines.append("- 状态 / status         查看当前学习进度")
        lines.append("- 模块 <编号>           查看某模块的课程列表")
        lines.append("- 课 <编号>             进入某一课（如：/py 课 1.1）")
        lines.append("- 下 / next             进入下一课")
        lines.append("- 上 / prev             进入上一课")
        lines.append("- 练习 / exercise       生成当前课的练习题")
        lines.append("- 答案 <你的答案/数量>  提交练习答案（文字）或指定文件数量（1-5，默认1）")
        lines.append("- 测验 / quiz           对当前课进行小测")
        lines.append("- 问 <问题>             向 AI 教练提问，也支持先上传文件再：/py 问 <文件数量> <问题>")
        lines.append("- 配置 / config         查看当前 AI 配置")
        lines.append("- 清空记忆 / clear      清空 AI 对话历史记忆")
        lines.append("")
        lines.append("快速开始：/py 开始")
        lines.append("")
        lines.append("提示：先上传多个文件（.py/.txt/.md/.ipynb），再发 /py 答案 3，将使用最后3个文件作为答案。")
        return "\n".join(lines)

    def _format_route(self) -> str:
        lines: list[str] = []
        lines.append("Python 学习路线：")
        for m in self._modules:
            lines.append(f"{m.id}. {m.title}（{len(m.lessons)} 课）")
        lines.append("\n用法：/py 开始 | /py 状态 | /py 模块 1 | /py 课 1.1 | /py 练习 | /py 问 你的问题")
        return "\n".join(lines)

    def _format_module(self, module: Module) -> str:
        lines: list[str] = []
        lines.append(f"模块 {module.id}：{module.title}")
        for i, l in enumerate(module.lessons, start=1):
            lines.append(f"- {l.id} {l.title}")
        lines.append("\n用法：/py 课 1.1")
        return "\n".join(lines)

    def _format_lesson(self, lesson: Lesson) -> str:
        lines: list[str] = []
        lines.append(f"课 {lesson.id}：{lesson.title}")
        lines.append("\n目标：")
        for g in lesson.goals:
            lines.append(f"- {g}")
        lines.append("\n讲解：")
        lines.append(lesson.explanation)
        lines.append("\n示例：")
        for ex in lesson.examples:
            lines.append(ex)
        lines.append("\n下一步：/py 练习 或 /py 问 你的问题")
        lines.append("切换课：/py 下 或 /py 上")
        return "\n".join(lines)

    async def _ensure_started(self, event: AstrMessageEvent) -> dict[str, Any]:
        state = await self._load_state(event)
        if not state:
            state = {"current_lesson": "1.1", "last_exercise": None, "last_answer": None, "conversation_history": []}
            await self._save_state(event, state)
        return state

    async def _call_openai_compatible(self, messages: list[dict[str, str]]) -> str:
        api_base = (self._cfg("api_base", "") or "").rstrip("/")
        api_key = self._cfg("api_key", "") or ""
        model = self._cfg("model", "") or ""

        if not api_base:
            raise RuntimeError(f"api_base is empty. plugin_config={_compact_json(self._get_plugin_config())}")

        url = f"{api_base}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,
        }

        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        choices = data.get("choices") or []
        if not choices:
            return ""
        msg = (choices[0] or {}).get("message") or {}
        content = msg.get("content")
        return content or ""

    def _build_study_prompt(self, state: dict[str, Any], user_question: str) -> list[dict[str, str]]:
        lesson_id = state.get("current_lesson") or "1.1"
        lesson = self._find_lesson(lesson_id)

        system_profile = self._cfg(
            "system_profile",
            "你是一名资深 Python 教练。你会用循序渐进的方式教学：先目标，再解释，再例子，再练习，再检查答案。回答要简洁、准确、可执行。",
        )

        context_lines: list[str] = []
        context_lines.append("学习插件上下文：")
        context_lines.append(f"- 当前课：{lesson_id}")
        if lesson is not None:
            context_lines.append(f"- 课题：{lesson.title}")
            context_lines.append(f"- 本课目标：{'; '.join(lesson.goals)}")
        if state.get("last_exercise"):
            context_lines.append("- 上次练习题：" + str(state.get("last_exercise")))
        if state.get("last_answer"):
            context_lines.append("- 你的上次答案：" + str(state.get("last_answer")))

        user_block = "\n".join(context_lines) + "\n\n用户问题：" + user_question

        messages: list[dict[str, str]] = [{"role": "system", "content": system_profile}]
        # 把历史对话加进去
        history = state.get("conversation_history", [])
        messages.extend(history)
        # 最后加当前用户问题
        messages.append({"role": "user", "content": user_block})
        return messages

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_receive_msg(self, event: AstrMessageEvent):
        """当收到消息时，检查是否有文件并缓存（按会话保存多个文件）"""
        has_file = False
        for item in event.message_obj.message:
            if isinstance(item, Comp.File):
                has_file = True
                break

        if has_file:
            session_id = event.unified_msg_origin
            if session_id not in self._file_cache:
                self._file_cache[session_id] = []
            for item in event.message_obj.message:
                if isinstance(item, Comp.File):
                    try:
                        file_path = await item.get_file()
                        file_name = os.path.basename(file_path)

                        # 只支持文本类文件
                        ext = os.path.splitext(file_name)[1].lower()
                        allowed_exts = {
                            # Python & 脚本
                            ".py", ".pyw", ".ipynb",
                            # Web
                            ".html", ".htm", ".css", ".scss", ".sass", ".less",
                            ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte",
                            # 编译型语言
                            ".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".hxx", ".hh",
                            ".java", ".kt", ".kts", ".go", ".rs", ".swift", ".cs",
                            # 解释型语言
                            ".rb", ".php", ".pl", ".pm", ".lua", ".sh", ".bash", ".zsh", ".fish",
                            ".bat", ".cmd", ".ps1", ".psm1",
                            # 配置 & 数据
                            ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env",
                            ".csv", ".tsv", ".jsonl", ".jsonc",
                            # 文档 & 文本
                            ".md", ".txt", ".rst", ".org",
                            # 其他常见格式
                            ".xml", ".svg", ".graphql", ".gql", ".sql", ".r", ".jl",
                        }
                        if ext not in allowed_exts:
                            continue

                        # 读取文件
                        content = _read_text_file(file_path)

                        # 缓存（往列表追加）
                        import time
                        file_info = {
                            "file_name": file_name,
                            "content": content,
                            "timestamp": time.time(),
                        }
                        self._file_cache[session_id].append(file_info)
                        logger.info(f"已缓存文件: {session_id} / {file_name}，大小 {len(content)} 字符，当前会话共 {len(self._file_cache[session_id])} 个文件")
                    except Exception as e:
                        logger.error(f"缓存文件失败: {e}")

    @filter.command("py", alias={"python", "Python"})
    async def py_entry(self, event: AstrMessageEvent):
        raw_text = event.get_message_str()
        sub, arg = _parse_py_command(raw_text)
        if not sub:
            event.set_result(MessageEventResult().message(self._format_route()).use_t2i(False))
            return

        arg = _clean_multiline_payload(arg)
        arg = _recover_newlines(arg)

        if sub in {"帮助", "help", "?"}:
            event.set_result(MessageEventResult().message(self._format_help()).use_t2i(False))
            return

        if sub in {"路线", "route"}:
            event.set_result(MessageEventResult().message(self._format_route()).use_t2i(False))
            return

        if sub in {"开始", "start"}:
            state = {"current_lesson": "1.1", "last_exercise": None, "last_answer": None}
            await self._save_state(event, state)
            msg = "已初始化学习进度。\n\n" + self._format_lesson(self._find_lesson("1.1"))
            event.set_result(MessageEventResult().message(msg).use_t2i(False))
            return

        if sub in {"状态", "status"}:
            state = await self._ensure_started(event)
            lesson_id = state.get("current_lesson")
            lesson = self._find_lesson(lesson_id)
            msg = f"当前课：{lesson_id}"
            if lesson is not None:
                msg += f"（{lesson.title}）"
            event.set_result(MessageEventResult().message(msg).use_t2i(False))
            return

        if sub in {"模块", "module"}:
            state = await self._ensure_started(event)
            module = self._find_module(arg) if arg else None
            if module is None:
                event.set_result(MessageEventResult().message("用法：/py 模块 <模块编号或名称关键词>").use_t2i(False))
                return
            event.set_result(MessageEventResult().message(self._format_module(module)).use_t2i(False))
            return

        if sub in {"课", "lesson"}:
            state = await self._ensure_started(event)
            lesson_id = _normalize_arg_text(arg)
            lesson = self._find_lesson(lesson_id)
            if lesson is None:
                event.set_result(MessageEventResult().message("课不存在。示例：/py 课 1.1").use_t2i(False))
                return
            state["current_lesson"] = lesson_id
            state["last_exercise"] = None
            state["last_answer"] = None
            await self._save_state(event, state)
            event.set_result(MessageEventResult().message(self._format_lesson(lesson)).use_t2i(False))
            return

        if sub in {"下", "下一课", "next"}:
            state = await self._ensure_started(event)
            current_id = state.get("current_lesson")
            _, next_lesson = self._find_prev_next_lesson(current_id)
            if next_lesson is None:
                event.set_result(MessageEventResult().message("已到最后一课！").use_t2i(False))
                return
            state["current_lesson"] = next_lesson.id
            state["last_exercise"] = None
            state["last_answer"] = None
            await self._save_state(event, state)
            event.set_result(MessageEventResult().message(self._format_lesson(next_lesson)).use_t2i(False))
            return

        if sub in {"上", "上一课", "prev", "previous"}:
            state = await self._ensure_started(event)
            current_id = state.get("current_lesson")
            prev_lesson, _ = self._find_prev_next_lesson(current_id)
            if prev_lesson is None:
                event.set_result(MessageEventResult().message("已到第一课！").use_t2i(False))
                return
            state["current_lesson"] = prev_lesson.id
            state["last_exercise"] = None
            state["last_answer"] = None
            await self._save_state(event, state)
            event.set_result(MessageEventResult().message(self._format_lesson(prev_lesson)).use_t2i(False))
            return

        if sub in {"练习", "exercise"}:
            state = await self._ensure_started(event)
            lesson = self._find_lesson(state.get("current_lesson") or "")
            if lesson is None:
                event.set_result(MessageEventResult().message("请先选择一课：/py 课 1.1").use_t2i(False))
                return
            idx = 0
            if state.get("last_exercise"):
                idx = 1
            ex = lesson.exercises[idx % len(lesson.exercises)]
            state["last_exercise"] = ex
            state["last_answer"] = None
            await self._save_state(event, state)
            msg = "练习题：\n" + ex + "\n\n提交：/py 答案 <你的答案> 或 先上传文件再发 /py 答案 <数量>"
            event.set_result(MessageEventResult().message(msg).use_t2i(False))
            return

        if sub in {"答案", "answer"}:
            state = await self._ensure_started(event)
            if not state.get("last_exercise"):
                event.set_result(MessageEventResult().message("没有待提交的练习题。先用：/py 练习").use_t2i(False))
                return

            session_id = event.unified_msg_origin
            cached_files = self._file_cache.get(session_id, [])
            user_answer = ""
            answer_header = ""

            if cached_files:
                # 解析要使用的文件数量（默认 1）
                arg_str = arg.strip()
                n = 1
                if arg_str and arg_str.isdigit():
                    n = int(arg_str)
                n = max(1, min(n, 5))  # 限制在 1-5

                # 取最后 n 个文件，按时间排序（旧到新）
                used_files = cached_files[-n:]

                # 格式化内容，告诉 AI 这是多个文件
                parts = []
                for idx, f in enumerate(used_files):
                    parts.append(f"=== 文件 {idx+1}/{len(used_files)}: {f['file_name']} ===")
                    parts.append(f["content"])
                user_answer = "\n\n".join(parts)
                state["last_answer"] = user_answer
                await self._save_state(event, state)

                # 清理已使用的文件
                self._file_cache[session_id] = cached_files[:-n]
                if not self._file_cache[session_id]:
                    del self._file_cache[session_id]

                file_names = ", ".join([f["file_name"] for f in used_files])
                answer_header = f"已使用 {len(used_files)} 个文件作为答案：{file_names}\n\n"
            else:
                # 使用文字输入
                user_answer = arg.strip()
                if not user_answer:
                    event.set_result(MessageEventResult().message("用法：/py 答案 <你的答案>，或 /py 答案 <数量>（先上传文件）").use_t2i(False))
                    return
                state["last_answer"] = user_answer
                await self._save_state(event, state)
                answer_header = ""

            prompt = (
                "请作为 Python 教练，针对用户的练习题答案做点评。\n"
                "要求：1) 先判断是否满足题意；2) 指出问题与改进点；3) 给出一个参考答案；"
                "4) 给出 1 个延伸练习。\n\n"
                f"练习题：{state.get('last_exercise')}\n\n用户答案：{user_answer}"
            )

            try:
                messages = self._build_study_prompt(state, prompt)
                content = await self._call_openai_compatible(messages)
                if not content:
                    content = "未获得模型回复。请检查 api_base/model 配置与服务状态。"
                event.set_result(MessageEventResult().message(answer_header + content).use_t2i(False))
                # 保存对话历史（最多保留 10 轮对话，即 20 条消息）
                history = state.get("conversation_history", [])
                history.append({"role": "user", "content": prompt})
                history.append({"role": "assistant", "content": content})
                # 只保留最近 20 条消息（10 轮对话）
                if len(history) > 20:
                    history = history[-20:]
                state["conversation_history"] = history
                await self._save_state(event, state)
            except Exception as e:
                logger.exception("python_teacher answer failed")
                event.set_result(MessageEventResult().message(f"AI 调用失败：{e}").use_t2i(False))
            return

        if sub in {"测验", "quiz"}:
            state = await self._ensure_started(event)
            lesson = self._find_lesson(state.get("current_lesson") or "")
            if lesson is None:
                event.set_result(MessageEventResult().message("请先选择一课：/py 课 1.1").use_t2i(False))
                return
            questions = "\n".join([f"- {q}" for q in lesson.quiz])
            msg = f"小测（课 {lesson.id}）：\n" + questions + "\n\n你可以用 /py 问 来提问或让 AI 帮你讲解。"
            event.set_result(MessageEventResult().message(msg).use_t2i(False))
            return

        if sub in {"问", "ask"}:
            state = await self._ensure_started(event)
            arg = arg.strip()

            # 尝试解析文件数量
            session_id = event.unified_msg_origin
            cached_files = self._file_cache.get(session_id, [])
            use_files = []
            question = arg
            n = None

            # 检查 arg 是否以数字开头
            if cached_files:
                import re
                match = re.match(r'^(\d+)(\s*)(.*)$', arg)
                if match:
                    n_str, _, rest = match.groups()
                    n = int(n_str)
                    n = max(1, min(n, 5))
                    use_files = cached_files[-n:]
                    question = rest.strip()

            # 如果只指定了文件数量但没有问题，提示补充问题
            if use_files and not question and n is not None:
                file_names = ", ".join([f["file_name"] for f in use_files])
                event.set_result(MessageEventResult().message(f"已加载文件：{file_names}\n\n请补充你的问题，比如：/py 问 {n} 这几行代码有什么问题？").use_t2i(False))
                return

            if not question:
                event.set_result(MessageEventResult().message("用法：/py 问 <问题> 或 /py 问 <文件数量> <问题>").use_t2i(False))
                return

            # 构建最终问题（如果有文件则加上）
            full_question = question
            answer_header = ""
            if use_files:
                file_parts = []
                for idx, f in enumerate(use_files):
                    file_parts.append(f"=== 文件 {idx+1}/{len(use_files)}: {f['file_name']} ===")
                    file_parts.append(f["content"])
                full_question = "\n\n".join(file_parts) + "\n\n用户问题：" + question
                file_names = ", ".join([f["file_name"] for f in use_files])
                answer_header = f"已使用文件：{file_names}\n\n"
                # 清理已使用的文件
                self._file_cache[session_id] = cached_files[:-len(use_files)]
                if not self._file_cache[session_id]:
                    del self._file_cache[session_id]

            try:
                messages = self._build_study_prompt(state, full_question)
                content = await self._call_openai_compatible(messages)
                if not content:
                    content = "未获得模型回复。请检查 api_base/model 配置与服务状态。"
                event.set_result(MessageEventResult().message(answer_header + content).use_t2i(False))
                # 保存对话历史（最多保留 10 轮对话，即 20 条消息）
                history = state.get("conversation_history", [])
                history.append({"role": "user", "content": full_question})
                history.append({"role": "assistant", "content": content})
                # 只保留最近 20 条消息（10 轮对话）
                if len(history) > 20:
                    history = history[-20:]
                state["conversation_history"] = history
                await self._save_state(event, state)
            except Exception as e:
                logger.exception("python_teacher ask failed")
                event.set_result(MessageEventResult().message(f"AI 调用失败：{e}").use_t2i(False))
            return

        if sub in {"配置", "config"}:
            api_base = self._cfg("api_base", "")
            api_key = self._cfg("api_key", "")
            model = self._cfg("model", "")
            msg = "当前配置：\n" + "\n".join(
                [
                    f"- api_base: {api_base}",
                    f"- model: {model}",
                    f"- api_key: {_mask_key(str(api_key))}",
                ]
            )
            event.set_result(MessageEventResult().message(msg).use_t2i(False))
            return

        if sub in {"清空记忆", "清除记忆", "clear", "reset"}:
            state = await self._ensure_started(event)
            state["conversation_history"] = []
            await self._save_state(event, state)
            event.set_result(MessageEventResult().message("已清空 AI 对话记忆。").use_t2i(False))
            return

        event.set_result(
            MessageEventResult().message(
                "子命令不支持。可用：路线/开始/状态/模块/课/下/上/练习/答案/测验/问/配置/清空记忆\n示例：/py 路线"
            ).use_t2i(False)
        )

    async def terminate(self):
        logger.info("python_teacher terminated")
